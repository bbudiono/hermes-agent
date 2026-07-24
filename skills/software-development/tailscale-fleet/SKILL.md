---
name: tailscale-fleet
description: "Fleet-wide SSH mesh verification and repair using fleet_ssh_mesh.sh. Read the mesh health matrix, run repairs, and report per-host status. Source: ~/.agents/scripts/fleet_ssh_mesh.sh"
version: 1.0.0
author: Hermes Agent
platforms: [macos, linux]
tags: [tailscale, ssh, fleet, infrastructure, networking]
source: ~/.agents/scripts/fleet_ssh_mesh.sh
---

# Tailscale Fleet SSH Mesh

Idempotent SSH mesh that gives every fleet Mac (and Hermes' host) passwordless SSH to every other fleet device via Tailscale MagicDNS.

**Fleet topology:**
```
FLEET_MACS:    bernie-macbookpro-m4, bernie-mac-studio-11119, bernie-macmini-m4, bernie-macmini-m4-02
HERMES_HOST:    bernie-macmini-m4  (Mac Mini M4 — this machine)
LINUX_SERVERS:  ai-server-01, ai-server-02, ai-server-03, ai-server-05, ai-server-06
EXCLUDED:      kaylyn-macbookpro-m3 (family device, P0.43 — manual seed required by Bernhard)
                ai-server-04 (hardware fault, drained)
```

**Users:** `bernhardbudiono` on all Macs · `bernhard-budiono` on all Linux servers
**DNS suffix:** `.tail164f4e.ts.net` (MagicDNS)

## Quick Reference

```bash
# Verify only — no changes
bash ~/.agents/scripts/fleet_ssh_mesh.sh --verify-only

# Full repair (idempotent — safe to re-run)
bash ~/.agents/scripts/fleet_ssh_mesh.sh

# From any Mac: check specific host reachability
ssh -o ConnectTimeout=5 -o BatchMode=yes bernhardbudiono@<host>.tail164f4e.ts.net "echo ok"
```

## What the script does (all idempotent)

1. **Ensure ed25519 keypair** on every fleet Mac
2. **Collect + distribute union pubkeys** — every Mac's `~/.ssh/authorized_keys` gets every other Mac's key
3. **Fix MagicDNS** — installs `/etc/resolver/ts.net → 100.100.100.100` on homebrew-variant tailscaled Macs (skips if already present)
4. **Seed Linux servers** — ensures Hermes host key is authorized on all Linux AI servers
5. **Verification matrix** — prints every edge with OK/FAIL; exits 0 only if all healthy

## Usage Patterns

### Check mesh health (read-only)
```
bash ~/.agents/scripts/fleet_ssh_mesh.sh --verify-only
```
Output: `OK` / `FAIL` per edge. Exit 0 = all healthy.

### Repair mesh
```
bash ~/.agents/scripts/fleet_ssh_mesh.sh
```
Idempotent. Safe to run any time. Fixes broken edges by redistributing keys.

### Manual single-host check
```bash
# Mac
ssh -o ConnectTimeout=5 -o BatchMode=yes bernhardbudiono@bernie-mac-studio-11119.tail164f4e.ts.net "echo ok"

# Linux
ssh -o ConnectTimeout=5 -o BatchMode=yes bernhard-budiono@ai-server-06.tail164f4e.ts.net "echo ok"
```

## Expected mesh matrix (healthy)

```
  bernie-macbookpro-m4   → bernie-mac-studio-11119  OK
  bernie-macbookpro-m4   → bernie-macmini-m4         OK
  bernie-macbookpro-m4   → bernie-macmini-m4-02      OK
  bernie-mac-studio-11119 → bernie-macbookpro-m4     OK
  bernie-mac-studio-11119 → bernie-macmini-m4        OK
  bernie-mac-studio-11119 → bernie-macmini-m4-02     OK
  bernie-macmini-m4       → bernie-macbookpro-m4     OK
  bernie-macmini-m4       → bernie-mac-studio-11119  OK
  bernie-macmini-m4       → bernie-macmini-m4-02      OK
  bernie-macmini-m4-02   → bernie-macbookpro-m4      OK
  bernie-macmini-m4-02   → bernie-mac-studio-11119   OK
  bernie-macmini-m4-02   → bernie-macmini-m4          OK
  hermes(bernie-macmini-m4) → ai-server-01           OK
  hermes(bernie-macmini-m4) → ai-server-02           OK
  hermes(bernie-macmini-m4) → ai-server-03           OK
  hermes(bernie-macmini-m4) → ai-server-05           OK
  hermes(bernie-macmini-m4) → ai-server-06           OK
```

## Pitfalls

1. **"no path in"** for ai-server-06 — server is genuinely offline or unreachable. Not a key/auth issue. Check if it has come back online with a direct ping before re-running.
2. **"ts.net resolution broken"** — MagicDNS not working on a Mac. Run: `printf "nameserver 100.100.100.100\n" | sudo tee /etc/resolver/ts.net` manually, or confirm the Mac is on Tailscale.
3. **kaylyn-macbookpro-m3** — family device, intentionally excluded. Do NOT attempt to seed it.
4. **ai-server-04** — hardware fault, intentionally excluded from mesh.
5. **BatchMode=yes** — if a key is missing, SSH fails immediately with "Permission denied (publickey)" rather than hanging on a password prompt.
6. **Passwordless sudo required** for MagicDNS fix on some Macs. The script checks `sudo -n` first and skips loudly if not available.

## Verification
```bash
bash ~/.agents/scripts/fleet_ssh_mesh.sh --verify-only && echo "MESH HEALTHY"
```
