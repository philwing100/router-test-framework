# Custom Firmware Build — RT-AC66U
## netmon daemon project

This document is a task checklist and question guide for building and flashing
a custom firmware image containing a network monitoring daemon onto the ASUS
RT-AC66U. Work through each phase in order. Do not skip ahead — later steps
depend on decisions made in earlier ones.

---

## Phase 1 — Obtain the GPL Source

### Tasks
- [ ] Go to the ASUS support page for the RT-AC66U and locate the GPL source
      download for firmware version 3.0.0.4
- [ ] Download the GPL tarball to your laptop
- [ ] Extract the tarball and inventory the top-level directory structure
- [ ] Locate the router source tree (typically under `release/src/router/`)
- [ ] Locate the existing init/rc scripts that control service startup at boot
- [ ] Locate where existing daemon binaries are placed before image creation
- [ ] Locate the build output directory where `.trx` firmware images are written

### Questions to answer before moving on
- What is the exact top-level directory structure of the GPL tree?
- Where are existing third-party daemons (e.g. dnsmasq, httpd) located in the
  source tree? This is where netmon will live.
- Where are compiled binaries staged before being packed into the firmware
  image? (look for a `romfs`, `rom`, or `staging` directory)
- Does the GPL tree include a pre-built toolchain, or do you need to install
  one separately? Run `find . -name "*gcc" | grep mips` to check.
- What is the exact make target for the RT-AC66U? Check the top-level Makefile
  for target names containing `ac66`.

---

## Phase 2 — Set Up the Build Environment

### Tasks
- [ ] Identify whether the GPL tree ships its own MIPS toolchain or requires
      a system-installed one
- [ ] Install required host build dependencies on your laptop
- [ ] Attempt a dry run of the top-level build to see how far it gets before
      failing
- [ ] Resolve any missing dependency errors one at a time
- [ ] Confirm the toolchain can compile a minimal hello world C file targeting
      MIPS
- [ ] Confirm the resulting binary is the correct architecture by running
      `file` on the output

### Questions to answer before moving on
- What host OS and version are you building on? (Ubuntu version matters for
  dependency availability)
- Did the dry run build fail? If so, what was the first error message?
- What MIPS toolchain prefix does the build system expect? (look for CC= or
  CROSS_COMPILE= in the Makefiles — it will be something like
  `mips-linux-gnu-` or `mipsel-linux-`)
- Is the toolchain MIPS big-endian or little-endian? Run `file` on an existing
  binary in the GPL tree to check. The RT-AC66U BCM4706 is big-endian MIPS.
- Do you need a 32-bit host environment or will 64-bit work? Some older ASUS
  GPL trees require a 32-bit build host.

---

## Phase 3 — Write the Daemon

### Tasks
- [ ] Create a new directory for the netmon daemon under the router source tree
- [ ] Write `netmon.c` — the daemon source file
- [ ] Write a `Makefile` for the daemon directory
- [ ] Cross-compile the daemon manually using the toolchain identified in
      Phase 2 to verify it compiles cleanly before touching the build system
- [ ] Run `file` on the compiled binary to confirm it is MIPS ELF
- [ ] Transfer the binary to the router via USB or wget and run it manually
      to verify it starts, logs to syslog, and responds on port 9000
- [ ] Verify the TCP response contains valid JSON with interface stats
- [ ] Verify anomaly logging appears in syslog when errors are injected

### Questions to answer before moving on
- Does the daemon start cleanly as a background process on the router?
- What does `/proc/net/dev` look like on this firmware? Confirm the column
  layout matches what the parser expects. Run `cat /proc/net/dev` over telnet.
- Does the router's syslog capture output from the daemon? Check with
  `logread` over telnet.
- Can you connect to port 9000 on 192.168.1.1 from your laptop and receive
  a JSON response?
- Does the JSON output contain all expected interfaces (lo, br0, vlan1,
  vlan2, eth0, eth1, eth2)?
- Does the process stay running after you close the telnet session? Test with
  `ps | grep netmon` after disconnecting.

---

## Phase 4 — Integrate Into the Build System

### Tasks
- [ ] Add the netmon directory to the router-level Makefile so it builds as
      part of the full firmware build
- [ ] Identify the correct init script or rc service file where daemons are
      launched at boot
- [ ] Add a start command for netmon in the correct location in the init
      sequence — it should start after networking is up
- [ ] Add a stop/kill command for clean shutdown
- [ ] Identify where to stage the compiled binary so it gets packed into the
      firmware image filesystem
- [ ] Add the binary staging step to the build process
- [ ] Confirm netmon appears in the correct location in the unpacked filesystem
      before attempting a full image build

### Questions to answer before moving on
- Which rc script controls service startup? Is it `rc/init.c`, `rc/services.c`,
  or a shell script? Look at how dnsmasq is started for reference.
- What is the correct point in the boot sequence to start netmon? It must
  start after br0 is up and has an IP address. Find where the LAN bridge
  is initialized.
- What directory does the build system use to stage the root filesystem before
  packing? (romfs, staging_dir, or similar)
- What is the path inside the firmware filesystem where sbin daemons live?
  Confirm by checking `which dnsmasq` on the live router over telnet.
