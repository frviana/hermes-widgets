"""Tests for scripts/check.py: python3 -m unittest discover -s scripts (CI runs this)."""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402

STARTER = json.loads((check.ROOT / "widgets" / "simple-switch" / "widget.json").read_text())
TIMER = json.loads((check.ROOT / "widgets" / "timer" / "widget.json").read_text())
VIDEO = json.loads((check.ROOT / "widgets" / "video" / "widget.json").read_text())


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

    def test_the_bindings_of_manifest_version_2(self):
        self.assertEqual(problems(TIMER), [])
        self.assertEqual(problems(VIDEO), [])
        self.assertEqual(check.classes_of(STARTER), ["switch", "plug"])
        self.assertEqual(check.classes_of(TIMER), [])
        device = {**STARTER, "manifest_version": 2, "binding": {"kind": "device", "device_classes": ["switch"]}}
        del device["device_classes"]
        self.assertEqual(problems(device), [])
        self.assertIn("manifest version 2 has a binding; device_classes goes inside a device binding",
                      problems({**device, "device_classes": ["switch"]}))
        self.assertIn("manifest version 1 has device_classes and no binding", problems({**STARTER, "binding": TIMER["binding"]}))

    def test_views_use_only_their_bindings_fields_and_controls(self):
        plain = {**TIMER, "binding": {"kind": "none"}}
        cases = [
            ({**plain, "views": {"s": {"kind": "timer"}}}, "the timer component needs a none binding with a timer"),
            ({**TIMER, "views": {"s": {"kind": "value", "field": "state.on"}}}, "field 'state.on' isn't available to a none binding"),
            ({**TIMER, "views": {"s": {"kind": "toggle", "field": "state.on"}}}, "a none binding can't have this control"),
            ({**VIDEO, "default_size": "s", "views": {"s": {"kind": "value", "field": "timer.remaining"}}}, "field 'timer.remaining' isn't available to a source binding"),
            ({**VIDEO, "default_size": "s", "views": {"s": {"kind": "text", "text": "Hi", "when": {"has": "on_off"}}}}, "a 'has' condition needs a device binding"),
            ({**STARTER, "views": {"s": {"kind": "button", "action": "source.open", "label": "Open"}}}, "'source.open' needs a source binding"),
            ({**TIMER, "runtime": {"kind": "declarative", "version": 2}}, "a timer needs runtime version 3"),
            ({**VIDEO, "runtime": {"kind": "declarative", "version": 1}}, "a source binding needs runtime version 2"),
            ({**TIMER, "binding": {"kind": "none", "timer": {"default_duration_s": 900, "max_duration_s": 600}}},
             "default_duration_s can't be more than max_duration_s"),
        ]
        for manifest, says in cases:
            with self.subTest(says=says):
                self.assertIn(says, problems(manifest))

    def test_permissions_follow_the_binding(self):
        self.assertIn("a widget tied to nothing has no permissions", problems({**TIMER, "permissions": ["device:read"]}))
        self.assertIn("a source widget's permissions are exactly ['source:read']", problems({**VIDEO, "permissions": []}))
        self.assertTrue(problems({**TIMER, "binding": {"kind": "none", "timer": {**TIMER["binding"]["timer"], "chime": "https://example.invalid/a.mp3"}}}))
        self.assertTrue(problems({**VIDEO, "binding": {"kind": "source", "provider": "https://example.invalid/feed"}}))

    def test_the_starter_is_not_changed_by_checking(self):
        before = copy.deepcopy(STARTER)
        problems(STARTER)
        self.assertEqual(STARTER, before)


if __name__ == "__main__":
    unittest.main()
