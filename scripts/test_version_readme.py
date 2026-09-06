"""Regression checks for stale profile images after publishing."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from version_readme import RAW_ASSETS, update_readme


class ReadmeVersionsTest(unittest.TestCase):
    def test_versions_track_content_and_preserve_external_images(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'assets').mkdir()
            svg = root / 'assets/panel.svg'
            svg.write_bytes(b'<svg>\r\n</svg>\r\n')
            readme = root / 'README.md'
            external = '<img src="https://example.com/visitor.svg" />'
            readme.write_text(
                '<picture><source srcset="assets/panel.svg" />'
                '<img src="assets/panel.svg" /></picture>' + external,
                encoding='utf-8',
            )
            self.assertTrue(update_readme(root))
            first = readme.read_text(encoding='utf-8')
            self.assertEqual(first.count(RAW_ASSETS + 'assets/panel.svg?v='), 2)
            self.assertIn(external, first)
            self.assertFalse(update_readme(root))
            svg.write_bytes(b'<svg>\n</svg>\n')
            self.assertFalse(update_readme(root))
            svg.write_bytes(b'<svg><rect /></svg>\n')
            self.assertTrue(update_readme(root))
            self.assertNotEqual(readme.read_text(encoding='utf-8'), first)
            self.assertFalse(update_readme(root))

    def test_missing_asset_does_not_partially_rewrite_readme(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            readme = root / 'README.md'
            original = '<img src="assets/missing.svg" />'
            readme.write_text(original, encoding='utf-8')
            with self.assertRaises(FileNotFoundError):
                update_readme(root)
            self.assertEqual(readme.read_text(encoding='utf-8'), original)


if __name__ == '__main__':
    unittest.main()
