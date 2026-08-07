"""Data model for a site-to-site VPN configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

# Human-facing menu choice  ->  Cisco IOS token used in `crypto isakmp policy`.
ENCRYPTION_ALGORITHMS = {"AES": "aes", "DES": "des", "3DES": "3des"}
HASH_FUNCTIONS = {"MD5": "md5", "SHA256": "sha256"}

# IPsec transform-set building blocks (already valid IOS tokens).
TRANSFORM_SET_OPTIONS = ["esp-aes", "esp-3des", "esp-des"]
HMAC_OPTIONS = ["ah-md5-hmac", "ah-sha-hmac", "esp-md5-hmac", "esp-sha-hmac"]


@dataclass
class VpnParameters:
    """All settings required to build one end of a site-to-site IPsec tunnel.

    Field defaults describe the R1 (client-site) end of the reference topology
    used in the study; see ``configs/README.md`` for the full addressing plan.
    """

    # --- Router access (never logged in cleartext) ---
    router_ip: str = "192.168.10.1"
    login: str = "admin"
    password: str = field(default="", repr=False)
    ssh_port: int = 22

    # --- IKE Phase 1 (ISAKMP) ---
    isakmp_policy: str = "1"
    encryption: str = "AES"          # key of ENCRYPTION_ALGORITHMS
    hash_function: str = "MD5"       # key of HASH_FUNCTIONS
    authentication: str = "pre-share"
    dh_group: str = "2"
    lifetime: str = "86400"
    crypto_key: str = field(default="Password", repr=False)

    # --- Peer / interesting traffic ---
    peer_ip: str = "10.0.0.54"
    acl_name: str = "VpnAcl"
    src_network: str = "192.168.1.0"
    src_wildcard: str = "0.0.0.255"
    dst_network: str = "192.168.2.0"
    dst_wildcard: str = "0.0.0.255"

    # --- IKE Phase 2 (IPsec) ---
    transform_set_name: str = "TS"
    transform_set_option: str = "esp-aes"
    hmac_option: str = "esp-sha-hmac"
    crypto_map_name: str = "cmap"
    crypto_map_number: str = "1"
    interface_id: str = "f2/0"

    def encryption_token(self) -> str:
        """IOS token for the chosen encryption algorithm."""
        return ENCRYPTION_ALGORITHMS.get(self.encryption, self.encryption.lower())

    def hash_token(self) -> str:
        """IOS token for the chosen IKE hash function."""
        return HASH_FUNCTIONS.get(self.hash_function, self.hash_function.lower())

    def validate(self) -> list[str]:
        """Return a list of human-readable problems; empty means valid."""
        problems: list[str] = []
        required = {
            "router IP": self.router_ip,
            "login": self.login,
            "ISAKMP policy number": self.isakmp_policy,
            "DH group": self.dh_group,
            "peer IP": self.peer_ip,
            "ACL name": self.acl_name,
            "interface ID": self.interface_id,
        }
        for label, value in required.items():
            if not str(value).strip():
                problems.append(f"Missing value: {label}.")
        try:
            port = int(self.ssh_port)
            if not (0 < port < 65536):
                problems.append("SSH port must be between 1 and 65535.")
        except (TypeError, ValueError):
            problems.append("SSH port must be a number.")
        return problems
