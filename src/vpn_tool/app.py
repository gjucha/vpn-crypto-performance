"""Tkinter GUI for configuring a site-to-site IPsec VPN on a Cisco router.

The GUI does no blocking network I/O on the main thread: every SSH action runs
in a background worker and streams output back through a thread-safe queue, so
the window stays responsive. A **Preview** button renders the exact IOS command
set without connecting (dry-run).
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk

from .models import (
    VpnParameters,
    ENCRYPTION_ALGORITHMS,
    HASH_FUNCTIONS,
    TRANSFORM_SET_OPTIONS,
    HMAC_OPTIONS,
)
from .config_builder import build_ios_commands, preview_text, mask_secrets


class VpnConfigApp(tk.Tk):
    PAD = 5
    ENTRY_W = 22

    def __init__(self) -> None:
        super().__init__()
        self.title("VPN Config Tool UWL 2024 vGJ2.1")

        self._log_queue: "queue.Queue[object]" = queue.Queue()
        self._router = None            # persistent manual session (optional)
        self._action_buttons: list[tk.Button] = []
        self._vars: dict[str, tk.Variable] = {}

        self._build_ui()
        self.after(100, self._drain_log_queue)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        root = tk.Frame(self)
        root.pack(fill="both", expand=True)

        left = tk.Frame(root)
        left.grid(row=0, column=0, sticky="n")
        self._build_access_frame(left)
        self._build_vpn_frame(left)
        self._build_command_frame(left)
        self._build_output_frame(root)

    def _add_entry(self, parent, row, label, key, default="", show=None):
        tk.Label(parent, text=label).grid(
            row=row, column=0, padx=self.PAD, pady=self.PAD, sticky="e")
        var = tk.StringVar(value=default)
        tk.Entry(parent, width=self.ENTRY_W, textvariable=var, show=show).grid(
            row=row, column=1, padx=self.PAD, pady=self.PAD, sticky="w")
        self._vars[key] = var
        return var

    def _add_option(self, parent, row, label, key, choices, default):
        tk.Label(parent, text=label).grid(
            row=row, column=0, padx=self.PAD, pady=self.PAD, sticky="e")
        var = tk.StringVar(value=default)
        tk.OptionMenu(parent, var, *choices).grid(
            row=row, column=1, padx=self.PAD, pady=self.PAD, sticky="w")
        self._vars[key] = var
        return var

    def _build_access_frame(self, parent):
        f = tk.LabelFrame(parent, text="Router Access Settings")
        f.grid(row=0, column=0, sticky="nsew", padx=self.PAD, pady=self.PAD)
        self._add_entry(f, 0, "Router IP Address:", "router_ip", "192.168.10.1")
        self._add_entry(f, 1, "Login:", "login", "admin")
        self._add_entry(f, 2, "Password:", "password", "", show="*")
        self._add_entry(f, 3, "SSH Port:", "ssh_port", "22")

        btns = tk.Frame(f)
        btns.grid(row=4, column=0, columnspan=2, pady=self.PAD)
        self._mk_button(btns, "Connect", self.on_connect).pack(side="left", padx=2)
        self._mk_button(btns, "Close Connection", self.on_close).pack(side="left", padx=2)

    def _build_vpn_frame(self, parent):
        container = tk.LabelFrame(parent, text="VPN Config")
        container.grid(row=1, column=0, sticky="nsew", padx=self.PAD, pady=self.PAD)
        f = tk.Frame(container)
        f.pack(fill="both", expand=True)

        self._add_entry(f, 0, "Crypto Isakmp Policy Number", "isakmp_policy", "1")
        self._add_option(f, 1, "Encryption Algorithm", "encryption",
                         list(ENCRYPTION_ALGORITHMS), "AES")
        self._add_option(f, 2, "Hash function", "hash_function",
                         list(HASH_FUNCTIONS), "MD5")
        self._add_entry(f, 3, "Authentication", "authentication", "pre-share")
        self._add_entry(f, 4, "DH Group Number", "dh_group", "2")
        self._add_entry(f, 5, "Lifetime", "lifetime", "86400")
        self._add_entry(f, 6, "Crypto Key", "crypto_key", "Password", show="*")
        self._add_entry(f, 7, "Peer IP Address:", "peer_ip", "10.0.0.54")
        self._add_entry(f, 8, "Access List Name:", "acl_name", "VpnAcl")
        self._add_entry(f, 9, "VPN Source Network:", "src_network", "192.168.1.0")
        self._add_entry(f, 10, "VPN Source Wildcard Mask:", "src_wildcard", "0.0.0.255")
        self._add_entry(f, 11, "VPN Destination Network:", "dst_network", "192.168.2.0")
        self._add_entry(f, 12, "VPN Destination Wildcard Mask:", "dst_wildcard", "0.0.0.255")
        self._add_entry(f, 13, "IPSec Transform-Set Name", "transform_set_name", "TS")
        self._add_option(f, 14, "Transform-Set Option", "transform_set_option",
                         TRANSFORM_SET_OPTIONS, "esp-aes")
        self._add_option(f, 15, "HMAC / Hash Option", "hmac_option",
                         HMAC_OPTIONS, "esp-sha-hmac")
        self._add_entry(f, 16, "Crypto Map Name", "crypto_map_name", "cmap")
        self._add_entry(f, 17, "Crypto Map Number", "crypto_map_number", "1")
        self._add_entry(f, 18, "Interface ID", "interface_id", "f2/0")

        btns = tk.Frame(f)
        btns.grid(row=19, column=0, columnspan=2, pady=12)
        self._mk_button(btns, "Preview Config (dry run)", self.on_preview).pack(side="left", padx=3)
        self._mk_button(btns, "Load VPN", self.on_load_vpn).pack(side="left", padx=3)

    def _build_command_frame(self, parent):
        f = tk.LabelFrame(parent, text="Command Control")
        f.grid(row=2, column=0, sticky="nsew", padx=self.PAD, pady=self.PAD)
        tk.Label(f, text="Command:").grid(row=0, column=0, padx=self.PAD, pady=self.PAD, sticky="w")
        self._vars["command"] = tk.StringVar()
        tk.Entry(f, width=self.ENTRY_W * 2, textvariable=self._vars["command"]).grid(
            row=0, column=1, padx=self.PAD, pady=self.PAD, sticky="w")
        self._mk_button(f, "Execute Command", self.on_execute).grid(
            row=1, column=0, columnspan=2, padx=self.PAD, pady=self.PAD, sticky="w")

    def _build_output_frame(self, parent):
        f = tk.LabelFrame(parent, text="Output Box")
        f.grid(row=0, column=1, sticky="nsew", padx=self.PAD, pady=self.PAD)
        self.output = tk.Text(f, height=34, width=52, state="disabled", wrap="word")
        self.output.grid(row=0, column=0, sticky="nsew")
        sb = tk.Scrollbar(f, command=self.output.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.output.config(yscrollcommand=sb.set)

    def _mk_button(self, parent, text, command) -> tk.Button:
        b = tk.Button(parent, text=text, command=command)
        self._action_buttons.append(b)
        return b

    # -------------------------------------------------------------- helpers
    def _params(self) -> VpnParameters:
        v = self._vars
        return VpnParameters(
            router_ip=v["router_ip"].get(), login=v["login"].get(),
            password=v["password"].get(), ssh_port=v["ssh_port"].get(),
            isakmp_policy=v["isakmp_policy"].get(), encryption=v["encryption"].get(),
            hash_function=v["hash_function"].get(), authentication=v["authentication"].get(),
            dh_group=v["dh_group"].get(), lifetime=v["lifetime"].get(),
            crypto_key=v["crypto_key"].get(), peer_ip=v["peer_ip"].get(),
            acl_name=v["acl_name"].get(), src_network=v["src_network"].get(),
            src_wildcard=v["src_wildcard"].get(), dst_network=v["dst_network"].get(),
            dst_wildcard=v["dst_wildcard"].get(),
            transform_set_name=v["transform_set_name"].get(),
            transform_set_option=v["transform_set_option"].get(),
            hmac_option=v["hmac_option"].get(),
            crypto_map_name=v["crypto_map_name"].get(),
            crypto_map_number=v["crypto_map_number"].get(),
            interface_id=v["interface_id"].get(),
        )

    def _log(self, text: str) -> None:
        """Thread-safe: queue a line for the output box."""
        self._log_queue.put(text)

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for b in self._action_buttons:
            b.config(state=state)

    def _run_worker(self, fn) -> None:
        """Disable buttons, run fn() in a daemon thread, re-enable when done."""
        self._set_busy(True)

        def wrapped():
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 - surfaced to the user
                self._log(f"[ERROR] {exc}")
            finally:
                self._log_queue.put(("__busy__", False))

        threading.Thread(target=wrapped, daemon=True).start()

    def _drain_log_queue(self) -> None:
        try:
            while True:
                item = self._log_queue.get_nowait()
                if isinstance(item, tuple) and item and item[0] == "__busy__":
                    self._set_busy(bool(item[1]))
                else:
                    self._append(str(item))
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _append(self, text: str) -> None:
        self.output.config(state="normal")
        self.output.insert(tk.END, text.rstrip("\n") + "\n")
        self.output.config(state="disabled")
        self.output.see(tk.END)

    # ------------------------------------------------------------- actions
    def on_preview(self) -> None:
        """Dry run: show the IOS commands without connecting to anything."""
        self._append(mask_secrets(preview_text(self._params())))

    def on_connect(self) -> None:
        p = self._params()
        problems = p.validate()
        if problems:
            self._log("Cannot connect:\n  " + "\n  ".join(problems))
            return

        def work():
            from .ssh_client import RouterSSH
            self._log(f"Connecting to {p.router_ip}:{p.ssh_port} ...")
            router = RouterSSH(p.router_ip, p.login, p.password, p.ssh_port)
            banner = router.connect()
            self._router = router
            self._log(banner or "(connected)")
            self._log("Session open. Use Command Control to run commands.")

        self._run_worker(work)

    def on_execute(self) -> None:
        command = self._vars["command"].get().strip()
        if not command:
            self._log("Enter a command first.")
            return
        if self._router is None or not self._router.connected:
            self._log("Not connected. Click Connect first.")
            return

        def work():
            self._log(f"> {command}")
            self._log(self._router.send(command))

        self._run_worker(work)

    def on_close(self) -> None:
        if self._router is not None:
            self._router.close()
            self._router = None
            self._log("Connection closed.")
        else:
            self._log("No active connection.")

    def on_load_vpn(self) -> None:
        p = self._params()
        problems = p.validate()
        if problems:
            self._log("Cannot load VPN:\n  " + "\n  ".join(problems))
            return
        commands = build_ios_commands(p)

        def work():
            from .ssh_client import RouterSSH
            self._log(f"--- Loading VPN configuration onto {p.router_ip} ---")
            self._log(f"    {p.encryption} + {p.hash_function} / "
                      f"{p.transform_set_option} {p.hmac_option}")
            with RouterSSH(p.router_ip, p.login, p.password, p.ssh_port) as router:
                for cmd in commands:
                    self._log(f"> {mask_secrets(cmd)}")
                    output = router.send(cmd)
                    if output.strip():
                        self._log(output)
            self._log("--- VPN configuration sent. Verify with "
                      "'show crypto isakmp sa'. ---")

        self._run_worker(work)
