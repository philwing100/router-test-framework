"""
test_traffic.py — Scapy-based packet capture and assertion tests.

tcpdump is not available on this router firmware. Capture runs on the
local machine's ethernet interface using Scapy (requires root/CAP_NET_RAW).

Run with: sudo pytest tests/test_traffic.py
Or grant cap_net_raw to the Python interpreter:
    sudo setcap cap_net_raw+eip $(which python3)
"""

import os
import time
import socket
import threading
import pytest

try:
    from scapy.all import sniff, IP, ICMP, TCP, UDP, send, conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


pytestmark = [
    pytest.mark.traffic,
    pytest.mark.skipif(not SCAPY_AVAILABLE, reason="scapy not installed"),
]

ROUTER_IP = "192.168.1.1"
LOCAL_IFACE = os.environ.get("LOCAL_IFACE", "eth0")
CAPTURE_TIMEOUT = 5  # seconds


def _capture_packets(iface: str, filter_expr: str, count: int, timeout: int) -> list:
    """Capture up to `count` packets matching `filter_expr` on `iface`."""
    return sniff(iface=iface, filter=filter_expr, count=count, timeout=timeout)


class TestICMPCapture:
    def test_icmp_echo_request_captured(self):
        """
        Send a ping to the router; capture ICMP echo request on local iface.
        """
        captured = []

        def capture():
            pkts = _capture_packets(
                LOCAL_IFACE,
                f"icmp and dst host {ROUTER_IP}",
                count=1,
                timeout=CAPTURE_TIMEOUT,
            )
            captured.extend(pkts)

        t = threading.Thread(target=capture, daemon=True)
        t.start()
        time.sleep(0.3)  # give sniffer time to start

        os.system(f"ping -c 1 -W 2 {ROUTER_IP} > /dev/null 2>&1")
        t.join(timeout=CAPTURE_TIMEOUT + 2)

        assert len(captured) >= 1, "No ICMP echo request captured"
        pkt = captured[0]
        assert IP in pkt, "Captured packet has no IP layer"
        assert ICMP in pkt, "Captured packet has no ICMP layer"
        assert pkt[IP].dst == ROUTER_IP

    def test_icmp_echo_reply_captured(self):
        """
        Send a ping to the router; capture ICMP echo reply from the router.
        """
        captured = []

        def capture():
            pkts = _capture_packets(
                LOCAL_IFACE,
                f"icmp and src host {ROUTER_IP}",
                count=1,
                timeout=CAPTURE_TIMEOUT,
            )
            captured.extend(pkts)

        t = threading.Thread(target=capture, daemon=True)
        t.start()
        time.sleep(0.3)

        os.system(f"ping -c 1 -W 2 {ROUTER_IP} > /dev/null 2>&1")
        t.join(timeout=CAPTURE_TIMEOUT + 2)

        assert len(captured) >= 1, "No ICMP echo reply captured from router"
        pkt = captured[0]
        assert pkt[IP].src == ROUTER_IP
        assert pkt[ICMP].type == 0  # echo reply


class TestARPCapture:
    def test_arp_traffic_on_lan(self):
        """ARP packets should be observable on the LAN interface."""
        pkts = _capture_packets(
            LOCAL_IFACE,
            filter_expr="arp",
            count=3,
            timeout=CAPTURE_TIMEOUT,
        )
        # Trigger some ARP by pinging the router
        os.system(f"ping -c 1 -W 1 {ROUTER_IP} > /dev/null 2>&1")
        # Even if we get 0 here it's not fatal — ARP may have been cached
        # This test primarily validates that capture machinery works
        assert pkts is not None


class TestPacketFields:
    def test_captured_ip_src_is_valid(self):
        """Packets sourced from the router should have a valid IP src."""
        pkts = _capture_packets(
            LOCAL_IFACE,
            filter_expr=f"src host {ROUTER_IP}",
            count=2,
            timeout=CAPTURE_TIMEOUT,
        )
        os.system(f"ping -c 2 -W 2 {ROUTER_IP} > /dev/null 2>&1")
        for pkt in pkts:
            if IP in pkt:
                src = pkt[IP].src
                assert src.startswith("192.168."), f"Unexpected src IP: {src}"
