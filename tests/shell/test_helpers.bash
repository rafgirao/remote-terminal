#!/usr/bin/env bash

RT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RT_BIN="${RT_ROOT}/bin/rt"

# Source rt functions without executing main block
source_rt() {
  source "$RT_BIN"
}
