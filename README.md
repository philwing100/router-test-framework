# Router Test Framework

A Python-based network test automation framework targeting the ASUS RT-AC66U as the device under test (DUT). Demonstrates functional, integration, regression, and performance testing of networking protocols and hardware — aligned with Network QA / Test Engineer role requirements.

---

## Hardware Setup

| Component | Details |
|---|---|
| Router (DUT) | ASUS RT-AC66U, ASUSWRT 3.0.0.4 |
| Transport | Telnet (SSH unavailable on this firmware) |
| Router IP | `192.168.1.1` |
| Access | Laptop connected to LAN port via ethernet |

Telnet must be enabled via **Administration > System** in the router web UI at `http://192.168.1.1`.

---

## Project Structure

```
.
├── lib/
│   ├── router_client.py    # telnetlib wrapper — connect, run, disconnect
│   └── reporter.py         # JUnit XML report generation
├── tests/
│   ├── test_connectivity.py  # interface state, ping, iptables chain presence
│   ├── test_dhcp.py          # DHCP nvram config, lease file assertions
│   ├── test_firewall.py      # iptables rule add/verify/remove lifecycle
│   ├── test_throughput.py    # iperf3 TCP/UDP performance tests
│   └── test_traffic.py       # Scapy packet capture and field assertions
├── scripts/
│   └── capture.sh          # local tcpdump/scapy capture wrapper
├── .github/workflows/
│   └── ci.yml              # GitHub Actions pipeline
├── conftest.py             # shared pytest fixtures (router session)
├── pytest.ini              # markers and test config
└── requirements.txt
```

---

## Quick Start

```bash
pip install -r requirements.txt

# Run connectivity tests against the router
pytest tests/test_connectivity.py \
  --router-password=<your_password> -v

# Run firewall tests
pytest tests/test_firewall.py \
  --router-password=<your_password> -v

# Run all tests (skip hardware-dependent ones in CI)
pytest -m "not throughput and not traffic and not second_device" -v
```

---

## Test Markers

| Marker | Description |
|---|---|
| `dhcp` | DHCP configuration and lease tests |
| `firewall` | iptables rule lifecycle tests |
| `throughput` | iperf3 performance tests (needs `--iperf-server`) |
| `traffic` | Scapy capture tests (needs root / `cap_net_raw`) |
| `second_device` | Tests requiring a second physical LAN device |

---

## CLI Options

| Option | Default | Description |
|---|---|---|
| `--router-host` | `192.168.1.1` | Router IP |
| `--router-user` | `admin` | Telnet username |
| `--router-password` | `admin` | Telnet password |
| `--iperf-server` | `192.168.1.100` | iperf3 server IP on LAN |

---

## Packet Capture

```bash
# Capture on local interface (requires tcpdump or scapy)
LOCAL_IFACE=eth0 ./scripts/capture.sh

# Run Scapy tests (requires root or cap_net_raw)
sudo pytest tests/test_traffic.py --router-password=<pw> -v
```

---

## CI/CD

The GitHub Actions workflow in [.github/workflows/ci.yml](.github/workflows/ci.yml) runs lint and offline tests on every push. Hardware-in-the-loop tests run on a self-hosted runner when `ROUTER_AVAILABLE=true` is set as a repository variable.

---

## Tools Used

- `pytest` — test orchestration
- `telnetlib` — router transport (stdlib)
- `iperf3` — throughput measurement
- `scapy` — packet capture and assertion
- `iptables` — firewall rule manipulation on DUT
- `ruff` — linting
- GitHub Actions — CI/CD pipeline
