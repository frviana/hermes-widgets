#!/usr/bin/env python3
"""Check this catalog the way Hermes UI's portal will, before anything is merged (docs/AUTHORING.md).

    python3 scripts/check.py                     check every widget and the catalog index (CI runs this)
    python3 scripts/check.py entry widgets/NAME  print the index entry for a widget, pinned to its last commit
    python3 scripts/check.py dev-catalog DIR     write a local catalog of every widget in the working tree, for a
                                                 Hermes UI dev portal (HERMES_UI_WIDGETS_CATALOG_DIR=DIR)

Needs Python 3.10+ and ``jsonschema`` (pip install jsonschema). The schemas in schema/ are copies of
hermes-ui's generated ones (schema/README.md); this script adds the rules a schema can't express, the same
ones the portal applies (hermes-ui backend/hermes_ui/widgets/manifest.py and catalog.py). The portal checks
everything again on its side: passing here is required, not sufficient.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    sys.exit("check.py needs jsonschema: pip install jsonschema")

ROOT = Path(__file__).resolve().parents[1]
REPO = "frviana/hermes-widgets"
MAX_MANIFEST_BYTES = 32 * 1024
MAX_NODES = 60
MAX_DEPTH = 6
CONTROLS = {"toggle", "slider", "stepper", "choice", "button"}
# What each binding's views may use (hermes-ui ADR 0010): the fields of a data source's provider, the timer's
# fields and controls, and the actions that are the host's own rather than device commands.
SOURCE_FIELDS = {"youtube_oembed": {"source.title", "source.channel"}}
SOURCE_OPENS = {"youtube_oembed"}
TIMER_FIELDS = {"timer.remaining", "timer.duration", "timer.running", "timer.finished"}
TIMER_ACTIONS = {"timer.start", "timer.pause", "timer.reset"}
LOCAL_ACTIONS = {"source.open", *TIMER_ACTIONS}


def load(raw: bytes) -> Any:
    def refuse(name: str):
        raise ValueError(f"{name} is not valid JSON")
    return json.loads(raw, parse_constant=refuse)


def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads((ROOT / "schema" / name).read_text()))


def _walk(node: dict, depth: int, found: dict) -> None:
    if depth > MAX_DEPTH:
        found["errors"].append(f"components are nested more than {MAX_DEPTH} deep")
        return
    found["count"] += 1
    found["nodes"].append(node)
    for child in node.get("children", ()):
        _walk(child, depth + 1, found)


def binding_of(manifest: dict) -> dict:
    """What the widget is tied to: version 1 is always a device."""
    return manifest.get("binding") or {"kind": "device", "device_classes": manifest.get("device_classes") or []}


def classes_of(manifest: dict) -> list[str]:
    b = binding_of(manifest)
    return list(b["device_classes"]) if b["kind"] == "device" else []


def _binding_problems(manifest: dict, nodes: list[dict]) -> list[str]:
    """Views use only their binding's fields and controls, and permissions say exactly that (the portal's rules)."""
    b = binding_of(manifest)
    kind, timer = b["kind"], bool(b.get("timer"))
    runtime = manifest["runtime"]["version"]
    errors = []
    if kind == "source" and runtime < 2:
        errors.append("a source binding needs runtime version 2")
    if timer and runtime < 3:
        errors.append("a timer needs runtime version 3")
    if timer and b["timer"]["default_duration_s"] > b["timer"]["max_duration_s"]:
        errors.append("default_duration_s can't be more than max_duration_s")
    allowed = (SOURCE_FIELDS.get(b.get("provider"), set()) if kind == "source" else TIMER_FIELDS if timer
               else set() if kind == "none" else None)   # None: a device's device.* and state.*
    commands = set()
    for node in nodes:
        timer_control = ((node["kind"] == "button" and node.get("action") in TIMER_ACTIONS)
                         or (node["kind"] == "stepper" and node.get("field") == "timer.duration"))
        if (node["kind"] == "timer" or timer_control) and not timer:
            errors.append(f"{node.get('action') or node.get('field') or 'the timer component'} needs a none binding with a timer")
        when = node.get("when") or {}
        for field in filter(None, (node.get("field"), when.get("field"))):
            ok = field.startswith(("device.", "state.")) if allowed is None else field in allowed
            if not ok:
                errors.append(f"field {field!r} isn't available to a {kind} binding")
        if "has" in when and kind != "device":
            errors.append("a 'has' condition needs a device binding")
        if node["kind"] in CONTROLS:
            action = node.get("action")
            if kind == "device" and action == "source.open":
                errors.append("'source.open' needs a source binding")
            elif kind == "source" and not (action == "source.open" and b.get("provider") in SOURCE_OPENS):
                errors.append("a source binding can't have this control")
            elif kind == "none" and not (timer and timer_control):
                errors.append("a none binding can't have this control")
            elif kind == "device" and action not in LOCAL_ACTIONS:
                commands.add(node["kind"])
    perms = set(manifest["permissions"])
    if kind == "device":
        if "device:read" not in perms or "source:read" in perms:
            errors.append("a device widget's permissions are 'device:read', plus 'device:command' with controls")
        elif bool(commands) != ("device:command" in perms):
            errors.append("permissions must include 'device:command' exactly when a view has a control")
    elif kind == "source" and perms != {"source:read"}:
        errors.append("a source widget's permissions are exactly ['source:read']")
    elif kind == "none" and perms:
        errors.append("a widget tied to nothing has no permissions")
    return list(dict.fromkeys(errors))


def manifest_problems(raw: bytes) -> tuple[dict | None, list[str]]:
    """The manifest, and everything wrong with it (the schema, then the portal's own rules)."""
    if len(raw) > MAX_MANIFEST_BYTES:
        return None, [f"widget.json is over {MAX_MANIFEST_BYTES // 1024} KiB"]
    try:
        manifest = load(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        return None, [f"not valid JSON: {exc}"]
    errors = [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message[:200]}"
              for e in sorted(validator("widget.schema.json").iter_errors(manifest), key=lambda e: list(e.absolute_path))]
    if errors:
        return manifest, errors[:10]
    if manifest["manifest_version"] == 1 and ("binding" in manifest or "device_classes" not in manifest):
        errors.append("manifest version 1 has device_classes and no binding")
    if manifest["manifest_version"] == 2 and ("binding" not in manifest or "device_classes" in manifest):
        errors.append("manifest version 2 has a binding; device_classes goes inside a device binding")
    views = {size: view for size, view in manifest["views"].items() if view is not None}
    if not views:
        errors.append("views needs at least one size (s, m or l)")
    if manifest["default_size"] not in views:
        errors.append(f"default_size {manifest['default_size']!r} has no view")
    nodes: list[dict] = []
    for size, view in views.items():
        found = {"count": 0, "nodes": [], "errors": []}
        _walk(view, 1, found)
        errors += found["errors"]
        if found["count"] > MAX_NODES:
            errors.append(f"views.{size} has {found['count']} components; the limit is {MAX_NODES}")
        nodes += found["nodes"]
    for key, values in (("device_classes", classes_of(manifest)), ("permissions", manifest["permissions"])):
        if len(set(values)) != len(values):
            errors.append(f"{key}: values must be unique")
    if not errors:
        errors += _binding_problems(manifest, nodes)
    return manifest, errors


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout.strip()


def at_commit(commit: str, path: str) -> bytes | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], check=True, capture_output=True).stdout
    except subprocess.CalledProcessError:
        return None


