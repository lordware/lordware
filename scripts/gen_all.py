"""Regenerate every profile panel. Use --offline for deterministic local previews."""
from pathlib import Path
import argparse
import gen_profile
import gen_instruments
import gen_telemetry
import gen_auxiliary
from version_readme import update_readme


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Use the saved GitHub and visitor snapshots without network requests')
    args = parser.parse_args()
    out = Path(__file__).resolve().parent.parent / 'assets'
    panels = [
        *gen_profile.generate(out),
        *gen_instruments.generate(out),
        *gen_telemetry.generate(out, offline=args.offline),
        *gen_auxiliary.generate(out, offline=args.offline),
    ]
    for path in panels:
        print(f'[gen_all] {path.name}')
    if update_readme(out.parent):
        print('[gen_all] README image versions updated')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
