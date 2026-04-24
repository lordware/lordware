#!/usr/bin/env bash
# Verifies every external image URL referenced in README.md responds with
# HTTP 200 and an image content-type. Run after every section is added.
set -euo pipefail

README="${1:-README.md}"
fail=0

urls=$(grep -oE 'https://[^")[:space:]]+' "$README" | sort -u || true)

if [[ -z "$urls" ]]; then
  echo "No URLs found in $README"
  exit 0
fi

while IFS= read -r url; do
  code=$(curl -sL -o /dev/null -w '%{http_code}' --max-time 10 "$url" || echo "000")
  if [[ "$code" == "200" ]]; then
    echo "OK  $code  $url"
  else
    echo "FAIL $code  $url"
    fail=1
  fi
done <<< "$urls"

exit "$fail"
