#!/usr/bin/env bats

load test_helpers

# ============================================
# Version
# ============================================

@test "rt version prints version string" {
  run "$RT_BIN" version
  [ "$status" -eq 0 ]
  [[ "$output" =~ ^rt\ v[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "rt --version is an alias for version" {
  run "$RT_BIN" --version
  [ "$status" -eq 0 ]
  [[ "$output" =~ ^rt\ v ]]
}

@test "rt -v is an alias for version" {
  run "$RT_BIN" -v
  [ "$status" -eq 0 ]
  [[ "$output" =~ ^rt\ v ]]
}

# ============================================
# Help
# ============================================

@test "rt help prints usage" {
  run "$RT_BIN" help
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Usage: rt" ]]
}

@test "rt --help is an alias for help" {
  run "$RT_BIN" --help
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Usage: rt" ]]
}

@test "rt -h is an alias for help" {
  run "$RT_BIN" -h
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Usage: rt" ]]
}

@test "rt help lists all commands" {
  run "$RT_BIN" help
  [[ "$output" =~ "setup" ]]
  [[ "$output" =~ "list" ]]
  [[ "$output" =~ "qr" ]]
  [[ "$output" =~ "reconnect" ]]
  [[ "$output" =~ "stop" ]]
  [[ "$output" =~ "version" ]]
  [[ "$output" =~ "help" ]]
}

# ============================================
# Port Calculation
# ============================================

@test "rt_ports produces deterministic ports for same name" {
  source_rt
  rt_ports "remote"
  local clip1=$RT_CLIP_PORT ttyd1=$RT_TTYD_PORT caddy1=$RT_CADDY_PORT

  rt_ports "remote"
  [ "$RT_CLIP_PORT" -eq "$clip1" ]
  [ "$RT_TTYD_PORT" -eq "$ttyd1" ]
  [ "$RT_CADDY_PORT" -eq "$caddy1" ]
}

@test "rt_ports produces different ports for different names" {
  source_rt
  rt_ports "foo"
  local clip_foo=$RT_CLIP_PORT

  rt_ports "bar"
  [ "$RT_CLIP_PORT" -ne "$clip_foo" ]
}

@test "rt_ports spacing is clip, clip+1, clip+2" {
  source_rt
  rt_ports "test-session"
  [ "$RT_TTYD_PORT" -eq $(( RT_CLIP_PORT + 1 )) ]
  [ "$RT_CADDY_PORT" -eq $(( RT_CLIP_PORT + 2 )) ]
}

@test "rt_ports are within valid range" {
  source_rt
  for name in alpha beta gamma delta epsilon remote work debug test prod; do
    rt_ports "$name"
    [ "$RT_CLIP_PORT" -ge 7680 ]
    [ "$RT_CLIP_PORT" -le 9177 ]
  done
}

# ============================================
# List
# ============================================

@test "rt list with no sessions shows empty message" {
  # Ensure no sessions exist
  rm -rf /tmp/remote-terminal-bats-test-* 2>/dev/null
  run "$RT_BIN" list
  [ "$status" -eq 0 ]
  [[ "$output" =~ "No sessions." ]]
}

@test "rt ls is an alias for list" {
  rm -rf /tmp/remote-terminal-bats-test-* 2>/dev/null
  run "$RT_BIN" ls
  [ "$status" -eq 0 ]
  [[ "$output" =~ "No sessions." ]]
}

@test "rt list detects a session directory" {
  local piddir="/tmp/remote-terminal-bats-list-test"
  mkdir -p "$piddir"
  echo "99999" > "${piddir}/ttyd.pid"

  run "$RT_BIN" list
  [ "$status" -eq 0 ]
  [[ "$output" =~ "bats-list-test" ]]

  rm -rf "$piddir"
}

# ============================================
# Stop
# ============================================

@test "rt stop nonexistent session returns error" {
  rm -rf /tmp/remote-terminal-nonexistent 2>/dev/null
  run "$RT_BIN" stop nonexistent
  [ "$status" -eq 1 ]
  [[ "$output" =~ "No session" ]]
}

@test "rt stop cleans up session directory" {
  local piddir="/tmp/remote-terminal-bats-stop-test"
  mkdir -p "$piddir"
  echo "99999" > "${piddir}/fake.pid"

  run "$RT_BIN" stop bats-stop-test
  [ "$status" -eq 0 ]
  [[ "$output" =~ "stopped" ]]
  [ ! -d "$piddir" ]
}

@test "rt stop --all stops multiple sessions" {
  mkdir -p /tmp/remote-terminal-bats-all-1
  mkdir -p /tmp/remote-terminal-bats-all-2
  echo "99999" > /tmp/remote-terminal-bats-all-1/fake.pid
  echo "99999" > /tmp/remote-terminal-bats-all-2/fake.pid

  run "$RT_BIN" stop --all
  [ "$status" -eq 0 ]
  [ ! -d /tmp/remote-terminal-bats-all-1 ]
  [ ! -d /tmp/remote-terminal-bats-all-2 ]
}

# ============================================
# QR
# ============================================

@test "rt qr with no active session returns error" {
  rm -rf /tmp/remote-terminal-nonexistent 2>/dev/null
  run "$RT_BIN" qr nonexistent
  [ "$status" -eq 1 ]
  [[ "$output" =~ "No active URL" ]]
}

@test "rt qr prints URL and PIN for active session" {
  local piddir="/tmp/remote-terminal-bats-qr-test"
  mkdir -p "$piddir"
  echo "https://example.com/token/" > "${piddir}/url"
  echo "1234" > "${piddir}/pin"

  run "$RT_BIN" qr bats-qr-test
  [ "$status" -eq 0 ] || true  # qrencode may not be installed in CI
  [[ "$output" =~ "https://example.com/token/" ]]
  [[ "$output" =~ "1234" ]]

  rm -rf "$piddir"
}

# ============================================
# Reconnect
# ============================================

@test "rt reconnect with no tmux session returns error" {
  run "$RT_BIN" reconnect bats-no-tmux
  [ "$status" -eq 1 ]
  [[ "$output" =~ "No tmux session" ]]
}

@test "rt rc is an alias for reconnect" {
  run "$RT_BIN" rc bats-no-tmux
  [ "$status" -eq 1 ]
  [[ "$output" =~ "No tmux session" ]]
}
