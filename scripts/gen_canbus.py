"""Generate assets/can-bus.svg — a CANopen frame monitor that scrolls upward.

Deterministic per UTC day. SMIL-based motion.
Includes an ASCII-column easter egg: a few consecutive frames carry bytes
that decode to content.canbus.easter_egg.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import random
from pathlib import Path
from xml.sax.saxutils import escape as _x

import yaml

BG      = "#1A1814"
SUB_BG  = "#221E18"
ROW_ALT = "#2A251E"
INK     = "#E8DCC4"
DIM     = "#A89968"
GRID    = "#3A352C"
GREEN   = "#4FD97F"
AMBER   = "#FFB83D"
BLUE    = "#4FC3FF"
RED     = "#FF5C3A"
FONT    = "'IBM Plex Mono', Menlo, Consolas, monospace"

W, H = 960, 200
HEADER_H = 24
FOOTER_H = 20
ROW_H = 13  # 10 rows visible in the (40..180)=140 area; we use 12 rows x ~11.5px but 13px is readable

# Columns (x positions)
COL_NUM  = 12
COL_TS   = 44
COL_ID   = 150
COL_TYPE = 210
COL_LEN  = 290
COL_DATA = 326
COL_ASCII= 690
COL_NODE = 820

VISIBLE_ROWS = 10
TOTAL_FRAMES = 24


def _seed_for_today() -> random.Random:
    date_str = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    digest = hashlib.sha256(date_str.encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _load_content() -> dict:
    here = Path(__file__).resolve().parent
    with open(here / "data" / "content.yml", "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _ascii_render(data: bytes) -> str:
    out = []
    for b in data:
        if 0x20 <= b < 0x7F:
            ch = chr(b)
            if ch in ("<", ">", "&"):
                ch = "."
            out.append(ch)
        else:
            out.append("·")
    return "".join(out)


def _type_color(t: str) -> str:
    if t.startswith("PDO"):
        return GREEN if "Tx" in t else BLUE
    if t.startswith("SDO"):
        return AMBER
    if t == "HB":
        return RED
    if t == "SYNC":
        return BLUE
    if t == "NMT":
        return "#B77FFF"
    return INK


def _build_frames(rng: random.Random, content: dict) -> list[dict]:
    ids = content["canbus"]["ids"]
    nodes = content["canbus"]["nodes"]
    easter = content["canbus"]["easter_egg"].encode("ascii", errors="replace")

    # Base timestamp random within the day
    start_ms = rng.randint(0, 23 * 3600 * 1000)
    t = start_ms

    # Pick 4 consecutive frame indices to carry the easter-egg bytes (8 bytes each, len=len of chunk).
    egg_chunks: list[bytes] = []
    i = 0
    while i < len(easter):
        chunk = easter[i:i + 8]
        egg_chunks.append(chunk)
        i += 8
    # Place them starting at some offset so they scroll through view.
    egg_start = rng.randint(4, max(4, TOTAL_FRAMES - len(egg_chunks) - 4))

    frames: list[dict] = []
    for n in range(TOTAL_FRAMES):
        dt_ms = rng.randint(10, 100)
        t += dt_ms
        hh = (t // 3600000) % 24
        mm = (t // 60000) % 60
        ss = (t // 1000) % 60
        ms = t % 1000
        ts = f"{hh:02d}:{mm:02d}:{ss:02d}.{ms:03d}"

        # Choose ID/type
        id_choice = rng.choice(ids)
        id_hex, msg_type = id_choice["id"], id_choice["type"]
        node = rng.choice(nodes)

        # Is this an easter-egg carrier?
        egg_idx = n - egg_start
        if 0 <= egg_idx < len(egg_chunks):
            data = bytes(egg_chunks[egg_idx])
            if len(data) < 8:
                # pad to at least some length; keep as-is length (CAN len = actual)
                length = len(data)
            else:
                length = 8
            # Prefer PDO-Tx for textual payloads
            id_hex, msg_type = "0x181", "PDO1-Tx"
        else:
            length = rng.randint(1, 8)
            data = bytes(rng.randint(0, 255) for _ in range(length))

        frames.append({
            "n": n + 1,
            "ts": ts,
            "id": id_hex,
            "type": msg_type,
            "len": length,
            "data": data,
            "ascii": _ascii_render(data),
            "node": node,
        })
    return frames


def _render_row(frame: dict, y: int, stripe: bool) -> str:
    data_hex = " ".join(f"{b:02X}" for b in frame["data"])
    tc = _type_color(frame["type"])
    ascii_text = frame["ascii"]
    parts: list[str] = []
    if stripe:
        parts.append(f'<rect x="0" y="{y - ROW_H + 3}" width="{W}" height="{ROW_H}" fill="{ROW_ALT}"/>')
    parts.append(f'<text x="{COL_NUM}"  y="{y}" class="c-dim">{frame["n"]:03d}</text>')
    parts.append(f'<text x="{COL_TS}"   y="{y}" class="c-ink">{_x(frame["ts"])}</text>')
    parts.append(f'<text x="{COL_ID}"   y="{y}" class="c-id">{_x(frame["id"])}</text>')
    parts.append(f'<text x="{COL_TYPE}" y="{y}" fill="{tc}" class="c-type">{_x(frame["type"])}</text>')
    parts.append(f'<text x="{COL_LEN}"  y="{y}" class="c-dim">{frame["len"]}</text>')
    parts.append(f'<text x="{COL_DATA}" y="{y}" class="c-ink">{_x(data_hex)}</text>')
    parts.append(f'<text x="{COL_ASCII}" y="{y}" class="c-ascii">{_x(ascii_text)}</text>')
    parts.append(f'<text x="{COL_NODE}" y="{y}" class="c-dim">{_x(frame["node"])}</text>')
    return "".join(parts)


def generate(out_dir: str | os.PathLike = "assets") -> str:
    content = _load_content()
    rng = _seed_for_today()
    frames = _build_frames(rng, content)

    # Rows are drawn stacked; the visible window is HEADER_H..(H-FOOTER_H) = 24..180 = 156px tall.
    # With ROW_H=13 and visible=10 rows we show ~130px; rest is padding.
    row_strip_height = TOTAL_FRAMES * ROW_H
    rows_nodes: list[str] = []
    for i, fr in enumerate(frames):
        y = ROW_H * (i + 1)  # baseline
        rows_nodes.append(_render_row(fr, y, stripe=(i % 2 == 1)))
    strip_inner = "\n      ".join(rows_nodes)

    dur = 22  # seconds for one full loop

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="CANopen live frame monitor">
  <defs>
    <style>
      .c-bg    {{ fill: {BG}; }}
      .c-subbg {{ fill: {SUB_BG}; }}
      .c-border{{ fill: none; stroke: {GRID}; stroke-width: 1; }}
      .c-head  {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; font-weight: 700; }}
      .c-ink   {{ font-family: {FONT}; font-size: 11px; fill: {INK}; }}
      .c-dim   {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
      .c-id    {{ font-family: {FONT}; font-size: 11px; fill: {AMBER}; font-weight: 700; }}
      .c-type  {{ font-family: {FONT}; font-size: 11px; font-weight: 700; }}
      .c-ascii {{ font-family: {FONT}; font-size: 11px; fill: {GREEN}; }}
      .c-foot  {{ font-family: {FONT}; font-size: 11px; fill: {INK}; }}
      .c-foot-dim {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
    </style>
    <clipPath id="c-clip">
      <rect x="0" y="{HEADER_H}" width="{W}" height="{H - HEADER_H - FOOTER_H}"/>
    </clipPath>
  </defs>

  <rect class="c-bg" width="{W}" height="{H}"/>
  <rect class="c-border" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"/>

  <!-- header row -->
  <rect class="c-subbg" x="0" y="0" width="{W}" height="{HEADER_H}"/>
  <line x1="0" y1="{HEADER_H}" x2="{W}" y2="{HEADER_H}" stroke="{GRID}" stroke-width="1"/>
  <text class="c-head" x="{COL_NUM}"   y="16">#</text>
  <text class="c-head" x="{COL_TS}"    y="16">timestamp</text>
  <text class="c-head" x="{COL_ID}"    y="16">id</text>
  <text class="c-head" x="{COL_TYPE}"  y="16">type</text>
  <text class="c-head" x="{COL_LEN}"   y="16">len</text>
  <text class="c-head" x="{COL_DATA}"  y="16">data</text>
  <text class="c-head" x="{COL_ASCII}" y="16">ascii</text>
  <text class="c-head" x="{COL_NODE}"  y="16">node</text>

  <!-- scrolling rows -->
  <g clip-path="url(#c-clip)">
    <g transform="translate(0 {HEADER_H})">
      <animateTransform attributeName="transform" type="translate" from="0 {HEADER_H}" to="0 {HEADER_H - row_strip_height}" dur="{dur}s" repeatCount="indefinite"/>
      <g>
      {strip_inner}
      </g>
      <g transform="translate(0 {row_strip_height})">
      {strip_inner}
      </g>
    </g>
  </g>

  <!-- footer -->
  <line x1="0" y1="{H - FOOTER_H}" x2="{W}" y2="{H - FOOTER_H}" stroke="{GRID}" stroke-width="1"/>
  <rect class="c-subbg" x="0" y="{H - FOOTER_H}" width="{W}" height="{FOOTER_H}"/>
  <text class="c-foot-dim" x="12" y="{H - 6}">CAN 2.0B · 500 kb/s · load 18% · err 0/0 · node 0x1A @ <tspan fill="{GREEN}">OPERATIONAL</tspan> · LIVE</text>
  <circle cx="{W - 90}" cy="{H - 10}" r="3" fill="{RED}">
    <animate attributeName="r" values="3;5;3" dur="1s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0.4;1" dur="1s" repeatCount="indefinite"/>
  </circle>
  <text class="c-foot" x="{W - 78}" y="{H - 6}">10ms</text>
  <text class="c-foot-dim" x="{W - 40}" y="{H - 6}">HB</text>
</svg>
'''

    out_path = Path(out_dir) / "can-bus.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8", newline="\n")
    return str(out_path)


if __name__ == "__main__":
    p = generate()
    print(f"wrote {p}")
