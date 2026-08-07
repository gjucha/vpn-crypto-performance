#!/usr/bin/env python3
"""Convenience launcher so the GUI runs with a single command:

    python src/run_vpn_tool.py

(equivalent to ``python -m vpn_tool`` when run from inside ``src/``).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vpn_tool.app import VpnConfigApp  # noqa: E402


if __name__ == "__main__":
    VpnConfigApp().mainloop()
