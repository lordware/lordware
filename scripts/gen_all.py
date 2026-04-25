from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_ticker
import gen_canbus
import gen_scope
import gen_boot
import gen_visitors
import gen_hero_uptime
import gen_repos
import gen_log
import gen_lang
import gen_stats


def main() -> int:
    mods = (
        gen_ticker, gen_canbus, gen_scope, gen_boot,
        gen_visitors, gen_hero_uptime,
        gen_repos, gen_log, gen_lang, gen_stats,
    )
    failures = 0
    for mod in mods:
        try:
            path = mod.generate(OUT)
            print(f"[gen_all] {mod.__name__} -> {path}")
        except Exception as e:
            print(f"[gen_all] {mod.__name__} FAILED: {e}")
            failures += 1
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
