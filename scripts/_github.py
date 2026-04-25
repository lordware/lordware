from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
USER_AGENT = "lordware-readme-regen/1.0"


class GitHubError(RuntimeError):
    pass


def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    if extra:
        h.update(extra)
    return h


def _request(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
    retries: int = 3,
) -> Any:
    last_exc: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, method=method, headers=_headers(headers))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code in (429, 502, 503, 504):
                time.sleep(1.5 * (attempt + 1))
                continue
            try:
                detail = e.read().decode("utf-8", errors="replace")[:200]
            except Exception:
                detail = ""
            raise GitHubError(f"HTTP {e.code} for {url}: {detail}") from e
        except urllib.error.URLError as e:
            last_exc = e
            time.sleep(1.0 * (attempt + 1))
            continue
    raise GitHubError(f"unreachable after retries: {url}: {last_exc}")


def get(path: str, **params: Any) -> Any:
    if path.startswith("http"):
        url = path
    else:
        url = f"{API}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    return _request(url)


def get_paged(path: str, *, per_page: int = 100, max_pages: int = 5, **params: Any) -> list[Any]:
    out: list[Any] = []
    for page in range(1, max_pages + 1):
        chunk = get(path, per_page=per_page, page=page, **params)
        if not isinstance(chunk, list) or not chunk:
            break
        out.extend(chunk)
        if len(chunk) < per_page:
            break
    return out


def graphql(query: str, variables: dict[str, Any] | None = None) -> Any:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    result = _request(
        GRAPHQL,
        method="POST",
        body=payload,
        headers={"Content-Type": "application/json"},
    )
    if isinstance(result, dict) and result.get("errors"):
        raise GitHubError(f"GraphQL errors: {result['errors']}")
    if not isinstance(result, dict) or "data" not in result:
        raise GitHubError(f"GraphQL: malformed response: {result!r}")
    return result["data"]
