"""Tests for scripts/check.py: python3 -m unittest discover -s scripts (CI runs this)."""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

STARTER = json.loads((check.ROOT / "widgets" / "simple-switch" / "widget.json").read_text())


def problems(manifest: dict) -> list[str]:
    return check.manifest_problems(json.dumps(manifest).encode())[1]


class ManifestRules(unittest.TestCase):
    def test_the_starter_widget_passes(self):
        self.assertEqual(problems(STARTER), [])

    def test_the_schema_refuses_what_the_standard_does_not_allow(self):
        for change in ({"device_classes": ["lock"]}, {"id": "Not An Id"}, {"version": "1.0"}, {"extra": True},
                       {"icon": "https://example.invalid/icon.png"}, {"name": "Two\nlines"},
                       {"views": {"s": {"kind": "html", "html": "<b>"}}}):
            with self.subTest(change=change):
                self.assertTrue(problems({**STARTER, **change}))

    def test_permissions_must_match_the_controls(self):
        self.assertIn("permissions must include 'device:command' exactly when a view has a control",
                      problems({**STARTER, "permissions": ["device:read"]}))
        read_only = {**STARTER, "views": {"s": {"kind": "value", "field": "state.on"}}, "default_size": "s"}
        self.assertEqual(problems({**read_only, "permissions": ["device:read"]}), [])
        self.assertTrue(problems(read_only))  # asks for device:command without a control

    def test_default_size_needs_a_view(self):
        self.assertIn("default_size 'l' has no view", problems({**STARTER, "default_size": "l"}))

    def test_views_are_bounded(self):
        leaf = {"kind": "value", "field": "state.on"}
        deep = leaf
        for _ in range(check.MAX_DEPTH):
            deep = {"kind": "stack", "children": [deep]}
        self.assertTrue(any("nested" in p for p in problems({**STARTER, "views": {"s": deep}})))
        wide = {"kind": "stack", "children": [{"kind": "row", "children": [leaf] * 8}] * 7}
        self.assertTrue(any("limit is 60" in p for p in problems({**STARTER, "views": {"s": wide}, "permissions": ["device:read"]})))

    def test_size_and_json(self):
        self.assertTrue(check.manifest_problems(b" " * (check.MAX_MANIFEST_BYTES + 1))[1])
        self.assertTrue(check.manifest_problems(b'{"manifest_version": NaN}')[1])

    def test_the_starter_is_not_changed_by_checking(self):
        before = copy.deepcopy(STARTER)
        problems(STARTER)
        self.assertEqual(STARTER, before)


if __name__ == "__main__":
    unittest.main()
