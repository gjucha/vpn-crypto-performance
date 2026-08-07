"""
vpn_tool
========

Site-to-Site IPsec VPN configuration tool for Cisco IOS routers.

Developed for the final-year research project *"Evaluating Security and Network
Performance Degradation Due to Cryptographic Algorithms in Site-to-Site VPNs"*
(University of West London / ICECER 2024).

Package layout:
    models          - VpnParameters dataclass describing a tunnel configuration
    config_builder  - pure function turning parameters into ordered IOS commands
    ssh_client      - RouterSSH, a small Paramiko wrapper (context manager)
    app             - VpnConfigApp, the Tkinter GUI
    __main__        - entry point (``python -m vpn_tool``)
"""

from .models import VpnParameters
from .config_builder import build_ios_commands

__version__ = "2.0.0"
__author__ = "Grzegorz Tomasz Jucha"
__all__ = ["VpnParameters", "build_ios_commands", "__version__"]
