from __future__ import annotations

import datetime as _dt
import json
import os
import re
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as _x

import _github
from gen_repos import LANG_COLORS

USER = os.environ.get("LORDWARE_GH_USER", "lordware")

BG       = "#1A1814"
SUB_BG   = "#221E18"
INK      = "#E8DCC4"
DIM      = "#A89968"
GRID     = "#3A352C"
GREEN    = "#4FD97F"
AMBER    = "#FFB83D"
PURPLE   = "#B77FFF"
HOT      = "#FF5C3A"
FONT     = "'IBM Plex Mono', Menlo, Consolas, monospace"

W, H = 960, 320
HEADER_H = 32
FOOTER_H = 22
TOP_N = 8

LABEL_W = 120
SUFFIX_W = 150
BAR_LEFT = LABEL_W + 16
BAR_RIGHT = W - SUFFIX_W - 16
BAR_W = BAR_RIGHT - BAR_LEFT


def _now_utc() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _fmt_bytes(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1e9:5.2f} GB"
    if n >= 1_000_000:
        return f"{n / 1e6:5.2f} MB"
    if n >= 1000:
        return f"{n / 1e3:5.1f} KB"
    return f"{n:5d}  B"


def _fetch_lang_totals() -> dict[str, int]:
    repos = _github.get_paged(f"users/{USER}/repos", sort="updated", per_page=100, max_pages=3)
    totals: dict[str, int] = {}
    seen = 0
    for r in repos:
        if r.get("fork") or r.get("private") or r.get("archived"):
            continue
        full = r.get("full_name")
        if not full:
            continue
        try:
            data = _github.get(f"repos/{full}/languages")
        except _github.GitHubError:
            continue
        if not isinstance(data, dict):
            continue
        for lang, bytes_ in data.items():
            try:
                totals[lang] = totals.get(lang, 0) + int(bytes_)
            except (TypeError, ValueError):
                continue
        seen += 1
        if seen >= 30:
            break
    return totals


