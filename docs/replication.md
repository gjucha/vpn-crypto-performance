# Replication Guide

Step-by-step instructions to rebuild the lab and reproduce the experiment from
scratch. Budget a few hours for first-time GNS3/VMware setup.

## 1. Prerequisites

| Software | Purpose |
|----------|---------|
| [GNS3](https://www.gns3.com/) + a Cisco IOS image (c7200 / IOS 12.4 or similar with IPsec) | Router emulation |
| VMware Workstation / Fusion (or GNS3's built-in VM) | Client, Server, Management hosts |
| Python 3.9+ and `pip` | Runs the configuration tool |
| [FileZilla Client](https://filezilla-project.org/) | Times the FTP transfers |
| An FTP server (e.g. Xlight, FileZilla Server) | Serves the test files |
| Kali Linux VM *(optional)* | Security testing (`macof`, `hping3`) |

> **Legal / licensing note:** Cisco IOS images are **not** distributed with this
> repository. You must supply your own image under your own Cisco licence.

## 2. Build the topology

1. Create a GNS3 project with **10 routers (R1–R10)** and the client/server/
   management hosts, cabled as described in
   [`../configs/README.md`](../configs/README.md).
2. Import each router's baseline configuration from
   [`../configs/`](../configs/) (`R1_startup-config.cfg` … `R10_startup-config.cfg`).
3. Verify the core comes up: OSPF should converge across the `10.0.0.0/24`
   `/30` links. From R1, `ping 192.168.2.1` (R10) should succeed **before** any
   VPN is applied.

## 3. Enable SSH on the edge routers (R1 and R10)

The Python tool connects over SSH, so enable it on the two tunnel endpoints:

```
configure terminal
ip domain-name lab.local
crypto key generate rsa modulus 1024
username admin privilege 15 secret <your-password>
line vty 0 4
 transport input ssh
 login local
ip ssh version 2
end
write memory
```

Make sure the management host (`192.168.10.20`) can reach R1 (`192.168.10.1`)
and R10 (`192.168.10.10`).

## 4. Install and run the configuration tool

```bash
git clone https://github.com/<your-username>/vpn-crypto-performance.git
cd vpn-crypto-performance
python -m pip install -r requirements.txt      # installs paramiko
# On Debian/Ubuntu also: sudo apt install python3-tk
python src/run_vpn_tool.py                     # or: cd src && python -m vpn_tool
```

> Prefer to review before touching a router? Click **Preview Config (dry run)**
> in the GUI to print the exact IOS command set without connecting.

In the GUI:

1. **Router Access** — enter the edge router's management IP (e.g.
   `192.168.10.1` for R1), the SSH username/password you set, and port `22`.
2. **VPN Config** — pick the **Encryption Algorithm** (AES / DES / 3DES),
   **Hash function** (MD5 / SHA256), matching **Transform-Set Options** and
   **Hash Function Options**, and confirm the peer/source/destination networks.
   Defaults already describe the R1↔R10 tunnel.
3. Click **Load VPN**. The tool pushes the full `crypto isakmp` / `crypto ipsec`
   / `crypto map` configuration and echoes each command in the **Output Box**.
4. Repeat on the **peer** router (R10), mirroring the source/destination
   networks and pointing the peer IP back at R1.

> The **Command Control** box lets you send ad-hoc IOS commands (e.g.
> `show crypto isakmp sa`) to verify the tunnel.

## 5. Verify the tunnel

On R1 or R10:

```
show crypto isakmp sa      ! should show QM_IDLE once traffic flows
show crypto ipsec sa       ! packet encaps/decaps counters should increment
```

Generate interesting traffic (an FTP download from client to server) to bring
Phase 2 up.

## 6. Run a performance scenario

1. Place the test payload on the FTP server, split per the case under test
   (1×1 GB, 10×100 MB, 100×10 MB, or 1000×1 MB — see
   [methodology.md](methodology.md)).
2. From the **client** VM, download the full set via FileZilla and record the
   transfer time reported by the client.
3. **Repeat five times** and average.
4. Reconfigure the crypto with the tool for the next scenario and repeat until
   all six encryption/hash combinations are covered.
5. *(Optional)* cross-check throughput with `iperf`/Jperf over TCP and UDP.

## 7. Security testing (optional)

From the Kali VM attached to a client- or server-side switch:

```bash
# MAC flooding
macof -i eth0

# SYN flooding
hping3 -S --flood -p 21 <server-ip>
```

Observe the effect on an in-progress FTP transfer and compare against the
baseline. **Only ever run these against your own isolated lab.**

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Tool can't SSH to the router | SSH not enabled, wrong VTY `login local`, or no RSA key — redo step 3 |
| `ModuleNotFoundError: paramiko` | `pip install -r requirements.txt` |
| `ModuleNotFoundError: _tkinter` (Linux) | `sudo apt install python3-tk` |
| Tunnel never comes up | Mismatched ISAKMP policy or transform-set between R1 and R10 — both sides must match exactly |
| No encaps in `show crypto ipsec sa` | ACL / interesting-traffic mismatch, or no traffic generated yet |
