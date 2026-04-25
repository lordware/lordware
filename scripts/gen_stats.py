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
INK      = "#E8DCC4"
DIM      = "#A89968"
GRID     = "#3A352C"
GREEN    = "#4FD97F"
AMBER    = "#FFB83D"
HOT      = "#FF5C3A"
BLUE     = "#4FC3FF"
PURPLE   = "#B77FFF"
FONT     = "'IBM Plex Mono', Menlo, Consolas, monospace"

W, H = 960, 160
HEADER_H = 26
FOOTER_H = 22
PAD = 12
N_CELLS = 5
CELL_GAP = 8


def _now_utc() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    following { totalCount }
    repositories(privacy: PUBLIC, first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount, forkCount }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def _streaks(weeks: list[dict[str, Any]], today: _dt.date) -> tuple[int, int]:
    days: list[tuple[_dt.date, int]] = []
    for w in weeks:
        for d in w.get("contributionDays", []):
            try:
                date = _dt.date.fromisoformat(d["date"])
            except Exception:
                continue
            count = int(d.get("contributionCount", 0))
            days.append((date, count))
    days.sort(key=lambda kv: kv[0])

    longest = cur = 0
    for _, c in days:
        if c > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    by_date = {d: c for d, c in days}
    current = 0
    cursor = today
    if by_date.get(cursor, 0) == 0:
        cursor -= _dt.timedelta(days=1)
    while by_date.get(cursor, 0) > 0:
        current += 1
        cursor -= _dt.timedelta(days=1)
    return current, longest


def _fetch_stats() -> dict[str, Any]:
    data = _github.graphql(GRAPHQL_QUERY, {"login": USER})
    user = (data or {}).get("user") or {}
    if not user:
        raise _github.GitHubError("graphql: empty user")

    followers = (user.get("followers") or {}).get("totalCount", 0)
    following = (user.get("following") or {}).get("totalCount", 0)
    repos_obj = user.get("repositories") or {}
    repos_total = repos_obj.get("totalCount", 0)
    nodes = repos_obj.get("nodes") or []
    stars_total = sum(int(n.get("stargazerCount", 0) or 0) for n in nodes)
    forks_total = sum(int(n.get("forkCount", 0) or 0) for n in nodes)

    contrib = user.get("contributionsCollection") or {}
    commits_year = int(contrib.get("totalCommitContributions", 0) or 0)
    pr_year = int(contrib.get("totalPullRequestContributions", 0) or 0)
    issues_year = int(contrib.get("totalIssueContributions", 0) or 0)

    cal = contrib.get("contributionCalendar") or {}
    total_year = int(cal.get("totalContributions", 0) or 0)
    today = _now_utc().date()
    current_streak, longest_streak = _streaks(cal.get("weeks", []), today)

    return {
        "followers": followers,
        "following": following,
        "repos": repos_total,
        "stars": stars_total,
        "forks": forks_total,
        "commits_year": commits_year,
        "pr_year": pr_year,
        "issues_year": issues_year,
        "total_year": total_year,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }


def _load_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    m = re.search(r'<metadata id="stats-cache">(\{.*?\})</metadata>', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _fmt_big(n: int) -> str:
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}k"
    return f"{n / 1_000_000:.1f}M"


def _cell(x: int, y: int, w: int, h: int, label: str, value: str, sub: str,
          color: str, accent: str = AMBER) -> str:
    inner_x = x + 12
    digit_size = 36 if len(value) <= 4 else (30 if len(value) <= 6 else 24)
    digit_y = y + h // 2 + digit_size // 3
    return (
        f'<g>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" '
        f'fill="{SUB_BG}" stroke="{GRID}"/>'
        f'<rect x="{x}" y="{y}" width="4" height="{h}" rx="2" fill="{accent}"/>'
        f'<text x="{inner_x}" y="{y + 16}" font-family="{FONT}" font-size="10" '
        f'fill="{DIM}" letter-spacing="2">{_x(label)}</text>'
        f'<circle cx="{x + w - 14}" cy="{y + 14}" r="2.5" fill="{accent}">'
        f'<animate attributeName="opacity" values="1;0.3;1" dur="1.4s" repeatCount="indefinite"/>'
        f'</circle>'
        f'<text x="{x + w - 12}" y="{y + h - 8}" font-family="{FONT}" font-size="9" '
        f'fill="{DIM}" text-anchor="end">{_x(sub)}</text>'
        f'<text x="{inner_x}" y="{digit_y}" font-family="{FONT}" font-size="{digit_size}" '
        f'font-weight="700" fill="{color}" letter-spacing="1">{_x(value)}</text>'
        f'</g>'
    )


