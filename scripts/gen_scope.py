"""Generate assets/scope.svg — RS-232 oscilloscope trace.

Encodes a UART transmission as a digital square wave, scrolls right-to-left.
Each character = start(0) + 8 data bits (LSB-first) + stop(1) = 10 bits.
Deterministic per UTC day.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import random
from pathlib import Path
from xml.sax.saxutils import escape as _x

import yaml

BG      = "#050808"
INK     = "#4FD97F"   # scope green
DIM     = "#2F5F3E"
GRID_C  = "#123C20"
LABEL   = "#9FD9AC"
AMBER   = "#FFB83D"
RED     = "#FF5C3A"
FONT    = "'IBM Plex Mono', Menlo, Consolas, monospace"

W, H = 960, 180

BIT_WIDTH = 18   # px per bit on screen
HIGH_Y = 70      # y for '1' level
LOW_Y  = 120     # y for '0' level
ASCII_Y = 155    # where decoded ASCII column prints


def _seed_for_today() -> random.Random:
    date_str = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    digest = hashlib.sha256(date_str.encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _load_content() -> dict:
    here = Path(__file__).resolve().parent
    with open(here / "data" / "content.yml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _uart_bits(msg: str) -> list[tuple[int, str]]:
    """Return [(bit, tag), ...] for the full message. tag='start'/'data'/'stop'/'idle'."""
    bits: list[tuple[int, str]] = []
    # small idle before first char
    bits.extend([(1, "idle")] * 2)
    for ch in msg:
        b = ord(ch) & 0xFF
        bits.append((0, "start"))
        for i in range(8):
            bits.append(((b >> i) & 1, "data"))
        bits.append((1, "stop"))
        # small idle between chars
        bits.append((1, "idle"))
    bits.extend([(1, "idle")] * 2)
    return bits


def _trace_path(bits: list[tuple[int, str]]) -> str:
    """Build SVG path 'd' for a digital trace."""
    d: list[str] = []
    x = 0
    y = HIGH_Y if bits[0][0] == 1 else LOW_Y
    d.append(f"M {x} {y}")
    for i, (b, _tag) in enumerate(bits):
        new_y = HIGH_Y if b == 1 else LOW_Y
        if new_y != y:
            # vertical edge
            d.append(f"L {x} {new_y}")
            y = new_y
        x += BIT_WIDTH
        d.append(f"L {x} {y}")
    return " ".join(d)


def _ascii_decorations(msg: str) -> list[tuple[int, str]]:
    """X position and character to print beneath each byte."""
    out: list[tuple[int, str]] = []
    # start: first char begins after 2 idle bits
    x = 2 * BIT_WIDTH
    for ch in msg:
        # byte spans start(1) + data(8) + stop(1) = 10 bits, center at x + 5 bits
        center_x = x + 5 * BIT_WIDTH
        display = ch if 0x20 <= ord(ch) < 0x7F else "·"
        out.append((center_x, display))
        x += 10 * BIT_WIDTH + BIT_WIDTH  # char + idle
    return out


def _grid_nodes() -> str:
    lines: list[str] = []
    # vertical dots
    for x in range(0, W + 1, 32):
        for y in range(30, H - 10, 10):
            lines.append(f'<circle cx="{x}" cy="{y}" r="0.6" fill="{GRID_C}"/>')
    # ground reference
    lines.append(f'<line x1="0" y1="{(HIGH_Y + LOW_Y) // 2}" x2="{W}" y2="{(HIGH_Y + LOW_Y) // 2}" stroke="{DIM}" stroke-width="0.5" stroke-dasharray="2 4"/>')
    return "\n    ".join(lines)


def generate(out_dir: str | os.PathLike = "assets") -> str:
    content = _load_content()
    rng = _seed_for_today()
    messages = content["scope"]["messages"]
    msg = rng.choice(messages)

    bits = _uart_bits(msg)
    total_px = len(bits) * BIT_WIDTH
    path_d = _trace_path(bits)

    # Ascii column: we position the decoded char beneath the data nibble in the trace
    ascii_positions = _ascii_decorations(msg)
    ascii_nodes = []
    for cx, ch in ascii_positions:
        ascii_nodes.append(f'<text x="{cx}" y="{ASCII_Y}" fill="{AMBER}" text-anchor="middle" class="s-ascii">{_x(ch)}</text>')
    ascii_inner = "\n      ".join(ascii_nodes)

    dur = 22  # seconds

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="RS-232 oscilloscope trace">
  <defs>
    <style>
      .s-bg      {{ fill: {BG}; }}
      .s-border  {{ fill: none; stroke: #1a3a26; stroke-width: 1; }}
      .s-label   {{ font-family: {FONT}; font-size: 11px; fill: {LABEL}; }}
      .s-rec     {{ font-family: {FONT}; font-size: 11px; fill: {RED}; font-weight: 700; }}
      .s-title   {{ font-family: {FONT}; font-size: 10px; fill: {DIM}; }}
      .s-trace   {{ fill: none; stroke: {INK}; stroke-width: 1.5; stroke-linejoin: miter; }}
      .s-ascii   {{ font-family: {FONT}; font-size: 12px; font-weight: 700; }}
    </style>
    <clipPath id="s-clip">
      <rect x="0" y="25" width="{W}" height="{H - 40}"/>
    </clipPath>
  </defs>

  <rect class="s-bg" width="{W}" height="{H}"/>
  <rect class="s-border" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"/>

  <!-- grid -->
  <g>
    {_grid_nodes()}
  </g>

  <!-- labels -->
  <text class="s-label" x="12" y="16">CH1  TTL 5V</text>
  <text class="s-rec" x="{W - 72}" y="16">&#9679; REC
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
  </text>
  <text class="s-title" x="{W - 72}" y="30">RS-232</text>
  <text class="s-label" x="12" y="{H - 6}">TIME 104us/div  TRIG ^ 2.5V  UART 9600 8N1</text>

  <!-- trace: two copies, outer group scrolls L<-R -->
  <g clip-path="url(#s-clip)">
    <g>
      <animateTransform attributeName="transform" type="translate" from="0 0" to="-{total_px} 0" dur="{dur}s" repeatCount="indefinite"/>
      <g>
        <path class="s-trace" d="{path_d}"/>
        {ascii_inner}
      </g>
      <g transform="translate({total_px} 0)">
        <path class="s-trace" d="{path_d}"/>
        {ascii_inner}
      </g>
    </g>
  </g>
</svg>
'''

    out_path = Path(out_dir) / "scope.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8", newline="\n")
    return str(out_path)


if __name__ == "__main__":
    p = generate()
    print(f"wrote {p}")
