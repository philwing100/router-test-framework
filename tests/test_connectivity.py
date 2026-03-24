"""
test_connectivity.py — Basic reachability and interface state tests.

Week 1 milestone: connect → run command → assert expected output.
"""

import pytest


class TestInterfaceState:
    def test_br0_is_up(self, router):
        """LAN bridge br0 should be UP with IP 192.168.1.1/24."""
        output = router.get_interface_info("br0")
        assert "UP" in output, f"br0 not UP.\n{output}"
        assert "192.168.1.1/24" in output, f"Expected IP not on br0.\n{output}"

    def test_eth1_exists(self, router):
        """2.4GHz radio interface eth1 should be present."""
        output = router.get_interface_info("eth1")
        assert "eth1" in output, f"eth1 not found.\n{output}"

    def test_eth2_exists(self, router):
        """5GHz radio interface eth2 should be present."""
        output = router.get_interface_info("eth2")
        assert "eth2" in output, f"eth2 not found.\n{output}"

    def test_all_interfaces(self, router):
        """ip addr show should list br0, eth1, eth2, vlan1, vlan2."""
        output = router.run("ip addr")
        for iface in ("br0", "eth1", "eth2", "vlan1", "vlan2"):
            assert iface in output, f"Interface {iface} missing from ip addr output.\n{output}"


class TestReachability:
    def test_loopback_ping(self, router):
        """Router should be able to ping its own loopback."""
        output = router.run("ping -c 3 127.0.0.1")
        assert "3 packets transmitted" in output
        assert "3 received" in output

    def test_lan_self_ping(self, router):
        """Router should be able to ping its own LAN IP."""
        output = router.run("ping -c 3 192.168.1.1")
        assert "3 packets transmitted" in output
        assert "3 received" in output

    def test_default_route_present(self, router):
        """ip route should contain at least a LAN-connected route."""
        output = router.get_routes()
        assert "192.168.1.0" in output, f"LAN route not found.\n{output}"


class TestIptablesBasic:
    def test_iptables_chains_present(self, router):
        """iptables filter table should have INPUT, FORWARD, OUTPUT chains."""
        output = router.get_iptables_rules()
        for chain in ("Chain INPUT", "Chain FORWARD", "Chain OUTPUT"):
            assert chain in output, f"{chain} not found in iptables -L output.\n{output}"
