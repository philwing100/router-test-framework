"""
test_firewall.py — iptables rule manipulation tests.

Week 3 milestone. Each test adds a rule, asserts it is present, then
removes it — leaving the router in its original state regardless of
test outcome. A pytest fixture handles cleanup so rules aren't leaked
even on test failure.
"""

import pytest


pytestmark = pytest.mark.firewall

# Unique comment tag so we can reliably grep our test-injected rules
RULE_COMMENT = "rtf-test"


@pytest.fixture(autouse=True)
def cleanup_test_rules(router):
    """Remove any leftover test rules before and after each test."""
    _flush_test_rules(router)
    yield
    _flush_test_rules(router)


def _flush_test_rules(router):
    """Delete all INPUT rules whose comment matches RULE_COMMENT."""
    # iptables on this firmware may not support --line-numbers; use -D by spec
    router.run(
        f"iptables -L INPUT -n --line-numbers 2>/dev/null | "
        f"grep {RULE_COMMENT} | awk '{{print $1}}' | sort -rn | "
        f"xargs -I{{}} iptables -D INPUT {{}} 2>/dev/null; true"
    )


class TestIptablesRuleLifecycle:
    def test_add_drop_rule_appears_in_chain(self, router):
        """Adding a DROP rule should make it visible in iptables -L."""
        router.run(
            f"iptables -I INPUT -p tcp --dport 9999 -j DROP -m comment --comment {RULE_COMMENT}"
        )
        output = router.get_iptables_rules()
        assert "9999" in output, f"Rule for port 9999 not found after adding.\n{output}"
        assert "DROP" in output

    def test_remove_rule_disappears_from_chain(self, router):
        """Removing a rule should make it absent from iptables -L."""
        router.run(
            f"iptables -I INPUT -p tcp --dport 9998 -j DROP -m comment --comment {RULE_COMMENT}"
        )
        output_before = router.get_iptables_rules()
        assert "9998" in output_before, "Rule was not added — precondition failed."

        router.run(
            f"iptables -D INPUT -p tcp --dport 9998 -j DROP -m comment --comment {RULE_COMMENT}"
        )
        output_after = router.get_iptables_rules()
        assert "9998" not in output_after, f"Rule for port 9998 still present after deletion.\n{output_after}"

    def test_accept_rule_for_lan(self, router):
        """Should be able to insert an ACCEPT rule for LAN subnet."""
        router.run(
            f"iptables -I INPUT -s 192.168.1.0/24 -j ACCEPT -m comment --comment {RULE_COMMENT}"
        )
        output = router.get_iptables_rules()
        assert "192.168.1.0/24" in output or "192.168.1.0" in output, (
            f"LAN ACCEPT rule not found.\n{output}"
        )

    def test_multiple_rules_independent(self, router):
        """Multiple rules can be added and each is independently verifiable."""
        ports = [19001, 19002, 19003]
        for port in ports:
            router.run(
                f"iptables -I INPUT -p tcp --dport {port} -j DROP -m comment --comment {RULE_COMMENT}"
            )

        output = router.get_iptables_rules()
        for port in ports:
            assert str(port) in output, f"Rule for port {port} missing.\n{output}"

    def test_nat_table_accessible(self, router):
        """iptables NAT table should be readable."""
        output = router.run("iptables -t nat -L -n")
        assert "Chain PREROUTING" in output, f"NAT table not accessible.\n{output}"
        assert "Chain POSTROUTING" in output
