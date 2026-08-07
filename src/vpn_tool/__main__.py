"""Entry point:  python -m vpn_tool"""

from .app import VpnConfigApp


def main() -> None:
    VpnConfigApp().mainloop()


if __name__ == "__main__":
    main()