def _render(stats: dict[str, Any], generated_at: _dt.datetime) -> str:
    cell_w = (W - PAD * 2 - CELL_GAP * (N_CELLS - 1)) // N_CELLS
    cell_h = H - HEADER_H - FOOTER_H - PAD
    y = HEADER_H + 4

    cells: list[str] = []
    cells_meta = [
        ("STARS",    _fmt_big(stats.get("stars", 0)),
         f"⑂ {_fmt_big(stats.get('forks', 0))} forks", AMBER, AMBER),
        ("REPOS",    str(stats.get("repos", 0)),
         "public · owner", BLUE, BLUE),
        ("FOLLOWERS", _fmt_big(stats.get("followers", 0)),
         f"following {_fmt_big(stats.get('following', 0))}", PURPLE, PURPLE),
        ("COMMITS / 1y", _fmt_big(stats.get("commits_year", 0)),
         f"PR {_fmt_big(stats.get('pr_year', 0))} · issues {_fmt_big(stats.get('issues_year', 0))}", GREEN, GREEN),
        ("STREAK", f"{stats.get('current_streak', 0)}d",
         f"longest {stats.get('longest_streak', 0)}d", HOT, HOT),
    ]
    for i, (label, value, sub, color, accent) in enumerate(cells_meta):
        cx = PAD + i * (cell_w + CELL_GAP)
        cells.append(_cell(cx, y, cell_w, cell_h, label, value, sub, color, accent))

    when = generated_at.strftime("%Y-%m-%d %H:%M:%SZ")
    total_year = stats.get("total_year", 0)
    cache_blob = json.dumps(stats, separators=(",", ":"))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="lordware live GitHub stats panel">
  <defs>
    <style>
      .st-bg     {{ fill: {BG}; }}
      .st-subbg  {{ fill: {SUB_BG}; }}
      .st-border {{ fill: none; stroke: {GRID}; stroke-width: 1; }}
      .st-title  {{ font-family: {FONT}; font-size: 13px; fill: {AMBER}; font-weight: 700; letter-spacing: 1px; }}
      .st-sub    {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
      .st-foot   {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
    </style>
  </defs>
  <metadata id="stats-cache">{cache_blob}</metadata>

  <rect class="st-bg" width="{W}" height="{H}"/>
  <rect class="st-border" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"/>

  <rect class="st-subbg" x="0" y="0" width="{W}" height="{HEADER_H}"/>
  <line x1="0" y1="{HEADER_H}" x2="{W}" y2="{HEADER_H}" stroke="{GRID}" stroke-width="1"/>
  <text class="st-title" x="12" y="18">/sys/lordware/stats</text>
  <text class="st-sub"   x="170" y="18">live · GitHub REST + GraphQL</text>
  <text class="st-sub"   x="{W - 240}" y="18">contrib (1y) {total_year} · refresh */6h</text>

  {"".join(cells)}

  <line x1="0" y1="{H - FOOTER_H}" x2="{W}" y2="{H - FOOTER_H}" stroke="{GRID}" stroke-width="1"/>
  <rect class="st-subbg" x="0" y="{H - FOOTER_H}" width="{W}" height="{FOOTER_H}"/>
  <circle cx="14" cy="{H - 10}" r="3" fill="{GREEN}">
    <animate attributeName="opacity" values="1;0.3;1" dur="1.4s" repeatCount="indefinite"/>
  </circle>
  <text class="st-foot" x="24" y="{H - 7}">sampled {when} · v3 api · graphql v4</text>
  <text class="st-foot" x="{W - 90}" y="{H - 7}">{USER}@gh</text>
</svg>
'''
    return svg


def _placeholder_stats() -> dict[str, Any]:
    return {
        "followers": 0, "following": 0, "repos": 0,
        "stars": 0, "forks": 0,
        "commits_year": 0, "pr_year": 0, "issues_year": 0,
        "total_year": 0, "current_streak": 0, "longest_streak": 0,
    }


def generate(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "stats.svg"

    try:
        stats = _fetch_stats()
    except _github.GitHubError as e:
        cache = _load_cache(out_path)
        if cache is None:
            print(f"[gen_stats] API failed and no cache: {e}; rendering placeholder")
            stats = _placeholder_stats()
        else:
            print(f"[gen_stats] API failed ({e}); using cached stats")
            stats = cache

    svg = _render(stats, _now_utc())
    out_path.write_text(svg, encoding="utf-8", newline="\n")
    return out_path


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    print(generate(ROOT / "assets"))
