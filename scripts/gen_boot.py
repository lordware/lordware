"""Generate assets/boot.svg — BIOS POST sequence that types itself in.

Deterministic per UTC day. SMIL-based line-by-line fade-in with fill=freeze
so the final state is static (no flicker loop).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import random
from pathlib import Path
from xml.sax.saxutils import escape as _x

import yaml

BG    = "#1A1814"
AMBER = "#FFB83D"
DIM   = "#A89968"
GREEN = "#4FD97F"
RED   = "#FF5C3A"
FONT  = "'IBM Plex Mono', Menlo, Consolas, monospace"

W, H = 960, 260

LINE_H    = 18
FIRST_Y   = 28
OK_COL_X  = 600
TEXT_COL_X = 20

STEP = 0.28  # seconds between line appearances


def _seed_for_today() -> random.Random:
    date_str = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    digest = hashlib.sha256(date_str.encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _load_content() -> dict:
    here = Path(__file__).resolve().parent
    with open(here / "data" / "content.yml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _line(i: int, y: int, left: str, right: str | None = None, right_color: str = GREEN, left_color: str = AMBER) -> str:
    begin = f"{STEP * i:.2f}s"
    parts: list[str] = []
    parts.append(
        f'<text x="{TEXT_COL_X}" y="{y}" opacity="0" font-family="{FONT}" font-size="13" fill="{left_color}">'
        f'{_x(left)}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin}" dur="0.08s" fill="freeze"/>'
        f'</text>'
    )
    if right is not None:
        parts.append(
            f'<text x="{OK_COL_X}" y="{y}" opacity="0" font-family="{FONT}" font-size="13" fill="{right_color}" font-weight="700">'
            f'{_x(right)}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin}" dur="0.08s" fill="freeze"/>'
            f'</text>'
        )
    return "".join(parts)


def generate(out_dir: str | os.PathLike = "assets") -> str:
    content = _load_content()
    rng = _seed_for_today()

    now = _dt.datetime.now(_dt.timezone.utc)
    date_str = now.strftime("%Y-%m-%d %H:%M UTC")
    doy = int(now.strftime("%j"))
    version = f"v2.{doy}.{rng.randint(10, 99):02d}"

    mem_bytes = rng.choice([4096, 8192, 16384, 32768])
    crc32 = f"{rng.randint(0, 0xFFFFFFFF):08X}"
    year = content["boot"].get("copyright_year", 2026)

    header_main = content["boot"].get("header", "LORDWARE BIOS")

    # Build lines (index -> content)
    lines: list[tuple[str, str | None, str]] = []  # (left, right, right_color)
    lines.append((f"{header_main} {version}  (c) {year} · AVR @ 16 MHz · 8K SRAM", None, GREEN))
    sep = "-" * 78
    lines.append((sep, None, DIM))
    lines.append((f"Memory test ......... {mem_bytes:>6d} bytes", "[ OK ]", GREEN))
    lines.append(("Detecting UART0 ..... 9600 8N1", "[ OK ]", GREEN))
    lines.append(("Detecting MCP2515 ... CAN 500 kb/s", "[ OK ]", GREEN))
    lines.append(("Detecting W25Q64 .... 8MB SPI flash", "[ OK ]", GREEN))
    lines.append((f"Firmware image ...... CRC32 {crc32}", "[ OK ]", GREEN))
    lines.append((f"RTC sync ............ {date_str}", "[ OK ]", GREEN))
    lines.append(("Network ............. dark fiber", "[ ?? ]", RED))
    lines.append(("Bringing up /proc/lordware ...", "[ OK ]", GREEN))
    lines.append(("All systems nominal.", None, GREEN))

    nodes: list[str] = []
    for i, (left, right, rcolor) in enumerate(lines):
        y = FIRST_Y + i * LINE_H
        # Make separator and "All systems nominal." dim/green respectively
        if i == 0:
            left_color = AMBER
        elif i == 1:
            left_color = DIM
        elif left.strip().startswith("All systems"):
            left_color = GREEN
        else:
            left_color = AMBER
        nodes.append(_line(i, y, left, right, right_color=rcolor, left_color=left_color))

    # Prompt line at bottom
    prompt_y = FIRST_Y + len(lines) * LINE_H + 8
    prompt_begin = f"{STEP * len(lines):.2f}s"
    nodes.append(
        f'<text x="{TEXT_COL_X}" y="{prompt_y}" opacity="0" font-family="{FONT}" font-size="14" fill="{GREEN}" font-weight="700">&gt;'
        f'<animate attributeName="opacity" from="0" to="1" begin="{prompt_begin}" dur="0.08s" fill="freeze"/>'
        f'</text>'
    )
    nodes.append(
        f'<rect x="{TEXT_COL_X + 14}" y="{prompt_y - 12}" width="9" height="14" fill="{AMBER}" opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{prompt_begin}" dur="0.08s" fill="freeze"/>'
        f'<animate attributeName="opacity" values="1;0;1" dur="1s" begin="{(STEP * len(lines) + 0.3):.2f}s" repeatCount="indefinite"/>'
        f'</rect>'
    )

    inner = "\n  ".join(nodes)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="lordware BIOS POST">
  <defs>
    <style>
      .b-bg     {{ fill: {BG}; }}
      .b-border {{ fill: none; stroke: #3A352C; stroke-width: 1; }}
    </style>
  </defs>
  <rect class="b-bg" width="{W}" height="{H}"/>
  <rect class="b-border" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"/>
  {inner}
</svg>
'''

    out_path = Path(out_dir) / "boot.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8", newline="\n")
    return str(out_path)


if __name__ == "__main__":
    p = generate()
    print(f"wrote {p}")
