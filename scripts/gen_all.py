"""Run all dynamic-SVG generators and write to assets/."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

# Make sibling gen_* modules importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_ticker    # noqa: E402
import gen_canbus    # noqa: E402
import gen_scope     # noqa: E402
import gen_boot      # noqa: E402
import gen_visitors  # noqa: E402


def main() -> int:
    for mod in (gen_ticker, gen_canbus, gen_scope, gen_boot, gen_visitors):
        path = mod.generate(OUT)
        print(f"[gen_all] {mod.__name__} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
