from __future__ import annotations

import datetime as _dt
import json
import os
import re
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as _x

import _github

USER = os.environ.get("LORDWARE_GH_USER", "lordware")

BG       = "#1A1814"
SUB_BG   = "#221E18"
ROW_ALT  = "#2A251E"
HILITE   = "#3A311F"
INK      = "#E8DCC4"
DIM      = "#A89968"
GRID     = "#3A352C"
GREEN    = "#4FD97F"
AMBER    = "#FFB83D"
BLUE     = "#4FC3FF"
HOT      = "#FF5C3A"
PURPLE   = "#B77FFF"
FONT     = "'IBM Plex Mono', Menlo, Consolas, monospace"

LANG_COLORS = {
    "C":            "#A8B9CC",
    "C++":          "#F34B7D",
    "C#":           "#9B7CB6",
    "Python":       "#FFD145",
    "Rust":         "#DEA584",
    "Go":           "#00ADD8",
    "JavaScript":   "#F1E05A",
    "TypeScript":   "#4FC3FF",
    "Shell":        "#89E051",
    "HTML":         "#E34C26",
    "CSS":          "#563D7C",
    "Java":         "#B07219",
    "Kotlin":       "#A97BFF",
    "Swift":        "#FA7343",
    "Ruby":         "#701516",
    "PHP":          "#777BB4",
    "Lua":          "#000080",
    "Verilog":      "#B2B7F8",
    "VHDL":         "#ADB2CB",
    "Assembly":     "#6E4C13",
    "Makefile":     "#427819",
    "CMake":        "#DA3434",
    "Dockerfile":   "#384D54",
    "Vim Script":   "#199F4B",
    "Jupyter Notebook": "#DA5B0B",
}

W, H = 960, 360
LINE_H = 14
HEADER_LINES = 5
HEADER_TOP = 18
COL_HDR_Y = HEADER_LINES * LINE_H + HEADER_TOP + 6
ROW_TOP = COL_HDR_Y + 8
VISIBLE_ROWS = 12
ROW_H = 16

COL_PID    = 12
COL_USER   = 70
COL_PR     = 150
COL_NI     = 180
COL_VIRT   = 215
COL_RES    = 285
COL_S      = 345
COL_CPU    = 370
COL_MEM    = 425
COL_TIME   = 480
COL_CMD    = 560


def _now_utc() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _short_pid(name: str) -> int:
    return abs(hash(name)) % 99000 + 1000


def _kib(size_kb: int) -> str:
    if size_kb >= 1_000_000:
        return f"{size_kb / 1_000_000:5.1f}G"
    if size_kb >= 1000:
        return f"{size_kb / 1000:5.1f}M"
    return f"{size_kb:5d}"


def _time_plus(parsed: _dt.datetime, now: _dt.datetime) -> str:
    delta = now - parsed
    seconds = int(delta.total_seconds())
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return f"  0:{seconds:02d}.00"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m:3d}:{s:02d}.00"
    days = delta.days
    if days < 1:
        h, rem = divmod(seconds, 3600)
        m, _ = divmod(rem, 60)
        return f"{h:3d}h{m:02d}m"
    if days < 365:
        return f"{days:4d}d{(seconds % 86400) // 3600:02d}h"
    y = days // 365
    rd = days % 365
    return f"{y:3d}y{rd:03d}d"


def _state(parsed: _dt.datetime, now: _dt.datetime) -> str:
    delta = now - parsed
    if delta.days <= 7:
        return "R"
    if delta.days <= 60:
        return "S"
    return "I"


def _state_color(s: str) -> str:
    return {"R": GREEN, "S": INK, "I": DIM}.get(s, INK)


def _pct(part: float, whole: float) -> float:
    if whole <= 0:
        return 0.0
    return min(99.9, 100.0 * part / whole)


def _fetch_repos() -> list[dict[str, Any]]:
    raw = _github.get_paged(f"users/{USER}/repos", sort="updated", per_page=100, max_pages=3)
    repos: list[dict[str, Any]] = []
    for r in raw:
        if r.get("fork") or r.get("archived") or r.get("private"):
            continue
        repos.append({
            "name":  r.get("name", "?"),
            "size":  int(r.get("size", 0) or 0),
            "stars": int(r.get("stargazers_count", 0) or 0),
            "forks": int(r.get("forks_count", 0) or 0),
            "lang":  r.get("language") or "",
            "pushed_at": r.get("pushed_at") or r.get("updated_at") or "",
        })
    repos.sort(key=lambda r: (-r["stars"], r["pushed_at"]), reverse=False)
    repos.sort(key=lambda r: (r["stars"], r["pushed_at"]), reverse=True)
    return repos[:VISIBLE_ROWS]


