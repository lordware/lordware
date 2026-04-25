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
INK      = "#E8DCC4"
DIM      = "#A89968"
GRID     = "#3A352C"
GREEN    = "#4FD97F"
AMBER    = "#FFB83D"
BLUE     = "#4FC3FF"
HOT      = "#FF5C3A"
PURPLE   = "#B77FFF"
PINK     = "#FF7FB2"
FONT     = "'IBM Plex Mono', Menlo, Consolas, monospace"

W, H = 960, 240
HEADER_H = 24
FOOTER_H = 20
ROW_H = 13
VISIBLE_ROWS = (H - HEADER_H - FOOTER_H) // ROW_H


EVENT_RENDERERS = {
    "PushEvent": ("kern",
                  GREEN,
                  lambda e: (
                      f"PushEvent: {e['repo']['name']} "
                      f"{(e.get('payload') or {}).get('ref', '').replace('refs/heads/', '')} "
                      f"+{(e.get('payload') or {}).get('size', 0)} commits"
                  )),
    "PullRequestEvent": ("sshd",
                         BLUE,
                         lambda e: (
                             f"PullRequestEvent: {e['repo']['name']} "
                             f"#{(e.get('payload') or {}).get('number', '?')} "
                             f"{(e.get('payload') or {}).get('action', '?')}"
                         )),
    "PullRequestReviewEvent": ("sshd",
                               BLUE,
                               lambda e: (
                                   f"PullRequestReviewEvent: {e['repo']['name']} "
                                   f"#{((e.get('payload') or {}).get('pull_request') or {}).get('number', '?')} "
                                   f"{(e.get('payload') or {}).get('action', '?')}"
                               )),
    "PullRequestReviewCommentEvent": ("sshd",
                                      BLUE,
                                      lambda e: (
                                          f"PRReviewCommentEvent: {e['repo']['name']} "
                                          f"{(e.get('payload') or {}).get('action', '?')}"
                                      )),
    "IssuesEvent": ("kern",
                    AMBER,
                    lambda e: (
                        f"IssuesEvent: {e['repo']['name']} "
                        f"#{((e.get('payload') or {}).get('issue') or {}).get('number', '?')} "
                        f"{(e.get('payload') or {}).get('action', '?')}"
                    )),
    "IssueCommentEvent": ("kern",
                          AMBER,
                          lambda e: (
                              f"IssueCommentEvent: {e['repo']['name']} "
                              f"#{((e.get('payload') or {}).get('issue') or {}).get('number', '?')} "
                              f"{(e.get('payload') or {}).get('action', '?')}"
                          )),
    "WatchEvent": ("systemd",
                   AMBER,
                   lambda e: f"WatchEvent: {e['repo']['name']} ★ +1"),
    "ForkEvent": ("systemd",
                  PURPLE,
                  lambda e: (
                      f"ForkEvent: {e['repo']['name']} -> "
                      f"{((e.get('payload') or {}).get('forkee') or {}).get('full_name', '?')}"
                  )),
    "CreateEvent": ("init",
                    GREEN,
                    lambda e: (
                        f"CreateEvent: {e['repo']['name']} "
                        f"{(e.get('payload') or {}).get('ref_type', 'ref')} "
                        f"{(e.get('payload') or {}).get('ref', '') or ''}"
                    ).rstrip()),
    "DeleteEvent": ("init",
                    HOT,
                    lambda e: (
                        f"DeleteEvent: {e['repo']['name']} "
                        f"{(e.get('payload') or {}).get('ref_type', 'ref')} "
                        f"{(e.get('payload') or {}).get('ref', '') or ''}"
                    ).rstrip()),
    "ReleaseEvent": ("init",
                     PINK,
                     lambda e: (
                         f"ReleaseEvent: {e['repo']['name']} "
                         f"{((e.get('payload') or {}).get('release') or {}).get('tag_name', '?')}"
                     )),
    "PublicEvent": ("init",
                    GREEN,
                    lambda e: f"PublicEvent: {e['repo']['name']} -> public"),
    "MemberEvent": ("init",
                    PURPLE,
                    lambda e: (
                        f"MemberEvent: {e['repo']['name']} "
                        f"{(e.get('payload') or {}).get('action', '?')} "
                        f"{((e.get('payload') or {}).get('member') or {}).get('login', '?')}"
                    )),
    "GollumEvent": ("kern",
                    BLUE,
                    lambda e: f"GollumEvent: {e['repo']['name']} wiki updated"),
    "CommitCommentEvent": ("kern",
                           AMBER,
                           lambda e: f"CommitCommentEvent: {e['repo']['name']}"),
}


def _now_utc() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _fmt_time(iso: str) -> str:
    try:
        dt = _dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        dt = _now_utc()
    return dt.strftime("%b %d %H:%M:%S")


def _is_noise(e: dict[str, Any]) -> bool:
    actor_login = ((e.get("actor") or {}).get("login") or "").lower()
    if actor_login.endswith("[bot]"):
        return True
    et = e.get("type")
    payload = e.get("payload") or {}
    if et == "PushEvent" and int(payload.get("size", 0) or 0) == 0:
        return True
    return False


