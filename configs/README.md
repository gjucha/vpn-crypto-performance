# Router Startup Configurations

This folder contains the **Cisco IOS startup configurations** for the ten
routers (R1–R10) that make up the test topology, exported from GNS3.

These are the **baseline** configurations: interface addressing and OSPF
routing only. They deliberately **do not** contain the IPsec/VPN crypto
configuration — that part is pushed at test time by
the [`vpn_tool`](../src/vpn_tool) application so that the encryption
algorithm and hash function can be swapped between scenarios. Load these first
to bring the network up, then apply a VPN scenario with the tool.

## Topology role

The transit core is a mesh of `10.0.0.0/24` point-to-point `/30` links running
**OSPF area 0**. The two VPN endpoints are the edge routers:

- **R1** — client site, LAN `192.168.1.0/24` (Client `192.168.1.2`)
- **R10** — server site, LAN `192.168.2.0/24` (Server `192.168.2.2`)

The site-to-site tunnel is built between R1 and R10; the eight routers in
between (R2–R9) only route encrypted transit traffic. A management LAN
`192.168.10.0/24` (App host `192.168.10.20`) reaches R1/R10 for SSH so the
Python tool can drive the configuration.

## Interface addressing plan

| Device | Interface | Address        | Mask | Link / Purpose |
|--------|-----------|----------------|------|----------------|
| R1  | f0/0 | 192.168.1.1  | /24 | To Client LAN |
| R1  | f1/0 | 10.0.0.1     | /30 | to R2 |
| R1  | f2/0 | 10.0.0.5     | /30 | to R3 |
| R1  | f3/0 | 10.0.0.9     | /30 | to R4 |
| R1  | f0/1 | 192.168.10.1 | /24 | Management switch |
| R2  | f1/0 | 10.0.0.2     | /30 | to R1 |
| R2  | f0/1 | 10.0.0.13    | /30 | to R5 |
| R2  | f0/0 | 10.0.0.61    | /30 | to R7 |
| R3  | f2/0 | 10.0.0.6     | /30 | to R1 |
| R3  | f1/0 | 10.0.0.17    | /30 | to R5 |
| R3  | f3/0 | 10.0.0.21    | /30 | to R6 |
| R4  | f3/0 | 10.0.0.10    | /30 | to R1 |
| R4  | f1/0 | 10.0.0.25    | /30 | to R6 |
| R4  | f0/0 | 10.0.0.65    | /30 | to R9 |
| R5  | f0/1 | 10.0.0.14    | /30 | to R2 |
| R5  | f1/0 | 10.0.0.18    | /30 | to R3 |
| R5  | f0/0 | 10.0.0.29    | /30 | to R6 |
| R5  | f2/0 | 10.0.0.33    | /30 | to R7 |
| R5  | f3/0 | 10.0.0.37    | /30 | to R8 |
| R6  | f3/0 | 10.0.0.22    | /30 | to R3 |
| R6  | f1/0 | 10.0.0.26    | /30 | to R4 |
| R6  | f0/0 | 10.0.0.30    | /30 | to R5 |
| R6  | f2/0 | 10.0.0.41    | /30 | to R8 |
| R6  | f0/1 | 10.0.0.45    | /30 | to R9 |
| R7  | f0/0 | 10.0.0.62    | /30 | to R2 |
| R7  | f2/0 | 10.0.0.34    | /30 | to R5 |
| R7  | f1/0 | 10.0.0.49    | /30 | to R10 |
| R8  | f3/0 | 10.0.0.38    | /30 | to R5 |
| R8  | f0/1 | 10.0.0.42    | /30 | to R6 |
| R8  | f2/0 | 10.0.0.53    | /30 | to R10 |
| R9  | f0/0 | 10.0.0.66    | /30 | to R4 |
| R9  | f0/1 | 10.0.0.46    | /30 | to R6 |
| R9  | f3/0 | 10.0.0.57    | /30 | to R10 |
| R10 | f0/0 | 192.168.2.1  | /24 | To Server LAN |
| R10 | f1/0 | 10.0.0.50    | /30 | to R7 |
| R10 | f2/0 | 10.0.0.54    | /30 | to R8 |
| R10 | f3/0 | 10.0.0.58    | /30 | to R9 |
| R10 | f0/1 | 192.168.10.10| /24 | Management switch |

## End hosts (virtual machines)

| Host   | Address        | Mask | Gateway       | Role |
|--------|----------------|------|---------------|------|
| Client | 192.168.1.2    | /24  | 192.168.1.1   | FileZilla FTP client |
| Server | 192.168.2.2    | /24  | 192.168.2.1   | Xlight FTP server |
| App    | 192.168.10.20  | /24  | 192.168.10.1  | Management host running the Python tool |

## Loading a configuration in GNS3

Each router in GNS3 can import a startup-config, or you can paste the file
into the console after boot. On a live console:

```
enable
configure terminal
! paste the contents of Rn_startup-config.cfg
end
write memory
```

> **Note:** These configs enable SSH-based management (`line vty` login). Set a
> username/password and `crypto key generate rsa` on the edge routers (R1/R10)
> before the Python tool can connect — see [`../docs/replication.md`](../docs/replication.md).