def _load_cache(path: Path) -> dict[str, int] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    m = re.search(r'<metadata id="lang-cache">(\{.*?\})</metadata>', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _render(totals: dict[str, int], generated_at: _dt.datetime) -> str:
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    grand = sum(v for _, v in items) or 1
    items = items[:TOP_N]

    rows: list[str] = []
    row_top = HEADER_H + 18
    row_h = (H - HEADER_H - FOOTER_H - 28) // max(TOP_N, 1)
    bar_h = max(8, row_h - 12)

    for i, (lang, bytes_) in enumerate(items):
        y = row_top + i * row_h
        baseline = y + bar_h
        pct = 100.0 * bytes_ / grand
        col = LANG_COLORS.get(lang, PURPLE)
        bar_fill_w = max(2, int(BAR_W * (bytes_ / max(items[0][1], 1))))

        rows.append(
            f'<text x="12" y="{baseline - 1}" class="l-label">{_x(lang[:14]):<14}</text>'
        )
        rows.append(
            f'<rect x="{BAR_LEFT}" y="{y}" width="{BAR_W}" height="{bar_h}" '
            f'fill="{SUB_BG}" stroke="{GRID}"/>'
        )
        rows.append(
            f'<rect x="{BAR_LEFT}" y="{y}" width="0" height="{bar_h}" fill="{col}">'
            f'<animate attributeName="width" from="0" to="{bar_fill_w}" '
            f'begin="{0.15 * i:.2f}s" dur="0.85s" fill="freeze" calcMode="spline" '
            f'keySplines="0.25 0.1 0.25 1"/>'
            f'</rect>'
        )
        ticks: list[str] = []
        for t in range(1, 10):
            tx = BAR_LEFT + int(BAR_W * t / 10.0)
            ticks.append(
                f'<line x1="{tx}" y1="{y}" x2="{tx}" y2="{y + bar_h}" stroke="{GRID}" stroke-width="1"/>'
            )
        rows.append("".join(ticks))
        rows.append(
            f'<text x="{BAR_RIGHT + 12}" y="{baseline - 1}" class="l-bytes">{_x(_fmt_bytes(bytes_))}</text>'
        )
        rows.append(
            f'<text x="{W - 56}" y="{baseline - 1}" class="l-pct">{pct:5.1f}%</text>'
        )

    if not items:
        rows.append(
            f'<text x="12" y="{row_top + 20}" class="l-label" fill="{DIM}">'
            f'no language data — API unreachable or no public repos</text>'
        )

    cache_blob = json.dumps(totals, separators=(",", ":"))
    when = generated_at.strftime("%Y-%m-%d %H:%M:%SZ")
    grand_str = _fmt_bytes(grand) if grand > 1 else "0  B"
    n_repos = len(totals)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="lordware language byte distribution">
  <defs>
    <style>
      .l-bg     {{ fill: {BG}; }}
      .l-subbg  {{ fill: {SUB_BG}; }}
      .l-border {{ fill: none; stroke: {GRID}; stroke-width: 1; }}
      .l-title  {{ font-family: {FONT}; font-size: 14px; fill: {AMBER}; font-weight: 700; letter-spacing: 1px; }}
      .l-sub    {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
      .l-label  {{ font-family: {FONT}; font-size: 12px; fill: {INK}; font-weight: 700; }}
      .l-bytes  {{ font-family: {FONT}; font-size: 11px; fill: {INK}; }}
      .l-pct    {{ font-family: {FONT}; font-size: 11px; fill: {AMBER}; font-weight: 700; }}
      .l-foot   {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
    </style>
  </defs>
  <metadata id="lang-cache">{cache_blob}</metadata>

  <rect class="l-bg" width="{W}" height="{H}"/>
  <rect class="l-border" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"/>

  <rect class="l-subbg" x="0" y="0" width="{W}" height="{HEADER_H}"/>
  <line x1="0" y1="{HEADER_H}" x2="{W}" y2="{HEADER_H}" stroke="{GRID}" stroke-width="1"/>
  <text class="l-title" x="12" y="20">LANGUAGE LOAD METER</text>
  <text class="l-sub"   x="220" y="20">/sys/class/lang/* · top {TOP_N} of {len(totals)} known</text>
  <text class="l-sub"   x="{W - 220}" y="20">total {_x(grand_str.strip())} · sampled {n_repos} keys</text>

  <text x="12" y="{HEADER_H + 14}" class="l-sub">name           usage         (filled = relative to leader)               bytes        %</text>

  {"".join(rows)}

  <line x1="0" y1="{H - FOOTER_H}" x2="{W}" y2="{H - FOOTER_H}" stroke="{GRID}" stroke-width="1"/>
  <rect class="l-subbg" x="0" y="{H - FOOTER_H}" width="{W}" height="{FOOTER_H}"/>
  <circle cx="14" cy="{H - 10}" r="3" fill="{GREEN}">
    <animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite"/>
  </circle>
  <text class="l-foot" x="24" y="{H - 7}">sampled {when} · refresh */6h via gh-actions</text>
  <text class="l-foot" x="{W - 110}" y="{H - 7}">[q]uit  [r]efresh</text>
</svg>
'''
    return svg


def generate(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lang.svg"

    try:
        totals = _fetch_lang_totals()
        if not totals:
            raise _github.GitHubError("no language data returned")
    except _github.GitHubError as e:
        cache = _load_cache(out_path)
        if cache is None:
            print(f"[gen_lang] API failed and no cache: {e}; rendering empty meter")
            totals = {}
        else:
            print(f"[gen_lang] API failed ({e}); using cached language totals")
            totals = cache

    svg = _render(totals, _now_utc())
    out_path.write_text(svg, encoding="utf-8", newline="\n")
    return out_path


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    print(generate(ROOT / "assets"))
