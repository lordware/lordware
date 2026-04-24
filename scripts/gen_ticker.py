"""Generate assets/ticker.svg — a horizontal NOW: marquee.

The generator is deterministic for a given UTC day: same day -> same bytes.
Motion uses SMIL so the marquee animates when the SVG is loaded via <img>
through GitHub's camo proxy (CSS @keyframes are unreliable there).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import random
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape as _x

import yaml

# Palette — shared NeXT-computer aesthetic.
BG       = "#1A1814"
SUB_BG   = "#2A251E"
INK      = "#E8DCC4"
DIM      = "#A89968"
GRID     = "#3A352C"
ACCENT_R = "#FF4F4F"
ACCENT_G = "#4FD97F"
FONT     = "'IBM Plex Mono', Menlo, Consolas, monospace"

CAT_COLORS = {
    "shipping":  "#FF5C3A",
    "tinkering": "#FFB83D",
    "learning":  "#4FD97F",
    "reading":   "#4FC3FF",
    "dreaming":  "#B77FFF",
}

W, H = 960, 90
CHAR_W = 8  # approx glyph advance for monospace at 14px — sizing-only


def _seed_for_today() -> random.Random:
    date_str = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    digest = hashlib.sha256(date_str.encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _load_content() -> dict:
    here = Path(__file__).resolve().parent
    with open(here / "data" / "content.yml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _build_items(rng: random.Random, items: list[dict]) -> list[dict]:
    pool = list(items)
    rng.shuffle(pool)
    return pool


def generate(out_dir: str | os.PathLike = "assets") -> str:
    content = _load_content()
    rng = _seed_for_today()
    items = _build_items(rng, content["ticker"])

    # Layout: build one "strip" of all items laid out L->R; duplicate for seamless loop.
    # Each item renders as: [category]  message   ·
    # In approximate pixels.
    x_cursor = 0
    PAD_AFTER_TAG = 12
    PAD_AFTER_MSG = 28
    tag_nodes: list[str] = []
    for it in items:
        cat = it["category"]
        msg = it["message"]
        tag_text = f"[{cat}]"
        color = CAT_COLORS.get(cat, INK)
        tag_w = len(tag_text) * CHAR_W
        msg_w = len(msg) * CHAR_W
        tag_nodes.append(
            f'<text x="{x_cursor}" y="62" class="t-tag" fill="{color}">{_x(tag_text)}</text>'
        )
        x_cursor += tag_w + PAD_AFTER_TAG
        tag_nodes.append(
            f'<text x="{x_cursor}" y="62" class="t-msg">{_x(msg)}</text>'
        )
        x_cursor += msg_w
        tag_nodes.append(
            f'<text x="{x_cursor + 6}" y="62" class="t-sep">·</text>'
        )
        x_cursor += PAD_AFTER_MSG

    strip_width = max(x_cursor, W)
    # Duration proportional to distance so speed stays ~constant no matter the strip length.
    dur = max(12, strip_width // 40)

    strip_inner = "\n      ".join(tag_nodes)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="lordware live ticker">
  <defs>
    <style>
      .t-bg      {{ fill: {BG}; }}
      .t-subbg   {{ fill: {SUB_BG}; }}
      .t-border  {{ fill: none; stroke: {GRID}; stroke-width: 1; }}
      .t-label   {{ font-family: {FONT}; font-size: 13px; font-weight: 700; fill: {INK}; }}
      .t-sub     {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
      .t-tx      {{ font-family: {FONT}; font-size: 11px; fill: {ACCENT_G}; }}
      .t-cursor  {{ font-family: {FONT}; font-size: 14px; fill: {INK}; }}
      .t-tag     {{ font-family: {FONT}; font-size: 14px; font-weight: 700; }}
      .t-msg     {{ font-family: {FONT}; font-size: 14px; fill: {INK}; }}
      .t-sep     {{ font-family: {FONT}; font-size: 14px; fill: {GRID}; }}
    </style>
    <clipPath id="t-clip">
      <rect x="0" y="22" width="{W}" height="{H - 22}"/>
    </clipPath>
  </defs>

  <rect class="t-bg" width="{W}" height="{H}"/>
  <rect class="t-subbg" width="{W}" height="22"/>
  <rect class="t-border" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"/>
  <line x1="0" y1="22" x2="{W}" y2="22" stroke="{GRID}" stroke-width="1"/>

  <!-- top bar -->
  <text class="t-label" x="12" y="15">NOW:</text>
  <text class="t-sub" x="56" y="15">/proc/lordware · live</text>
  <text class="t-tx" x="{W - 120}" y="15">tx {dur}s loop</text>
  <text class="t-cursor" x="{W - 18}" y="17">&#9612;<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></text>

  <!-- marquee: two copies of the strip, outer group translates left -->
  <g clip-path="url(#t-clip)">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-{strip_width} 0" dur="{dur}s" repeatCount="indefinite"/>
      <g>
      {strip_inner}
      </g>
      <g transform="translate({strip_width} 0)">
      {strip_inner}
      </g>
    </g>
  </g>
</svg>
'''

    out_path = Path(out_dir) / "ticker.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8", newline="\n")
    return str(out_path)


if __name__ == "__main__":
    p = generate()
    print(f"wrote {p}")
