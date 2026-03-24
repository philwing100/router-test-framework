"""
test_throughput.py — iperf3 throughput performance tests.

Week 4 milestone (requires iperf3 server on a second LAN device).
The local machine acts as iperf3 client; the second device runs iperf3 -s.

Configure the server IP via --iperf-server pytest option or the
IPERF_SERVER env var. Tests are skipped if no server is reachable.
"""

import json
import shutil
import subprocess
import os
import pytest


pytestmark = pytest.mark.throughput

DEFAULT_IPERF_SERVER = os.environ.get("IPERF_SERVER", "192.168.1.100")
IPERF_DURATION = 5  # seconds


def pytest_addoption(parser):
    # Note: if conftest.py already adds this, remove from here.
    try:
        parser.addoption(
            "--iperf-server",
            default=DEFAULT_IPERF_SERVER,
            help="IP of the iperf3 server on the LAN",
        )
    except ValueError:
        pass  # already added by conftest


@pytest.fixture(scope="session")
def iperf_server(request):
    return request.config.getoption("--iperf-server", default=DEFAULT_IPERF_SERVER)


@pytest.fixture(scope="session", autouse=True)
def require_iperf3():
    if shutil.which("iperf3") is None:
        pytest.skip("iperf3 not found in PATH — install it to run throughput tests")


def _run_iperf3(server: str, protocol: str = "tcp", duration: int = IPERF_DURATION, reverse: bool = False) -> dict:
    cmd = [
        "iperf3",
        "-c", server,
        "-t", str(duration),
        "-J",  # JSON output
    ]
    if protocol == "udp":
        cmd += ["-u", "-b", "100M"]
    if reverse:
        cmd.append("-R")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 15)
    if result.returncode != 0:
        pytest.skip(f"iperf3 server at {server} not reachable: {result.stderr.strip()}")

    return json.loads(result.stdout)


class TestTCPThroughput:
    def test_tcp_upload_nonzero(self, iperf_server):
        """TCP upload throughput to LAN server should be > 0 Mbps."""
        data = _run_iperf3(iperf_server, protocol="tcp")
        bits_per_second = data["end"]["sum_sent"]["bits_per_second"]
        mbps = bits_per_second / 1e6
        assert mbps > 0, f"TCP upload reported 0 Mbps"
        print(f"\nTCP upload: {mbps:.1f} Mbps")

    def test_tcp_download_nonzero(self, iperf_server):
        """TCP download throughput from LAN server should be > 0 Mbps."""
        data = _run_iperf3(iperf_server, protocol="tcp", reverse=True)
        bits_per_second = data["end"]["sum_received"]["bits_per_second"]
        mbps = bits_per_second / 1e6
        assert mbps > 0, f"TCP download reported 0 Mbps"
        print(f"\nTCP download: {mbps:.1f} Mbps")

    def test_tcp_upload_meets_minimum(self, iperf_server):
        """TCP upload should exceed 10 Mbps on a local LAN (no WAN bottleneck)."""
        data = _run_iperf3(iperf_server, protocol="tcp")
        bits_per_second = data["end"]["sum_sent"]["bits_per_second"]
        mbps = bits_per_second / 1e6
        assert mbps >= 10, f"TCP upload {mbps:.1f} Mbps is below 10 Mbps minimum"

    def test_tcp_retransmits_low(self, iperf_server):
        """TCP retransmit count should be low on a clean LAN path."""
        data = _run_iperf3(iperf_server, protocol="tcp")
        retransmits = data["end"]["sum_sent"].get("retransmits", 0)
        assert retransmits < 100, f"High TCP retransmit count: {retransmits}"


class TestUDPThroughput:
    def test_udp_upload_nonzero(self, iperf_server):
        """UDP upload throughput should be > 0 Mbps."""
        data = _run_iperf3(iperf_server, protocol="udp")
        bits_per_second = data["end"]["sum"]["bits_per_second"]
        mbps = bits_per_second / 1e6
        assert mbps > 0, f"UDP upload reported 0 Mbps"
        print(f"\nUDP upload: {mbps:.1f} Mbps")

    def test_udp_packet_loss_acceptable(self, iperf_server):
        """UDP packet loss should be under 1% on a clean LAN."""
        data = _run_iperf3(iperf_server, protocol="udp")
        lost = data["end"]["sum"].get("lost_percent", 0)
        assert lost < 1.0, f"UDP packet loss {lost:.2f}% exceeds 1% threshold"
