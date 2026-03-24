# Network Test Framework — Project Context

## What This Project Is

A Python-based network test automation framework that targets an ASUS RT-AC66U router as the device under test (DUT). The goal is to demonstrate functional, integration, regression, and performance testing of networking protocols and hardware — directly aligned with Network QA / Test Engineer roles in the industry.

All test orchestration runs on a local machine. The router is purely a target device — it does not run any custom code.

---

## Target Role Alignment

This project was scoped to match the requirements of a Network QA/Test Engineer position. Key JD requirements it addresses:

- Python/Bash scripting for test automation
- Functional, integration, regression, and performance testing
- Linux networking and command-line tools
- Familiarity with tcpdump, iperf3, wireshark
- CI/CD pipeline integration
- Debugging and reporting software/network defects

---

## Hardware

**Device:** ASUS RT-AC66U (original, non-B1)
**Firmware:** ASUSWRT 3.0.0.4 (built May 7, 2016)
**Kernel:** Linux 2.6.22.19
**CPU:** Broadcom BCM4706KPBG MIPS74K @ 600MHz (single core)
**RAM:** 256MB DDR2
**Flash:** 128MB

### Interface Layout (from `ip addr`)
| Interface | Role |
|---|---|
| `br0` | LAN bridge — `192.168.1.1/24` |
| `vlan1@eth0` | LAN side |
| `vlan2@eth0` | WAN side (not currently configured) |
| `eth1` | 2.4GHz wireless radio |
| `eth2` | 5GHz wireless radio |

---

## Access Method

**Telnet** (SSH is not available on this firmware version)

```bash
telnet 192.168.1.1
# login: admin
# password: <your password>
```

SSH option does not appear in the Administration > System panel on this firmware. Telnet was enabled via the web UI at `http://192.168.1.1` under Administration > System.

Web admin panel is accessible at `http://192.168.1.1`.

### Available on the router
- `iptables` — fully accessible, read and write
- `ip addr`, `ip route` — available
- `nvram` — available for reading router config values
- `tcpdump` — **NOT available** (not in PATH, not installed)

---

## Current Status

**Nothing has been built yet.** This file documents the environment investigation and project plan established before writing any code.

The physical setup is:
- Laptop connected to one of LAN ports 1–4 via ethernet
- Router factory reset, web UI accessible, telnet enabled
- WAN port not currently connected (internet connection not yet configured)

---

## Planned Architecture

```
Local Machine (test orchestration)
│
├── pytest test suite
├── RouterClient (telnetlib) ──────────────→ RT-AC66U (192.168.1.1)
├── iperf3 client ─────────────────────────→ second device on LAN
└── scapy (packet capture on local iface)
```

### Why telnetlib instead of Paramiko
SSH is unavailable on this firmware. `telnetlib` (Python stdlib) is used as the transport layer instead. The `RouterClient` wrapper abstracts this so tests don't care about the transport.

---

## Planned Project Structure

```
network-test-suite/
├── lib/
│   ├── router_client.py        # telnetlib wrapper — connect, run commands, disconnect
│   └── reporter.py             # JUnit XML / HTML report generation
├── tests/
│   ├── test_connectivity.py    # ping, interface state, basic reachability
│   ├── test_dhcp.py            # lease assignment, renewal, expiry
│   ├── test_firewall.py        # iptables rule add/verify/remove
│   ├── test_throughput.py      # iperf3 client/server performance tests
│   └── test_traffic.py         # scapy packet capture and assertion
├── scripts/
│   └── capture.sh              # bash wrapper around local tcpdump/scapy
├── ci/
│   └── .github/workflows/ci.yml  # GitHub Actions pipeline
├── CLAUDE.md                   # this file
└── README.md                   # project framing for resume/interviews
```

---

## Planned Build Order

### Week 1 — Framework shell
- `RouterClient` class using `telnetlib`
- First passing test: connect → run `iptables -L` → assert `Chain INPUT` present
- pytest config, basic project structure

### Week 2 — DHCP and interface tests
- Assert `br0` is UP with correct IP via `ip addr`
- Connect a second device, assert it receives a `192.168.1.x` DHCP lease
- Query `nvram` for WAN config values

### Week 3 — Firewall manipulation tests
- Add an iptables rule over telnet
- Assert it appears in `iptables -L`
- Remove it and assert it's gone
- Most directly relevant to the target role

### Week 4 — Traffic capture with Scapy
- Run `scapy` on local ethernet interface
- Generate traffic, capture packets, assert on IP src/dst
- Programmatic pcap analysis

### Week 5 — CI/CD + cleanup
- GitHub Actions workflow that runs the test suite
- HTML/JUnit XML test report output
- README framed as a professional network validation framework

---

## Known Constraints and Workarounds

| Constraint | Workaround |
|---|---|
| No `tcpdump` on router | Capture on local machine interface using `scapy` |
| Telnet instead of SSH | `telnetlib` wrapper — tests are transport-agnostic |
| No WAN connection yet | All Week 1–3 tests are LAN-only and unaffected |
| Single-core 600MHz CPU | Router is DUT only — no code runs on it |
| Old kernel (2.6.22) | `iptables` and networking primitives still fully functional |

---

## WAN Status

WAN port is physically unconnected. When ready to configure:

```bash
# Check current WAN config via telnet
nvram get wan_proto
nvram get wan_ipaddr
```

Then configure the connection type in the web UI under WAN > Internet Connection.

WAN connectivity unlocks DNS resolution tests, port forwarding validation, and internet-path performance tests.