def entry_for(folder: Path, commit: str | None = None, tag: str | None = None) -> dict:
    path = folder.resolve().relative_to(ROOT).as_posix()
    file = f"{path}/widget.json"
    commit = commit or git("log", "-1", "--format=%H", "--", file)
    if not commit:
        raise SystemExit(f"{file} has no commit yet: merge it first, then pin it in catalog/index.json")
    raw = at_commit(commit, file)
    if raw is None:
        raise SystemExit(f"{file} is not in commit {commit[:12]}")
    if raw != (ROOT / file).read_bytes():
        raise SystemExit(f"{file} has changed since {commit[:12]}: commit and merge it, then pin the new commit")
    manifest, errors = manifest_problems(raw)
    if errors:
        raise SystemExit(f"{file} is not valid:\n  " + "\n  ".join(errors))
    entry = {key: manifest[key] for key in ("id", "name", "author", "description", "version", "icon")}
    entry |= {"device_classes": classes_of(manifest), "runtime": manifest["runtime"], "repo": REPO, "path": path, "commit": commit, "manifest_sha256": hashlib.sha256(raw).hexdigest()}
    if tag:
        entry["tag"] = tag
    return entry


def check() -> int:
    problems: list[str] = []
    for file in sorted((ROOT / "widgets").glob("*/widget.json")):
        manifest, errors = manifest_problems(file.read_bytes())
        rel = file.relative_to(ROOT)
        problems += [f"{rel}: {e}" for e in errors]
        if manifest and not errors and manifest["id"].split(".", 1)[1] != file.parent.name:
            problems.append(f"{rel}: the folder should be named after the id's second part ({manifest['id'].split('.', 1)[1]})")

    index_file = ROOT / "catalog" / "index.json"
    try:
        index = load(index_file.read_bytes())
    except ValueError as exc:
        problems.append(f"catalog/index.json: {exc}")
        index = None
    if index is not None:
        problems += [f"catalog/index.json: {'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message[:200]}"
                     for e in validator("catalog-index.schema.json").iter_errors(index)]
        seen: set[str] = set()
        for entry in index.get("widgets", []) if isinstance(index, dict) else []:
            if not isinstance(entry, dict) or "id" not in entry:
                continue
            where = f"catalog/index.json: {entry['id']}"
            if entry["id"] in seen:
                problems.append(f"{where}: listed twice")
            seen.add(entry["id"])
            if entry.get("repo") != REPO:
                continue  # another repository: the portal checks it when it reads the catalog
            raw = at_commit(entry.get("commit", ""), f"{entry['path']}/widget.json" if entry.get("path") else "widget.json")
            if raw is None:
                problems.append(f"{where}: widget.json is not at {entry.get('path')!r} in commit {str(entry.get('commit'))[:12]}")
                continue
            if hashlib.sha256(raw).hexdigest() != entry.get("manifest_sha256"):
                problems.append(f"{where}: manifest_sha256 does not match widget.json at that commit")
            manifest, errors = manifest_problems(raw)
            problems += [f"{where} (at its commit): {e}" for e in errors]
            if manifest and not errors:
                for key in ("id", "version", "runtime"):
                    if manifest[key] != entry.get(key):
                        problems.append(f"{where}: {key} differs from the manifest's")
                if sorted(classes_of(manifest)) != sorted(entry.get("device_classes", [])):
                    problems.append(f"{where}: device_classes differ from the manifest's")
            branch = "origin/main" if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "-q", "origin/main"],
                                                     capture_output=True).returncode == 0 else "HEAD"
            if subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", entry["commit"], branch],
                              capture_output=True).returncode != 0:
                problems.append(f"{where}: commit {entry['commit'][:12]} is not on {branch}; pin a merged commit")

    for p in problems:
        print(p, file=sys.stderr)
    print(f"{'FAIL' if problems else 'OK'}: {len(list((ROOT / 'widgets').glob('*/widget.json')))} widget(s), "
          f"{len((index or {}).get('widgets', [])) if isinstance(index, dict) else 0} listed")
    return 1 if problems else 0


