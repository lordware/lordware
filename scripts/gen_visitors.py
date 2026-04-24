"""Generate assets/visitors.svg — a themed LCD-style view counter.

Wraps komarev/github-profile-views-counter: we fetch its SVG, parse the
current count, and re-render it inside our NeXT-computer-aesthetic frame.
Falls back to the last-known count (from the on-disk SVG) if komarev is
unreachable so the page never goes blank.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape as _x

# Palette — matches the rest of the embedded/NeXT aesthetic.
BG       = "#1A1814"
SUB_BG   = "#221E18"
INK      = "#E8DCC4"
DIM      = "#A89968"
GRID     = "#3A352C"
AMBER    = "#FFB83D"
HOT      = "#FF5C3A"
FONT     = "'IBM Plex Mono', Menlo, Consolas, monospace"

W, H = 320, 80
KOMAREV_URL = (
    "https://komarev.com/ghpvc/?username=lordware&label=visitors"
)


def _fetch_count(timeout: float = 6.0) -> int | None:
    """Fetch the current view count from komarev. Returns None on failure."""
    try:
        req = urllib.request.Request(
            KOMAREV_URL,
            headers={"User-Agent": "lordware-readme-regen/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None

    # Komarev embeds the count as `>NNN<` inside <text> tags, duplicated
    # (shadow + main). Any of the matches will be the count.
    matches = re.findall(r">(\d+)<", body)
    for m in matches:
        return int(m)
    return None


def _previous_count(out_path: Path) -> int:
    """Read the count baked into a previously-generated visitors.svg, or 0."""
    if not out_path.exists():
        return 0
    try:
        text = out_path.read_text(encoding="utf-8")
    except Exception:
        return 0
    m = re.search(r'data-count="(\d+)"', text)
    return int(m.group(1)) if m else 0


def render(count: int) -> str:
    """Render the SVG for the given view count."""
    # Format the number with thin spaces for readability past 1k.
    shown = f"{count:,}".replace(",", "\u2009")

    # Right-align the counter glyphs; approx 24px per digit at 36px font.
    digits = len(shown)
    num_x = W - 24 - (digits * 22)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="visitors: {count}" '
        f'data-count="{count}">\n'
        f'  <defs>\n'
        f'    <style>\n'
        f'      .v-bg    {{ fill: {BG}; }}\n'
        f'      .v-panel {{ fill: {SUB_BG}; stroke: {GRID}; stroke-width: 1; }}\n'
        f'      .v-label {{ fill: {DIM}; font-family: {FONT}; font-size: 10px; letter-spacing: 2px; }}\n'
        f'      .v-sub   {{ fill: {DIM}; font-family: {FONT}; font-size: 9px; }}\n'
        f'      .v-count {{ fill: {AMBER}; font-family: {FONT}; font-weight: 700; font-size: 36px; letter-spacing: 1px; }}\n'
        f'      .v-bar   {{ fill: {AMBER}; }}\n'
        f'    </style>\n'
        f'  </defs>\n'
        f'  <rect width="{W}" height="{H}" class="v-bg"/>\n'
        f'  <rect x="6" y="6" width="{W - 12}" height="{H - 12}" rx="4" class="v-panel"/>\n'
        f'  <rect x="6" y="6" width="4" height="{H - 12}" class="v-bar"/>\n'
        f'  <text x="20" y="26" class="v-label">VISITORS</text>\n'
        f'  <text x="20" y="44" class="v-sub">/proc/lordware · hits</text>\n'
        f'  <g>\n'
        f'    <circle cx="22" cy="60" r="2.5" fill="{HOT}">\n'
        f'      <animate attributeName="opacity" values="1;0.25;1" dur="1.4s" repeatCount="indefinite"/>\n'
        f'    </circle>\n'
        f'    <text x="32" y="63" class="v-sub">· live</text>\n'
        f'  </g>\n'
        f'  <text x="{num_x}" y="54" class="v-count">{_x(shown)}</text>\n'
        f'</svg>\n'
    )


def generate(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "visitors.svg"

    fetched = _fetch_count()
    if fetched is not None:
        count = fetched
    else:
        # Komarev unreachable — keep the previous count so the page stays sane.
        count = _previous_count(out_path)

    out_path.write_text(render(count), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    print(generate(ROOT / "assets"))
