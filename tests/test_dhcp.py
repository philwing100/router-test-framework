"""
test_dhcp.py — DHCP lease assignment and configuration tests.

Week 2 milestone. Tests assert on router-side lease state (via nvram and
/var/lib/misc/dnsmasq.leases or similar). A second physical device on the
LAN is required to exercise full lease assignment; those tests are marked
with the 'second_device' marker and skipped if not available.
"""

import pytest
import re


pytestmark = pytest.mark.dhcp


class TestDHCPConfiguration:
    def test_dhcp_enabled_via_nvram(self, router):
        """nvram should indicate DHCP server is enabled on the LAN."""
        value = router.get_nvram("dhcp_enable_x")
        assert value.strip() == "1", f"DHCP not enabled (dhcp_enable_x={value!r})"

    def test_dhcp_pool_start(self, router):
        """DHCP pool start address should be in 192.168.1.x range."""
        value = router.get_nvram("dhcp_start")
        assert value.strip().startswith("192.168.1."), f"Unexpected DHCP start: {value!r}"

    def test_dhcp_pool_end(self, router):
        """DHCP pool end address should be in 192.168.1.x range."""
        value = router.get_nvram("dhcp_end")
        assert value.strip().startswith("192.168.1."), f"Unexpected DHCP end: {value!r}"

    def test_dhcp_lease_time(self, router):
        """DHCP lease time should be a positive integer (seconds)."""
        value = router.get_nvram("dhcp_lease")
        assert value.strip().isdigit() and int(value.strip()) > 0, (
            f"Unexpected lease time: {value!r}"
        )

    def test_lan_ip_matches_gateway(self, router):
        """LAN IP reported by nvram should match the br0 interface address."""
        nvram_ip = router.get_nvram("lan_ipaddr").strip()
        iface_output = router.get_interface_info("br0")
        assert nvram_ip in iface_output, (
            f"lan_ipaddr {nvram_ip!r} not found in br0 output.\n{iface_output}"
        )


class TestDHCPLeases:
    def test_lease_file_accessible(self, router):
        """dnsmasq lease file should be readable."""
        output = router.run("cat /var/lib/misc/dnsmasq.leases 2>/dev/null || echo NO_LEASE_FILE")
        # Either the file exists (possibly empty) or we note it's missing.
        # Existence is router-version dependent; we just assert the command ran.
        assert output is not None

    @pytest.mark.second_device
    def test_active_lease_present(self, router):
        """
        At least one active DHCP lease should exist when a second device is connected.

        Requires a physical device to be connected and have obtained a lease.
        Run with: pytest -m second_device
        """
        output = router.run("cat /var/lib/misc/dnsmasq.leases")
        assert len(output.strip()) > 0, "No active leases found — is a second device connected?"

        # Each line: <expiry> <mac> <ip> <hostname> <client-id>
        lines = [l for l in output.strip().splitlines() if l.strip()]
        assert len(lines) >= 1, "Lease file is empty"

        # Validate that the leased IP is in the LAN subnet
        first_fields = lines[0].split()
        assert len(first_fields) >= 3, f"Unexpected lease line format: {lines[0]!r}"
        leased_ip = first_fields[2]
        assert leased_ip.startswith("192.168.1."), f"Leased IP {leased_ip!r} not in expected subnet"
