#!/usr/bin/env bash
# capture.sh — local tcpdump/scapy capture wrapper
#
# Usage:
#   ./scripts/capture.sh [iface] [filter] [output.pcap]
#
# Defaults:
#   iface   = eth0  (override with LOCAL_IFACE env var)
#   filter  = ""    (capture everything)
#   output  = captures/capture_<timestamp>.pcap

set -euo pipefail

IFACE="${LOCAL_IFACE:-eth0}"
FILTER="${2:-}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="${3:-captures/capture_${TIMESTAMP}.pcap}"

mkdir -p "$(dirname "$OUTPUT")"

echo "Capturing on interface: $IFACE"
echo "Filter: ${FILTER:-<none>}"
echo "Output: $OUTPUT"
echo "Press Ctrl+C to stop."
echo ""

if command -v tcpdump &>/dev/null; then
    tcpdump -i "$IFACE" -w "$OUTPUT" ${FILTER:+-f "$FILTER"}
else
    # Fall back to scapy if tcpdump is unavailable
    python3 - <<PYEOF
from scapy.all import sniff, wrpcap
import sys

iface = "$IFACE"
filt  = "$FILTER" or None
out   = "$OUTPUT"

print(f"scapy: sniffing on {iface}" + (f" with filter '{filt}'" if filt else ""))
pkts = sniff(iface=iface, filter=filt, store=True)
wrpcap(out, pkts)
print(f"Written {len(pkts)} packets to {out}")
PYEOF
fi
