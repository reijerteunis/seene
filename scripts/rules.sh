#!/usr/bin/env bash
# The one definition of what running the rule set means.
#
# SEEN-114. The pre-commit hook calls `staged`, CI calls `tree` and `fixtures`,
# and all three are here rather than restated in the hook and in the workflow,
# because SEEN-097 recorded what happens when the same environment has two
# definitions: they drift, and the one nobody runs locally is the one that fails.
#
# A tool runs only when its configuration is in the tree, so the set grows by
# adding a configuration and never by editing this file. That is deliberately
# forgiving, and what stops it being a hole is `harness rules --check`: the
# registry carries a rule for everything that runs, and a rule whose
# configuration has gone fails the build from the other side.
#
#   staged    Biome, ast-grep and dependency-cruiser over the staged paths.
#             Under ten seconds is the budget the ticket sets, and the script
#             prints what it took so the budget is measured and not assumed.
#   tree      the same tools over the whole tree, plus knip, which cannot be
#             asked about a staged file: a dead export is a property of the
#             whole import graph.
#   fixtures  `harness rules --fixtures`, which runs each rule against the
#             fixture it stands on and refuses one that does not fire.
set -euo pipefail

cd "$(dirname "$0")/.."

mode="${1:-tree}"
bin=node_modules/.bin
failed=0

started() { printf '==> %s\n' "$1"; }

timed() {
  local label="$1"
  shift
  local start
  start=$(date +%s)
  if "$@"; then
    printf '    %s: ok in %ss\n' "$label" "$(( $(date +%s) - start ))"
  else
    printf '    %s: FAILED in %ss\n' "$label" "$(( $(date +%s) - start ))"
    failed=1
  fi
}

# Every path git has staged for this commit, added through renamed, which is the
# set the hook is about. Deleted paths are left out: a rule cannot be run over a
# file that is gone, and running it over the version still in the index would
# report a violation the commit removes.
staged_paths() {
  git diff --cached --name-only --diff-filter=ACMR
}

keep() {
  grep -E "$1" || true
}

run_staged() {
  local all code_paths
  all=$(staged_paths)
  if [ -z "$all" ]; then
    echo "Nothing is staged, so there is nothing to check."
    return 0
  fi

  # Biome and ast-grep read source files; dependency-cruiser reads the modules
  # they import. All three are handed only the staged paths, which is the whole
  # reason the hook fits in the budget.
  code_paths=$(printf '%s\n' "$all" | keep '\.(ts|tsx|js|jsx|mts|cts|mjs|cjs|json)$')

  if [ -n "$code_paths" ] && [ -f biome.json ]; then
    started "Biome on the staged files"
    # shellcheck disable=SC2086
    timed biome "$bin/biome" check --no-errors-on-unmatched $code_paths
  fi

  local module_paths
  module_paths=$(printf '%s\n' "$all" | keep '\.(ts|tsx|js|jsx|mts|cts|mjs|cjs)$')

  if [ -n "$module_paths" ] && [ -f sgconfig.yml ]; then
    started "ast-grep on the staged files"
    # shellcheck disable=SC2086
    timed ast-grep "$bin/ast-grep" scan $module_paths
  fi

  if [ -n "$module_paths" ] && [ -f .dependency-cruiser.json ]; then
    started "dependency-cruiser on the staged files"
    # shellcheck disable=SC2086
    timed dependency-cruiser "$bin/depcruise" --config .dependency-cruiser.json \
      --output-type err --no-progress $module_paths
  fi
  return 0
}

run_tree() {
  if [ -f biome.json ]; then
    started "Biome on the tree"
    timed biome "$bin/biome" check .
  fi
  if [ -f sgconfig.yml ]; then
    started "ast-grep on the tree"
    timed ast-grep "$bin/ast-grep" scan
  fi
  if [ -f .dependency-cruiser.json ]; then
    started "dependency-cruiser on the tree"
    timed dependency-cruiser "$bin/depcruise" --config .dependency-cruiser.json \
      --output-type err --no-progress apps packages
  fi
  if [ -f knip.json ]; then
    started "knip on the tree"
    timed knip "$bin/knip"
  fi
  return 0
}

case "$mode" in
  staged) run_staged ;;
  tree) run_tree ;;
  fixtures)
    started "Every rule against the fixture it stands on"
    timed fixtures python3 harness/run.py rules --fixtures
    ;;
  *)
    echo "Usage: scripts/rules.sh [staged|tree|fixtures]" >&2
    exit 2
    ;;
esac

if [ "$failed" -ne 0 ]; then
  echo "The rule set refused this change. Every rule says what it stands on in rules/registry.toml." >&2
  exit 1
fi
