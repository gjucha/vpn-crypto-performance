# Methodology

This document summarises the experimental approach used to evaluate how
different cryptographic algorithms and hash functions affect network
performance in a site-to-site VPN. It condenses the research paper
*"Evaluating Security and Network Performance Degradation Due to Cryptographic
Algorithms in Site-to-Site VPNs"* (Jucha & Yeboah-Ofori, ICECER 2024).

## Research question

> Which combinations of encryption algorithm and hash function provide the best
> balance between **security** and **transmission efficiency** in a site-to-site
> IPsec VPN, across different network-traffic characteristics (file size and
> file count)?

## Approach

A **qualitative, tool-driven experiment** was run entirely in a virtual lab.
Rather than reconfiguring routers by hand between every run, a purpose-built
Python application ([`src/vpn_tool/`](../src/vpn_tool)) pushes
the full IKE/IPsec crypto configuration to the edge routers over SSH, so a
scenario can be swapped in seconds and the topology stays otherwise identical.

### Simulation environment

| Component | Tool | Role |
|-----------|------|------|
| Network emulation | **GNS3** | Emulates the 10-router Cisco IOS topology |
| Virtualisation | **VMware Fusion** | Hosts the Client, Server and Management VMs |
| Router images | Cisco IOS (c7200, 12.4) | Provide real IPsec crypto engines |
| FTP server | **Xlight FTP Server** (Windows 10) | Serves the test files |
| FTP client | **FileZilla** (Windows 10) | Downloads files and is timed |
| Throughput probe | **Jperf / iperf** | Cross-check TCP vs UDP behaviour |
| Attack host | **Kali Linux** | MAC-flooding (`macof`) and SYN-flooding (`hping3`) |
| Config tool | **Python + Paramiko** (PyCharm) | Automates VPN configuration |

### Independent variables

**Encryption × Hash — six scenarios:**

| Scenario | Encryption | Hash | IPsec transform-set |
|----------|-----------|------|---------------------|
| 1 | AES  | MD5  | `esp-aes  esp-md5-hmac` |
| 2 | AES  | SHA2 | `esp-aes  esp-sha-hmac` |
| 3 | 3DES | MD5  | `esp-3des esp-md5-hmac` |
| 4 | 3DES | SHA2 | `esp-3des esp-sha-hmac` |
| 5 | DES  | MD5  | `esp-des  esp-md5-hmac` |
| 6 | DES  | SHA2 | `esp-des  esp-sha-hmac` |

**Traffic characteristic — four cases (constant ~1 GB payload, different shape):**

| Case | File count | File size | Total |
|------|-----------|-----------|-------|
| 1 | 1     | 1 GB   | 1 GB |
| 2 | 10    | 100 MB | 1 GB |
| 3 | 100   | 10 MB  | 1 GB |
| 4 | 1000  | 1 MB   | 1 GB |

> RSA was intentionally excluded: it is designed for key exchange and digital
> signatures rather than bulk data encryption, and testing it fairly would
> require a very different, computation-heavy harness.

### Dependent variable

**Average transmission time** for a full transfer, measured by the FTP client.

### Controls for reliability

- Every measurement is **repeated five times** and averaged.
- All VMs use **identical hardware/software specs**.
- The topology is isolated to minimise external congestion.
- Both TCP and UDP behaviour is cross-checked with Jperf.
- Because absolute times depend on host performance, conclusions are drawn from
  **normalised percentage differences** between scenarios, not raw values.

## Fixed IKE / IPsec parameters

| Parameter | Value |
|-----------|-------|
| IKE authentication | pre-shared key |
| Diffie–Hellman group | 2 |
| ISAKMP SA lifetime | 86400 s |
| Tunnel endpoints | R1 (client site) ↔ R10 (server site) |
| Protected traffic | `192.168.1.0/24` ↔ `192.168.2.0/24` |

## Security testing

Alongside performance, the resilience of the tunnel was probed with two
Layer-2 / transport denial-of-service attacks launched from Kali Linux against
the client-side and server-side switches:

- **MAC flooding** (`macof`) — overflows the switch CAM table.
- **SYN flooding** (`hping3`) — exhausts server connection state.

Impact was measured with the same metrics (transmission time, packet loss,
jitter). See [results.md](results.md) for findings.
