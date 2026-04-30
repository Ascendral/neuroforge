#!/usr/bin/env bash
# NeuroForge pre-commit hook — anti-theater enforcement.
# Install: ln -s ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit
set -euo pipefail

# Block staged content with theater markers unless an explicit justification is present.
# Justification = a comment containing "ANTI-THEATER-OK:" on the same or adjacent line.
staged=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|ts|tsx|js|jsx)$' || true)
if [ -z "$staged" ]; then
  exit 0
fi

bad=0
for f in $staged; do
  if [ ! -f "$f" ]; then continue; fi
  # Look for theater markers
  hits=$(grep -nE '(# *(TODO|FIXME): *hardcoded|# *FAKE|# *MOCK|// *FAKE|// *MOCK|// *TODO: *hardcoded)' "$f" || true)
  if [ -n "$hits" ]; then
    while IFS= read -r line; do
      lineno=$(echo "$line" | cut -d: -f1)
      # check the line itself and the line above for ANTI-THEATER-OK
      ctx=$(sed -n "$((lineno-1)),${lineno}p" "$f")
      if ! echo "$ctx" | grep -q 'ANTI-THEATER-OK:'; then
        echo "BLOCKED: theater marker without justification in $f:$lineno"
        echo "  $line"
        bad=1
      fi
    done <<< "$hits"
  fi
done

if [ "$bad" -ne 0 ]; then
  echo
  echo "Add an 'ANTI-THEATER-OK: <reason>' comment on or above the line, or remove the marker."
  exit 1
fi
exit 0
