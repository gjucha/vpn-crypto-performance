# Results & Discussion

Findings from the six encryption/hash scenarios and the two attack techniques.
Figures are the aggregate averages reported in the research paper (each value
is the mean of five repeated transfers). Because absolute timings depend on the
performance of the virtual host, the **relative differences** between scenarios
are the meaningful output.

## 1. Encryption × hash performance

| Scenario | Encryption + Hash | Relative outcome |
|----------|-------------------|------------------|
| 5 | **DES + MD5**  | **Fastest** overall — but insecure (DES broken, MD5 deprecated) |
| 2 | **AES + SHA2** | Only ~4 % slower than the fastest — strong security, low overhead |
| 4 | **3DES + SHA2**| Balanced — the recommended production baseline |
| 1 | **AES + MD5**  | **Slowest** overall |

Key numbers reported in the paper:

- **Fastest:** Scenario 5 (DES + MD5) ≈ **10,010** (compromised — not usable in practice).
- **Slowest:** Scenario 1 (AES + MD5) ≈ **12,460**.
- **Strong & fast:** Scenario 2 (AES + SHA2) ≈ **10,419** — only **~4 %** slower than the fastest.
- **Spread between best and worst configuration ≈ 22 %.**

**Takeaway:** the performance penalty for choosing a *secure* configuration over
the fastest *insecure* one is small. Moving from broken DES+MD5 to robust
AES+SHA2 costs only a few percent, so there is little performance justification
for weak cryptography.

## 2. Effect of traffic shape (file size vs. count)

Holding the total payload at ~1 GB but changing how it is split:

| Case | Shape | Relative outcome |
|------|-------|------------------|
| 2 | 10 × 100 MB  | **Shortest** transmission time (≈ 9,692) |
| 3 | 100 × 10 MB  | **Longest** transmission time (≈ 11,805), ~22 % longer |

**Takeaway:** many small transfers are markedly slower than a few large ones
because each file incurs connection setup/teardown overhead. End-node (client/
server) behaviour influences total transfer time **more than** the choice of VPN
crypto — an important scoping insight for anyone benchmarking VPNs.

## 3. Transport protocol: UDP vs TCP (Jperf)

- **UDP** ([`images/jperf-udp.png`](images/jperf-udp.png)) — higher, steadier
  throughput with fewer fluctuations.
- **TCP** ([`images/jperf-tcp.png`](images/jperf-tcp.png)) — pronounced peaks and
  drops caused by flow control and delivery guarantees.

## 4. Security testing

| Attack | Tool | Effect on the VPN |
|--------|------|-------------------|
| MAC flooding | `macof` | Caused distortion but **did not stop** transfers. Client-side attacks and **source-address spoofing** were the most disruptive. |
| SYN flooding | `hping3` | **Complete stoppage** of client transfers — highly effective, underlining the need for physical/switch-level protection. |

Even a correctly configured, strongly encrypted tunnel remains vulnerable to
Layer-2 / transport DoS at the switches. Encryption protects confidentiality
and integrity of the payload, not availability of the underlying network.

## Recommendation

> **Use 3DES + SHA2 as the balanced baseline** for security and end-user comfort.
> AES + SHA2 is an equally strong, marginally faster alternative. Avoid DES and
> MD5 despite their speed — both are compromised. Pair the crypto choice with
> switch hardening (port security, storm control) to mitigate the DoS attacks
> that encryption alone cannot stop.

Future work: additional algorithms and security protocols, including
post-quantum / quantum-cryptography comparisons.

---

*Raw per-run measurements for every scenario and case live in the project's
`Adresacja IP(CORRECTED).xlsx` workbook (sheets "Scenario 1–3"). They are not
committed here to keep the repository lean; see the paper for the full tables.*
