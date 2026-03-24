"""
reporter.py — JUnit XML and HTML report generation helpers.

pytest-html and junit-xml are used as backends. This module provides
thin wrappers so tests don't import third-party libs directly, making
future backend swaps easy.
"""

import datetime
import xml.etree.ElementTree as ET
from pathlib import Path


def write_junit_xml(results: list[dict], output_path: str = "report.xml") -> None:
    """
    Write a minimal JUnit XML report.

    Each result dict must have:
        name (str), status ('pass'|'fail'|'error'|'skip'),
        duration (float, seconds), message (str, optional)
    """
    now = datetime.datetime.utcnow().isoformat()
    failures = sum(1 for r in results if r["status"] == "fail")
    errors = sum(1 for r in results if r["status"] == "error")

    suite = ET.Element(
        "testsuite",
        name="router-test-framework",
        tests=str(len(results)),
        failures=str(failures),
        errors=str(errors),
        timestamp=now,
    )

    for r in results:
        tc = ET.SubElement(suite, "testcase", name=r["name"], time=f"{r.get('duration', 0):.3f}")
        if r["status"] == "fail":
            fail = ET.SubElement(tc, "failure", message=r.get("message", ""))
            fail.text = r.get("message", "")
        elif r["status"] == "error":
            err = ET.SubElement(tc, "error", message=r.get("message", ""))
            err.text = r.get("message", "")
        elif r["status"] == "skip":
            ET.SubElement(tc, "skipped", message=r.get("message", ""))

    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="unicode", xml_declaration=True)
    print(f"JUnit XML report written to {path}")