def dev_catalog(out: Path) -> int:
    """Every valid widget in the working tree, listed with its current hash (commit unchecked locally)."""
    if out.exists() and any(out.iterdir()) and not (out / "catalog" / "index.json").exists():
        raise SystemExit(f"{out} is not empty and not a catalog: choose another folder")
    shutil.rmtree(out, ignore_errors=True)
    entries = []
    for file in sorted((ROOT / "widgets").glob("*/widget.json")):
        raw = file.read_bytes()
        manifest, errors = manifest_problems(raw)
        if errors:
            print(f"skipped {file.relative_to(ROOT)}: {errors[0]}", file=sys.stderr)
            continue
        target = out / "widgets" / file.parent.name / "widget.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        entries.append({key: manifest[key] for key in ("id", "name", "author", "description", "version", "icon")}
                       | {"device_classes": classes_of(manifest), "runtime": manifest["runtime"], "repo": REPO, "path": f"widgets/{file.parent.name}", "commit": "0" * 40,
                          "manifest_sha256": hashlib.sha256(raw).hexdigest()})
    (out / "catalog").mkdir(parents=True, exist_ok=True)
    (out / "catalog" / "index.json").write_text(json.dumps({"catalog_version": 1, "widgets": entries}, indent=2) + "\n")
    print(f"wrote {len(entries)} widget(s) to {out}; start a Hermes UI dev portal with HERMES_UI_WIDGETS_CATALOG_DIR={out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")
    e = sub.add_parser("entry", help="print a widget's catalog entry, pinned to its last commit")
    e.add_argument("folder", type=Path)
    e.add_argument("--commit")
    e.add_argument("--tag")
    d = sub.add_parser("dev-catalog", help="write a local catalog for a Hermes UI dev portal")
    d.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "entry":
        print(json.dumps(entry_for(args.folder, args.commit, args.tag), indent=2))
        return 0
    if args.command == "dev-catalog":
        return dev_catalog(args.out)
    return check()


if __name__ == "__main__":
    sys.exit(main())
