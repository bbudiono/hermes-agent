#!/bin/bash
# fleet_ssh_mesh.sh — idempotent macOS-fleet SSH mesh: every fleet Mac can
# passwordless-SSH to every other, and Hermes' host (bernie-macmini-m4) can
# reach the Linux AI servers too. Safe to re-run any time ("the fix IS the
# script"). Born 2026-07-18 (user directive: all Macs talk + passwordless SSH;
# hardened + easily rectified).
#
# What it does (all idempotent):
#   1. Ensures an ed25519 keypair exists on every fleet Mac.
#   2. Collects all fleet-Mac pubkeys and appends the UNION to every fleet
#      Mac's ~/.ssh/authorized_keys (dedup by key material; 700/600 perms).
#   3. Fixes MagicDNS on Macs running the homebrew tailscaled variant by
#      installing /etc/resolver/ts.net -> 100.100.100.100 (needs passwordless
#      sudo on the target; skips loudly if unavailable).
#   4. Ensures the Hermes host key is authorized on the Linux AI servers.
#   5. Prints a full verification matrix; exits 1 if any expected edge fails.
#
# Out of scope (reported, never touched): kaylyn-macbookpro-m3 (family device,
# profile-scoped per P0.43 — needs a one-time manual initial auth to seed),
# offline devices (bernie-macbookpro-intel, macbook-air/Jacquie denylist).
#
# Usage:  bash ~/.agents/scripts/fleet_ssh_mesh.sh [--verify-only]
set -u

TS_SUFFIX="tail164f4e.ts.net"
MAC_USER="bernhardbudiono"
LINUX_USER="bernhard-budiono"
FLEET_MACS=(bernie-macbookpro-m4 bernie-mac-studio-11119 bernie-macmini-m4 bernie-macmini-m4-02)
HERMES_HOST="bernie-macmini-m4"
LINUX_SERVERS=(ai-server-01 ai-server-02 ai-server-03 ai-server-05 ai-server-06)  # s04 drained (hw fault)
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new)
SELF="$(hostname -s | tr '[:upper:]' '[:lower:]')"
TMP="$(mktemp -d /tmp/fleet_ssh_mesh.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
FAIL=0

say() { printf '%s\n' "$*"; }
run_on() {  # run_on <mac-host> <cmd...>
  local h="$1"; shift
  if [ "$h" = "$SELF" ] || [ "$h" = "bernie-macbookpro-m4" -a "$SELF" = "bernie-macbookpro-m4" ]; then
    bash -c "$*"
  else
    command ssh "${SSH_OPTS[@]}" "$MAC_USER@$h.$TS_SUFFIX" "$*"
  fi
}

VERIFY_ONLY=0
[ "${1:-}" = "--verify-only" ] && VERIFY_ONLY=1

if [ "$VERIFY_ONLY" -eq 0 ]; then
  say "== 1/4 ensure keys + collect pubkeys =="
  for h in "${FLEET_MACS[@]}"; do
    run_on "$h" 'test -f ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -q; cat ~/.ssh/id_ed25519.pub' \
      > "$TMP/$h.pub" 2>/dev/null
    if [ -s "$TMP/$h.pub" ]; then say "  key OK: $h"; else say "  !! could not reach $h (skipping its key)"; FAIL=1; fi
  done
  cat "$TMP"/*.pub > "$TMP/union.pub" 2>/dev/null

  say "== 2/4 distribute union to every fleet Mac =="
  for h in "${FLEET_MACS[@]}"; do
    run_on "$h" 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && cat >> ~/.ssh/authorized_keys.mesh_in && awk "!seen[\$1\" \"\$2]++" ~/.ssh/authorized_keys ~/.ssh/authorized_keys.mesh_in > ~/.ssh/authorized_keys.new && mv ~/.ssh/authorized_keys.new ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && rm -f ~/.ssh/authorized_keys.mesh_in' \
      < "$TMP/union.pub" 2>/dev/null && say "  authorized_keys updated: $h" || { say "  !! failed updating $h"; FAIL=1; }
  done

  say "== 3/4 MagicDNS resolver fix (homebrew tailscaled Macs) =="
  for h in "${FLEET_MACS[@]}"; do
    run_on "$h" '
      if ! grep -rqs 100.100.100.100 /etc/resolver/ts.net 2>/dev/null; then
        if dscacheutil -q host -a name hello.ts.net >/dev/null 2>&1; then
          echo "  resolver OK (app variant): '"$h"'"
        elif sudo -n true 2>/dev/null; then
          printf "nameserver 100.100.100.100\n" | sudo tee /etc/resolver/ts.net >/dev/null
          sudo dscacheutil -flushcache 2>/dev/null
          echo "  resolver INSTALLED: '"$h"'"
        else
          echo "  !! '"$h"': ts.net resolution broken and no passwordless sudo — run: printf \"nameserver 100.100.100.100\\n\" | sudo tee /etc/resolver/ts.net"
        fi
      else
        echo "  resolver file present: '"$h"'"
      fi' 2>/dev/null || { say "  !! resolver check failed on $h"; FAIL=1; }
  done

  say "== 4/4 Hermes host -> Linux AI servers =="
  HERMES_PUB="$(cat "$TMP/$HERMES_HOST.pub" 2>/dev/null)"
  if [ -n "$HERMES_PUB" ]; then
    for s in "${LINUX_SERVERS[@]}"; do
      if run_on "$HERMES_HOST" "command ssh ${SSH_OPTS[*]} $LINUX_USER@$s.$TS_SUFFIX 'echo ok' >/dev/null 2>&1"; then
        say "  already OK: hermes -> $s"
      else
        # push hermes key via THIS host's (assumed-working) access to the server
        printf '%s\n' "$HERMES_PUB" | command ssh "${SSH_OPTS[@]}" "$LINUX_USER@$s.$TS_SUFFIX" \
          'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && sort -u -o ~/.ssh/authorized_keys ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys' \
          2>/dev/null && say "  key pushed: hermes -> $s" || { say "  !! could not seed $s (no path in)"; FAIL=1; }
      fi
    done
  else
    say "  !! no hermes pubkey collected"; FAIL=1
  fi
fi

say "== verification matrix =="
for src in "${FLEET_MACS[@]}"; do
  for dst in "${FLEET_MACS[@]}"; do
    [ "$src" = "$dst" ] && continue
    if run_on "$src" "command ssh ${SSH_OPTS[*]} $MAC_USER@$dst.$TS_SUFFIX 'echo ok' >/dev/null 2>&1"; then
      say "  OK   $src -> $dst"
    else
      say "  FAIL $src -> $dst"; FAIL=1
    fi
  done
done
for s in "${LINUX_SERVERS[@]}"; do
  if run_on "$HERMES_HOST" "command ssh ${SSH_OPTS[*]} $LINUX_USER@$s.$TS_SUFFIX 'echo ok' >/dev/null 2>&1"; then
    say "  OK   hermes($HERMES_HOST) -> $s"
  else
    say "  FAIL hermes($HERMES_HOST) -> $s"; FAIL=1
  fi
done

say ""
if [ "$FAIL" -eq 0 ]; then say "MESH HEALTHY — all expected edges passwordless."; else say "MESH INCOMPLETE — see FAIL/!! lines above; re-run after fixing."; fi
exit "$FAIL"