def _fetch_events() -> list[dict[str, Any]]:
    raw = _github.get_paged(f"users/{USER}/events/public", per_page=100, max_pages=2)
    out: list[dict[str, Any]] = []
    for e in raw:
        et = e.get("type")
        if et not in EVENT_RENDERERS:
            continue
        if _is_noise(e):
            continue
        facility, color, fmt = EVENT_RENDERERS[et]
        try:
            msg = fmt(e)
        except Exception:
            continue
        out.append({
            "ts": e.get("created_at", ""),
            "facility": facility,
            "color": color,
            "msg": msg,
        })
    return out


def _load_cache(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    m = re.search(r'<metadata id="syslog-cache">(\[.*?\])</metadata>', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _render(events: list[dict[str, Any]], generated_at: _dt.datetime) -> str:
    if not events:
        events = [{
            "ts": generated_at.isoformat(),
            "facility": "init",
            "color": DIM,
            "msg": "no public events visible right now — try again later",
        }]

    events = events[:40]

    rows: list[str] = []
    for i, ev in enumerate(events):
        y = (i + 1) * ROW_H
        ts = _fmt_time(ev["ts"])
        facility = ev["facility"]
        msg = ev["msg"]
        if len(msg) > 92:
            msg = msg[:89] + "..."
        if i % 2 == 1:
            rows.append(
                f'<rect x="0" y="{y - ROW_H + 3}" width="{W}" height="{ROW_H}" fill="{ROW_ALT}"/>'
            )
        rows.append(
            f'<text x="12" y="{y}" class="s-ts">{_x(ts)}</text>'
        )
        rows.append(
            f'<text x="120" y="{y}" class="s-host">lordware-pi</text>'
        )
        rows.append(
            f'<text x="208" y="{y}" class="s-fac">{_x(facility)}:</text>'
        )
        rows.append(
            f'<text x="262" y="{y}" fill="{ev["color"]}" class="s-msg">{_x(msg)}</text>'
        )

    strip_height = len(events) * ROW_H
    dur = max(20, len(events) * 2)
    rows_inner = "\n      ".join(rows)

    cache_blob = json.dumps(events, separators=(",", ":"))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="lordware syslog tail of GitHub events">
  <defs>
    <style>
      .s-bg    {{ fill: {BG}; }}
      .s-subbg {{ fill: {SUB_BG}; }}
      .s-border{{ fill: none; stroke: {GRID}; stroke-width: 1; }}
      .s-head  {{ font-family: {FONT}; font-size: 11px; fill: {AMBER}; font-weight: 700; }}
      .s-headd {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
      .s-ts    {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
      .s-host  {{ font-family: {FONT}; font-size: 11px; fill: {BLUE}; }}
      .s-fac   {{ font-family: {FONT}; font-size: 11px; fill: {AMBER}; font-weight: 700; }}
      .s-msg   {{ font-family: {FONT}; font-size: 11px; }}
      .s-foot  {{ font-family: {FONT}; font-size: 11px; fill: {DIM}; }}
    </style>
    <clipPath id="s-clip">
      <rect x="0" y="{HEADER_H}" width="{W}" height="{H - HEADER_H - FOOTER_H}"/>
    </clipPath>
  </defs>
  <metadata id="syslog-cache">{cache_blob}</metadata>

  <rect class="s-bg" width="{W}" height="{H}"/>
  <rect class="s-border" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}"/>

  <rect class="s-subbg" x="0" y="0" width="{W}" height="{HEADER_H}"/>
  <line x1="0" y1="{HEADER_H}" x2="{W}" y2="{HEADER_H}" stroke="{GRID}" stroke-width="1"/>
  <text class="s-head"  x="12"  y="16">$ tail -F /var/log/lordware/github.log</text>
  <text class="s-headd" x="{W - 240}" y="16">facility=user · {len(events)} entries · live</text>

  <g clip-path="url(#s-clip)">
    <g transform="translate(0 {HEADER_H})">
      <animateTransform attributeName="transform" type="translate"
        from="0 {HEADER_H}" to="0 {HEADER_H - strip_height}"
        dur="{dur}s" repeatCount="indefinite"/>
      <g>
      {rows_inner}
      </g>
      <g transform="translate(0 {strip_height})">
      {rows_inner}
      </g>
    </g>
  </g>

  <line x1="0" y1="{H - FOOTER_H}" x2="{W}" y2="{H - FOOTER_H}" stroke="{GRID}" stroke-width="1"/>
  <rect class="s-subbg" x="0" y="{H - FOOTER_H}" width="{W}" height="{FOOTER_H}"/>
  <circle cx="14" cy="{H - 10}" r="3" fill="{HOT}">
    <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite"/>
  </circle>
  <text class="s-foot" x="24" y="{H - 6}">rsyslog · /dev/github · {USER} · regen */6h</text>
  <text class="s-foot" x="{W - 60}" y="{H - 6}">^C</text>
</svg>
'''
    return svg


def generate(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "syslog.svg"

    try:
        events = _fetch_events()
        svg = _render(events, _now_utc())
    except _github.GitHubError as e:
        cache = _load_cache(out_path)
        if cache is None:
            print(f"[gen_log] API failed and no cache: {e}; rendering placeholder")
            svg = _render([], _now_utc())
        else:
            print(f"[gen_log] API failed ({e}); using cached events")
            svg = _render(cache, _now_utc())

    out_path.write_text(svg, encoding="utf-8", newline="\n")
    return out_path


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    print(generate(ROOT / "assets"))
