"""Give README images a new cache key whenever their SVG content changes."""
from hashlib import sha256
from pathlib import Path
import re


RAW_ASSETS = 'https://raw.githubusercontent.com/lordware/lordware/main/'
IMAGE_URL = re.compile(
    r'(?P<attribute>\b(?:src|srcset)=")'
    r'(?:' + re.escape(RAW_ASSETS) + r')?'
    r'(?P<path>assets/[\w-]+\.svg)(?:\?v=[\w-]+)?(?=")'
)


def update_readme(root: Path) -> bool:
    readme = root / 'README.md'
    original = readme.read_text(encoding='utf-8')

    def version(match):
        # Normalize line endings so Windows and Actions produce the same key.
        content = (root / match['path']).read_text(encoding='utf-8').encode('utf-8')
        digest = sha256(content).hexdigest()[:16]
        # Use raw URLs directly: GitHub's /raw/ redirect drops query parameters.
        return f"{match['attribute']}{RAW_ASSETS}{match['path']}?v={digest}"

    updated = IMAGE_URL.sub(version, original)
    if updated == original:
        return False
    readme.write_text(updated, encoding='utf-8', newline='\n')
    return True


if __name__ == '__main__':
    update_readme(Path(__file__).resolve().parent.parent)