- Does the build system require you to list the binary explicitly in a manifest
  or package file, or does staging it in the right directory suffice?

---

## Phase 5 — Build the Firmware Image

### Tasks
- [ ] Run the full firmware build using the correct make target for the RT-AC66U
- [ ] Resolve any build errors that appear — document each one and its fix
- [ ] Locate the output `.trx` image file when the build completes
- [ ] Confirm the image file size is in the expected range for this router
      (check the size of the stock 3.0.0.4 firmware as a reference)
- [ ] Unpack the image and verify netmon is present at the correct path inside
      the filesystem before flashing

### Questions to answer before moving on
- Did the build complete without errors?
- What is the exact path and filename of the output image?
- What is the file size of the output image compared to the stock firmware?
  A dramatically larger image may not fit in flash.
- How much flash space is available on the RT-AC66U? (128MB flash, but most
  is used — confirm the partition layout with `cat /proc/mtd` over telnet)
- Can you extract and inspect the squashfs filesystem from the image to
  confirm netmon is present before flashing?

---

## Phase 6 — Flash the Firmware

### Tasks
- [ ] Back up the current working firmware by downloading it from the web UI
      before flashing anything custom
- [ ] Document the exact recovery procedure for a failed flash before starting
- [ ] Flash the custom image via the web UI firmware upgrade page
- [ ] Wait for the router to fully reboot — do not interrupt power
- [ ] Confirm the router comes back up and is reachable at 192.168.1.1
- [ ] Connect via telnet and confirm the firmware version string reflects your
      custom build
- [ ] Confirm netmon is running with `ps | grep netmon`
- [ ] Confirm netmon is logging to syslog with `logread | grep netmon`
- [ ] Confirm port 9000 responds with JSON from your laptop

### Questions to answer before moving on
- Does the ASUS web UI accept the custom .trx image, or does it reject it
  with a signature/checksum error? Some ASUS firmware versions verify image
  signatures.
- If the web UI rejects the image, is recovery mode (hold reset at power on)
  available as a fallback flashing method?
- After flashing, does the router boot into your firmware or fall back to
  stock? Check the firmware version string in the web UI or via telnet:
  `nvram get buildno`
- Is netmon present at the expected path? Run `ls -la /usr/sbin/netmon`
- Is netmon actually running at boot, or does it need to be started manually?
  Reboot the router and check `ps` output without manually starting it.

### Recovery procedure (document this before flashing)
- Power off the router
- Hold the reset button while applying power
- Router enters CFE recovery mode and serves a web interface at 192.168.1.1
- Use the ASUS Firmware Restoration utility (Windows) or a direct HTTP POST
  to upload a known-good firmware image
- Allow 5 minutes for flash and reboot
- Keep a copy of the stock 3.0.0.4 firmware downloaded before you start

---

## Phase 7 — Query From the Python Test Framework

### Tasks
- [ ] Add a `NetmonClient` class to `lib/` in the netval test framework
- [ ] Write `tests/test_netmon.py` with the following test cases:
      - Router responds on port 9000
      - Response is valid JSON
      - All expected interfaces are present in the response
      - No interface has non-zero error counts under normal conditions
      - br0 shows non-zero rx_bytes and tx_bytes when traffic is passing
      - Rates (bytes per second) are within expected range for idle state
- [ ] Add netmon tests to the CI pipeline
- [ ] Generate traffic with iperf3 and assert that br0 rate stats increase
      in the netmon response
- [ ] Document the full query → assert flow in the README

### Questions to answer before moving on
- Does the NetmonClient connect reliably, or does the daemon occasionally
  drop connections?
- Are the rate calculations accurate? Cross-check bytes-per-second from
  netmon against iperf3 reported throughput.
- Does the daemon survive continuous querying without memory growth or crashes?
  Run `ps` and check VSZ/RSS after 100 queries.
- What happens to the daemon if the router has been up for a long time and
  counters overflow? The RT-AC66U uses 32-bit counters in older kernels —
  confirm whether `/proc/net/dev` on kernel 2.6.22 uses 32 or 64-bit values.

---

## Known Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Web UI rejects custom image (signature check) | Medium | Use CFE recovery mode via reset button |
| GPL build fails due to old host dependencies | High | Try building in a Ubuntu 14.04 Docker container which matches the era of this firmware |
| Flash corrupted, router unresponsive | Low | CFE recovery mode is independent of firmware |
| netmon not starting at boot despite init changes | Medium | Test by manually running it first, then trace exactly where in init sequence networking comes up |
| 32-bit counter overflow in /proc/net/dev | Low | Add overflow detection in the daemon and handle wrap-around |
| Image too large for flash partition | Medium | Check MTD partition sizes first with `cat /proc/mtd` before building |

---

## References

- ASUS GPL source downloads: https://www.asus.com/networking-iot-servers/wifi-routers/asus-wifi-routers/rt-ac66u/helpdesk_bios/
- BCM4706 is big-endian MIPS32 — ensure toolchain matches
- Firmware partition layout: check `cat /proc/mtd` on the live router
- Stock firmware version for recovery: 3.0.0.4 (keep a local copy)
- netmon TCP port: 9000 (confirm not already in use with `netstat -tlnp` on router)
