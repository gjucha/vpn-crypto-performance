"""A small, robust Paramiko wrapper for driving a Cisco IOS interactive shell."""

from __future__ import annotations

import time
from typing import Optional

try:
    import paramiko
except ImportError as exc:  # pragma: no cover - surfaced to the user at runtime
    raise ImportError(
        "paramiko is required to connect to routers. "
        "Install it with:  pip install -r requirements.txt"
    ) from exc


class RouterSSH:
    """Manage an interactive SSH session to a Cisco router.

    Usable as a context manager so the connection is *always* closed::

        with RouterSSH(ip, user, pw, port) as router:
            print(router.send("show crypto isakmp sa"))

    This fixes two bugs in the original prototype: the connection is now
    reliably closed (the old ``ssh.close`` reference was never called), and
    reads wait for the shell to settle instead of sleeping a fixed number of
    seconds.
    """

    def __init__(self, host: str, username: str, password: str, port: int = 22,
                 connect_timeout: float = 10.0):
        self.host = host
        self.username = username
        self.password = password
        self.port = int(port)
        self.connect_timeout = connect_timeout
        self._client: Optional["paramiko.SSHClient"] = None
        self._channel = None

    # -- lifecycle ---------------------------------------------------------
    def connect(self) -> str:
        """Open the session and return the router's initial banner/prompt."""
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(
            self.host,
            username=self.username,
            password=self.password,
            port=self.port,
            timeout=self.connect_timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        self._channel = self._client.invoke_shell()
        return self._read()

    def close(self) -> None:
        """Close the channel and client if open (safe to call repeatedly)."""
        if self._channel is not None:
            try:
                self._channel.close()
            finally:
                self._channel = None
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None

    @property
    def connected(self) -> bool:
        return self._channel is not None

    # -- io ----------------------------------------------------------------
    def send(self, command: str, settle: float = 0.4, timeout: float = 15.0) -> str:
        """Send one command line and return the router's response text."""
        if self._channel is None:
            raise RuntimeError("Not connected. Call connect() first.")
        self._channel.send(command + "\n")
        return self._read(settle=settle, timeout=timeout)

    def _read(self, settle: float = 0.4, timeout: float = 15.0) -> str:
        """Read until the shell goes quiet for `settle` seconds (or timeout)."""
        assert self._channel is not None
        buffer = ""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._channel.recv_ready():
                chunk = self._channel.recv(65535).decode("ascii", errors="ignore")
                buffer += chunk
            else:
                time.sleep(settle)
                if not self._channel.recv_ready():
                    break
        return buffer

    # -- context manager ---------------------------------------------------
    def __enter__(self) -> "RouterSSH":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
