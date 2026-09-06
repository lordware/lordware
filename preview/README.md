# Local profile preview

From the repository root, run:

```powershell
python preview/server.py
```

Open <http://127.0.0.1:4173>. Stop the server with Ctrl+C. To use a different port, run `python preview/server.py --port 4174`.

**After** reads the current root `README.md`; **Before** reads `HEAD:README.md` without changing Git state. Original `main/assets/` image URLs are served from the same Git snapshot. Other original external images remain external. Use **Refresh** after edits. Desktop uses an 896 px outer frame (830 px content); Mobile uses a 375 px outer frame (341 px content), capped to the available viewport. Picture source width queries use the simulated 375 px viewport in Mobile and the browser viewport in Desktop, updating on resize. Theme controls select the matching `<picture>` source and set the browser color scheme; combined width and theme queries are evaluated together.

This is a local approximation of GitHub's README rendering, not a GitHub page or publication. It supports repository HTML plus the headings and fenced code blocks used by the original README. It does not implement arbitrary Markdown or GitHub sanitization. Only use it with trusted local README content.

The Python standard library server binds exclusively to `127.0.0.1`. Its routes expose only the preview page, CSS, JavaScript, README JSON, and image files inside `assets/` (including read-only HEAD versions); other paths return 404. No dependencies, Git changes, or uploads are required.

## Profile artwork

From the repository root, rebuild the complete SVG set using saved snapshots:

```powershell
python scripts/gen_all.py --offline
```

Python 3.10+ and PyYAML are required (`python -m pip install pyyaml`). Omit `--offline` to refresh GitHub, visitor, and contribution sources. Scheduled GitHub workflows use the new generators. API counters retain source timestamps and display unavailable values explicitly.

The README contains only SVG images, with separate compositions below 600px. Every original panel is retained. CAN/serial/POST screens are protocol illustrations; GitHub counters and events use recorded API data. The local preview does not publish changes; publishing happens through Git.
