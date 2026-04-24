"""Patch the UPTIME line in assets/hero-next.svg to reflect today's value.

The hero SVG is otherwise static — we only replace the text between the
<!-- gen_hero_uptime:start --> and <!-- gen_hero_uptime:end --> markers so
the "Ny Md · developing since YYYY" counter stays current across
workflow-driven regenerations.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "scripts" / "data" / "content.yml"
HERO = ROOT / "assets" / "hero-next.svg"

START_MARKER = "<!-- gen_hero_uptime:start -->"
END_MARKER   = "<!-- gen_hero_uptime:end -->"


def _uptime(start: _dt.date, today: _dt.date) -> tuple[int, int]:
    """Return (years, days) between start and today, floored."""
    years = today.year - start.year
    anniversary = _dt.date(today.year, start.month, start.day)
    if today < anniversary:
        years -= 1
        anniversary = _dt.date(today.year - 1, start.month, start.day)
    days = (today - anniversary).days
    return years, days


def generate(out_dir: Path) -> Path:
    # out_dir is accepted for parity with the other generators but ignored —
    # we always patch the canonical assets/hero-next.svg in place.
    _ = out_dir

    with open(DATA, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
    hero_cfg = content.get("hero", {})
    start_str = hero_cfg.get("developing_since", "2017-01-01")
    label = hero_cfg.get("uptime_label", f"developing since {start_str[:4]}")

    start = _dt.date.fromisoformat(start_str)
    today = _dt.datetime.utcnow().date()
    years, days = _uptime(start, today)

    new_text = (
        f'<text x="170" y="192" fill="#E8DCC4">{years}y {days}d '
        f'<tspan fill="#A89968">· {label}</tspan></text>'
    )

    svg = HERO.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n    {new_text}\n    {END_MARKER}"
    if not pattern.search(svg):
        raise RuntimeError(
            "hero-next.svg is missing the gen_hero_uptime markers; "
            "cannot patch uptime."
        )

    svg = pattern.sub(replacement, svg)
    HERO.write_text(svg, encoding="utf-8")
    return HERO


if __name__ == "__main__":
    print(generate(ROOT / "assets"))
