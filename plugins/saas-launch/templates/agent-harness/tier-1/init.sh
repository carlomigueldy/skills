#!/usr/bin/env bash
# {{PRODUCT_NAME}} — single entry point for every build agent's install/verify/test/start.
# AGENTS.md's Commands section delegates here — never hand-roll these commands
# elsewhere; if the command needs to change, change it here so every agent
# (Claude or otherwise) picks it up the same way.
set -euo pipefail

INSTALL_CMD="pnpm install"
VERIFY_CMD="pnpm turbo run lint typecheck build"
TEST_CMD="pnpm turbo run test"
START_CMD="pnpm dev"

usage() {
  cat <<EOF
Usage: ./init.sh <command>

Commands:
  install   $INSTALL_CMD
  verify    $VERIFY_CMD
  test      $TEST_CMD
  start     $START_CMD
EOF
}

case "${1:-}" in
  install)
    exec $INSTALL_CMD
    ;;
  verify)
    exec $VERIFY_CMD
    ;;
  test)
    exec $TEST_CMD
    ;;
  start)
    exec $START_CMD
    ;;
  *)
    usage
    exit 1
    ;;
esac
