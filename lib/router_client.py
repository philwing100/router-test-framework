"""
RouterClient — telnetlib wrapper for the ASUS RT-AC66U.

SSH is unavailable on this firmware (ASUSWRT 3.0.0.4), so telnet is used
as the transport layer. Tests interact only with this abstraction and are
therefore transport-agnostic.
"""

import telnetlib
import time
import re


PROMPT = b"#"
LOGIN_TIMEOUT = 10
CMD_TIMEOUT = 15
ENCODING = "utf-8"


class RouterClientError(Exception):
    pass


class RouterClient:
    def __init__(self, host: str = "192.168.1.1", user: str = "admin", password: str = "admin", port: int = 23):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self._tn: telnetlib.Telnet | None = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the telnet session and authenticate."""
        self._tn = telnetlib.Telnet(self.host, self.port, timeout=LOGIN_TIMEOUT)

        self._tn.read_until(b"login: ", LOGIN_TIMEOUT)
        self._tn.write(self.user.encode(ENCODING) + b"\n")

        self._tn.read_until(b"Password: ", LOGIN_TIMEOUT)
        self._tn.write(self.password.encode(ENCODING) + b"\n")

        # Wait for shell prompt (#)
        index, _, _ = self._tn.expect([PROMPT], LOGIN_TIMEOUT)
        if index == -1:
            raise RouterClientError("Authentication failed — shell prompt not received")

    def disconnect(self) -> None:
        """Close the telnet connection cleanly."""
        if self._tn:
            try:
                self._tn.write(b"exit\n")
            except Exception:
                pass
            self._tn.close()
            self._tn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def run(self, command: str, timeout: float = CMD_TIMEOUT) -> str:
        """
        Send a shell command and return stdout as a string.

        Uses a unique sentinel echo to reliably detect command completion,
        which avoids false-positive prompt matches inside command output.
        """
        if self._tn is None:
            raise RouterClientError("Not connected — call connect() first")

        sentinel = f"__END_{int(time.time() * 1000)}__"
        full_cmd = f"{command}; echo {sentinel}\n"
        self._tn.write(full_cmd.encode(ENCODING))

        output_bytes = self._tn.read_until(sentinel.encode(ENCODING), timeout)
        output = output_bytes.decode(ENCODING, errors="replace")

        # Strip the echoed command and the sentinel line
        lines = output.splitlines()
        result_lines = []
        for line in lines:
            if command in line:
                continue
            if sentinel in line:
                break
            result_lines.append(line)

        return "\n".join(result_lines).strip()

    def run_and_expect(self, command: str, expected: str, timeout: float = CMD_TIMEOUT) -> str:
        """Run a command and assert that expected string appears in output."""
        output = self.run(command, timeout)
        if expected not in output:
            raise AssertionError(
                f"Expected {expected!r} not found in output of {command!r}.\nOutput:\n{output}"
            )
        return output

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def get_interface_info(self, iface: str) -> str:
        return self.run(f"ip addr show {iface}")

    def get_iptables_rules(self, table: str = "filter") -> str:
        return self.run(f"iptables -t {table} -L -n -v")

    def get_nvram(self, key: str) -> str:
        return self.run(f"nvram get {key}")

    def get_routes(self) -> str:
        return self.run("ip route show")
