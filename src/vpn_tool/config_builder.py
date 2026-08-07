"""Pure translation of :class:`VpnParameters` into ordered Cisco IOS commands.

This module has **no side effects** and no dependency on Tkinter or Paramiko.
That keeps it easy to unit-test and lets the GUI offer a "Preview" (dry-run)
mode that shows exactly what would be sent to the router without connecting.
"""

from __future__ import annotations

import re

from .models import VpnParameters

_PSK_RE = re.compile(r"(crypto isakmp key\s+)(\S+)(\s+address)")


def mask_secrets(command: str) -> str:
    """Hide the pre-shared key when a command is shown on screen or in a log."""
    return _PSK_RE.sub(r"\1******\3", command)


def build_ios_commands(p: VpnParameters) -> list[str]:
    """Return the ordered list of IOS commands that configure the tunnel.

    The sequence mirrors a standard Cisco IKEv1/IPsec site-to-site setup:
    ISAKMP (Phase 1) policy, pre-shared key, interesting-traffic ACL, IPsec
    transform-set and crypto map (Phase 2), then binding the map to the
    outbound interface.
    """
    return [
        "configure terminal",
        # --- IKE Phase 1: ISAKMP policy ---
        f"crypto isakmp policy {p.isakmp_policy}",
        f"encryption {p.encryption_token()}",
        f"hash {p.hash_token()}",
        f"authentication {p.authentication}",
        f"group {p.dh_group}",
        f"lifetime {p.lifetime}",
        "exit",
        # --- Pre-shared key for the peer ---
        f"crypto isakmp key {p.crypto_key} address {p.peer_ip}",
        # --- Interesting-traffic ACL ---
        f"ip access-list extended {p.acl_name}",
        f"permit ip {p.src_network} {p.src_wildcard} {p.dst_network} {p.dst_wildcard}",
        "exit",
        # --- IKE Phase 2: IPsec transform-set + crypto map ---
        f"crypto ipsec transform-set {p.transform_set_name} "
        f"{p.transform_set_option} {p.hmac_option}",
        f"crypto map {p.crypto_map_name} {p.crypto_map_number} ipsec-isakmp",
        f"set peer {p.peer_ip}",
        f"set transform-set {p.transform_set_name}",
        f"match address {p.acl_name}",
        "exit",
        # --- Apply the crypto map to the outbound interface ---
        f"interface {p.interface_id}",
        f"crypto map {p.crypto_map_name}",
        "exit",
        "end",
    ]


def preview_text(p: VpnParameters) -> str:
    """Render the command list as a copy-pasteable IOS script for dry-run mode."""
    header = (
        "! ----- DRY RUN: commands that WOULD be sent -----\n"
        f"! target router : {p.router_ip} (port {p.ssh_port})\n"
        f"! encryption/hash: {p.encryption} + {p.hash_function}\n"
        f"! transform-set  : {p.transform_set_option} {p.hmac_option}\n"
        f"! protected      : {p.src_network} {p.src_wildcard} "
        f"<-> {p.dst_network} {p.dst_wildcard}\n"
        "! (pre-shared key masked)\n"
        "! ------------------------------------------------\n"
    )
    return header + "\n".join(mask_secrets(c) for c in build_ios_commands(p))