def _load_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    m = re.search(r'<metadata id="repos-cache">(\{.*?\})</metadata>', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _row(i: int, y: int, repo: dict[str, Any], total_stars: int, now: _dt.datetime) -> str:
    pid = _short_pid(repo["name"])
    pushed_iso = repo["pushed_at"]
    try:
        pushed = _dt.datetime.fromisoformat(pushed_iso.replace("Z", "+00:00"))
    except Exception:
        pushed = now
    state = _state(pushed, now)
    state_col = _state_color(state)
    stars = repo["stars"]
    forks = repo["forks"]
    cpu = _pct(stars, max(total_stars, 1))
    mem = _pct(forks, max(stars or 1, 1))
    timeplus = _time_plus(pushed, now)
    lang = repo["lang"]
    lang_col = LANG_COLORS.get(lang, PURPLE)
    cpu_col = HOT if cpu >= 30 else (AMBER if cpu >= 10 else INK)

    parts: list[str] = []
    if i % 2 == 1:
        parts.append(f'<rect x="0" y="{y - LINE_H + 3}" width="{W}" height="{ROW_H}" fill="{ROW_ALT}"/>')

    parts.append(f'<text x="{COL_PID}"  y="{y}" class="r-pid">{pid:5d}</text>')
    parts.append(f'<text x="{COL_USER}" y="{y}" class="r-ink">{_x(USER[:8]):<8}</text>')
    parts.append(f'<text x="{COL_PR}"   y="{y}" class="r-dim">20</text>')
    parts.append(f'<text x="{COL_NI}"   y="{y}" class="r-dim"> 0</text>')
    parts.append(f'<text x="{COL_VIRT}" y="{y}" class="r-ink">{_x(_kib(repo["size"]))}</text>')
    parts.append(f'<text x="{COL_RES}"  y="{y}" class="r-star">★ {stars:4d}</text>')
    parts.append(f'<text x="{COL_S}"    y="{y}" fill="{state_col}" class="r-state">{state}</text>')
    parts.append(f'<text x="{COL_CPU}"  y="{y}" fill="{cpu_col}" class="r-num">{cpu:5.1f}</text>')
    parts.append(f'<text x="{COL_MEM}"  y="{y}" class="r-ink">{mem:5.1f}</text>')
    parts.append(f'<text x="{COL_TIME}" y="{y}" class="r-dim">{_x(timeplus)}</text>')
    parts.append(f'<text x="{COL_CMD}"  y="{y}" class="r-cmd">{_x(repo["name"][:28])}</text>')
    if lang:
        tag_x = COL_CMD + min(len(repo["name"][:28]) * 7 + 12, 220)
        parts.append(
            f'<text x="{tag_x}" y="{y}" font-family="{FONT}" font-size="11" fill="{lang_col}">'
            f'· {_x(lang)}</text>'
        )
    return "".join(parts)


def _render(repos: list[dict[str, Any]], total_stars: int, total_forks: int, generated_at: _dt.datetime) -> str:
    now = generated_at
    uptime_days = (now.date() - _dt.date(2017, 1, 1)).days
    uptime_y = uptime_days // 365
    uptime_d = uptime_days % 365
    uptime_str = f"{uptime_y}y {uptime_d:3d}d"

    n_total = len(repos)
    n_running = sum(1 for r in repos if _state(_dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")), now) == "R")
    n_sleep = sum(1 for r in repos if _state(_dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")), now) == "S")
    n_idle = n_total - n_running - n_sleep

    la_1 = round(min(4.0, n_running * 0.7 + (n_sleep * 0.05)), 2)
    la_5 = round(la_1 * 0.85, 2)
    la_15 = round(la_1 * 0.7, 2)

    cpu_us = round(min(40.0, n_running * 3.2 + 1.0), 1)
    cpu_id = round(100.0 - cpu_us - 1.0, 1)

    hh = now.strftime("%H:%M:%S")

    header_lines = [
        (
            f'<text x="12" y="{HEADER_TOP}" class="r-ink">'
            f'top - <tspan fill="{AMBER}">{hh}</tspan> '
            f'up <tspan fill="{INK}">{_x(uptime_str)}</tspan>, '
            f'1 user, load average: '
            f'<tspan fill="{HOT if la_1 >= 1 else INK}">{la_1:.2f}</tspan>, '
            f'<tspan fill="{INK}">{la_5:.2f}</tspan>, '
            f'<tspan fill="{DIM}">{la_15:.2f}</tspan>'
            f'</text>'
        ),
        (
            f'<text x="12" y="{HEADER_TOP + LINE_H}" class="r-ink">'
            f'Tasks: <tspan fill="{AMBER}">{n_total:3d}</tspan> total, '
            f'<tspan fill="{GREEN}">{n_running:3d}</tspan> running, '
            f'<tspan fill="{INK}">{n_sleep:3d}</tspan> sleeping, '
            f'<tspan fill="{DIM}">{n_idle:3d}</tspan> idle, '
            f'<tspan fill="{HOT}">  0</tspan> zombie'
            f'</text>'
        ),
        (
            f'<text x="12" y="{HEADER_TOP + LINE_H * 2}" class="r-ink">'
            f'%Cpu(s): <tspan fill="{AMBER}">{cpu_us:5.1f}</tspan> us, '
            f'<tspan fill="{INK}">  1.0</tspan> sy, '
            f'<tspan fill="{DIM}">  0.0</tspan> ni, '
            f'<tspan fill="{GREEN}">{cpu_id:5.1f}</tspan> id, '
            f'<tspan fill="{DIM}">  0.0</tspan> wa, '
            f'<tspan fill="{DIM}">  0.0</tspan> hi, '
            f'<tspan fill="{DIM}">  0.0</tspan> si'
            f'</text>'
        ),
        (
            f'<text x="12" y="{HEADER_TOP + LINE_H * 3}" class="r-ink">'
            f'KiB Mem : <tspan fill="{AMBER}">{total_stars * 1024:9d}</tspan> total, '
            f'<tspan fill="{GREEN}">{(total_stars * 256):9d}</tspan> free, '
            f'<tspan fill="{INK}">{(total_stars * 768):9d}</tspan> used   '
            f'<tspan fill="{DIM}">(★ </tspan>'
            f'<tspan fill="{AMBER}">{total_stars}</tspan>'
            f'<tspan fill="{DIM}"> stars · ⑂ {total_forks} forks)</tspan>'
            f'</text>'
        ),
        (
            f'<text x="12" y="{HEADER_TOP + LINE_H * 4}" class="r-ink">'
            f'KiB Swap: <tspan fill="{DIM}">     2048</tspan> total, '
            f'<tspan fill="{GREEN}">     2048</tspan> free, '
            f'<tspan fill="{DIM}">        0</tspan> used.   '
            f'<tspan fill="{INK}">{(total_stars * 256 + 5120):9d}</tspan> avail Mem'
            f'</text>'
        ),
    ]

    col_hdr = (
        f'<rect x="0" y="{COL_HDR_Y - LINE_H + 4}" width="{W}" height="{ROW_H}" fill="{HILITE}"/>'
        f'<text x="{COL_PID}"  y="{COL_HDR_Y}" class="r-hdr">  PID</text>'
        f'<text x="{COL_USER}" y="{COL_HDR_Y}" class="r-hdr">USER    </text>'
        f'<text x="{COL_PR}"   y="{COL_HDR_Y}" class="r-hdr">PR</text>'
        f'<text x="{COL_NI}"   y="{COL_HDR_Y}" class="r-hdr">NI</text>'
        f'<text x="{COL_VIRT}" y="{COL_HDR_Y}" class="r-hdr">  VIRT</text>'
        f'<text x="{COL_RES}"  y="{COL_HDR_Y}" class="r-hdr">   RES</text>'
        f'<text x="{COL_S}"    y="{COL_HDR_Y}" class="r-hdr">S</text>'
        f'<text x="{COL_CPU}"  y="{COL_HDR_Y}" class="r-hdr"> %CPU</text>'
        f'<text x="{COL_MEM}"  y="{COL_HDR_Y}" class="r-hdr"> %MEM</text>'
        f'<text x="{COL_TIME}" y="{COL_HDR_Y}" class="r-hdr">    TIME+</text>'
        f'<text x="{COL_CMD}"  y="{COL_HDR_Y}" class="r-hdr">COMMAND</text>'
    )

    rows: list[str] = []
    for i, repo in enumerate(repos):
        y = ROW_TOP + (i + 1) * ROW_H - 4
        rows.append(_row(i, y, repo, total_stars, now))
    rows_inner = "\n      ".join(rows)

    sel_dur = max(8, len(repos))
    sel_keytimes = ";".join(f"{i / max(len(repos), 1):.4f}" for i in range(len(repos) + 1))
    sel_values = ";".join(str(ROW_TOP + i * ROW_H - LINE_H + 3) for i in range(len(repos) + 1))

    refresh = f"every {now.strftime('%Hh')} · cron */6h"

    cache_blob = json.dumps({
        "generated_at": now.isoformat(),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "repos": repos,
    }, separators=(",", ":"))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="lordware top-style repo process table">
  <defs>
    <style>
      .r-bg    {{ fill: {BG}; }}
      .r-subbg {{ fill: {SUB_BG}; }}
      .r-border{{ fill: none; stroke: {GRID}; stroke-width: 1; }}
      .r-ink   {{ font-family: {FONT}; font-size: 11px; fill: {INK}; }}
      .r-dim   {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
      .r-hdr   {{ font-family: {FONT}; font-size: 11px; fill: {AMBER}; font-weight: 700; letter-spacing: 0.4px; }}
      .r-pid   {{ font-family: {FONT}; font-size: 11px; fill: {BLUE}; }}
      .r-state {{ font-family: {FONT}; font-size: 11px; font-weight: 700; }}
      .r-num   {{ font-family: {FONT}; font-size: 11px; font-weight: 700; }}
      .r-star  {{ font-family: {FONT}; font-size: 11px; fill: {AMBER}; }}
      .r-cmd   {{ font-family: {FONT}; font-size: 11px; fill: {INK}; font-weight: 700; }}
      .r-foot  {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
    </style>
  </defs>
  <metadata id="repos-cache">{cache_blob}</metadata>

  <rect class="r-bg" width="{W}" height="{H}"/>
  <rect class="r-border" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"/>

  {chr(10).join(header_lines)}

  {col_hdr}

  <rect x="0" y="{ROW_TOP - LINE_H + 3}" width="{W}" height="{ROW_H}" fill="{HILITE}" opacity="0.55">
    <animate attributeName="y" values="{sel_values}" keyTimes="{sel_keytimes}" dur="{sel_dur}s" repeatCount="indefinite"/>
  </rect>

  <g>
    {rows_inner}
  </g>

  <line x1="0" y1="{H - 18}" x2="{W}" y2="{H - 18}" stroke="{GRID}" stroke-width="1"/>
  <rect class="r-subbg" x="0" y="{H - 18}" width="{W}" height="18"/>
  <circle cx="14" cy="{H - 9}" r="3" fill="{GREEN}">
    <animate attributeName="opacity" values="1;0.25;1" dur="1.4s" repeatCount="indefinite"/>
  </circle>
  <text class="r-foot" x="24" y="{H - 6}">live · GitHub API · {USER}@lordware-pi · refresh {_x(refresh)}</text>
  <text class="r-foot" x="{W - 130}" y="{H - 6}">F1 Help  F10 Quit</text>
</svg>
'''
    return svg


def _render_from_cache(cache: dict[str, Any]) -> str:
    repos = cache.get("repos", [])
    total_stars = cache.get("total_stars", sum(r.get("stars", 0) for r in repos))
    total_forks = cache.get("total_forks", sum(r.get("forks", 0) for r in repos))
    return _render(repos, total_stars, total_forks, _now_utc())


def generate(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "repos.svg"

    try:
        repos = _fetch_repos()
        if not repos:
            raise _github.GitHubError("no public repos returned")
        total_stars = sum(r["stars"] for r in repos)
        total_forks = sum(r["forks"] for r in repos)
        svg = _render(repos, total_stars, total_forks, _now_utc())
    except _github.GitHubError as e:
        cache = _load_cache(out_path)
        if cache is None:
            print(f"[gen_repos] API failed and no cache: {e}; rendering empty table")
            svg = _render([], 0, 0, _now_utc())
        else:
            print(f"[gen_repos] API failed ({e}); using cached data from {cache.get('generated_at')}")
            svg = _render_from_cache(cache)

    out_path.write_text(svg, encoding="utf-8", newline="\n")
    return out_path


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    print(generate(ROOT / "assets"))
