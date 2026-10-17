# Listing a widget

How a widget gets into the store, and how it changes after that. How to build one is in [docs/AUTHORING.md](docs/AUTHORING.md).

Every Hermes UI portal reads `catalog/index.json` on `main`. An entry pins a widget to **one commit** and the **SHA-256 of its `widget.json`** at that commit. The portal checks both, validates the manifest again and only then offers it. So listing takes two steps: first the widget is merged, then its merged commit is pinned.

## 1. Submit the widget
Open a pull request that adds `widgets/<name>/`:
- `widget.json`;
- a short `README.md`: what it shows, what it works with, what it can do, and its sizes (copy [the starter's](widgets/simple-switch/README.md)).

CI runs `python3 scripts/check.py`, which must pass. A maintainer reviews it against §3 and merges it.

A widget in **its own repository** (one repository per widget, like HACS) skips this step. Tag a release there, then go to step 2 with that repository's details.

## 2. Pin it in the catalog
After the merge, a second pull request adds the entry. For a widget in this repository:
```sh
git pull
python3 scripts/check.py entry widgets/<name> --tag <name>-v1.0.0
```
This prints the entry: the identity fields copied from the manifest, `repo`, `path`, the merged `commit` and `manifest_sha256`. Add it to `catalog/index.json`'s `widgets`.

CI checks the pin:
- the file exists at that commit on `main`;
- its hash matches;
- id, version, classes and runtime match the entry.

For a widget in another repository, the entry names that `repo`, the full 40-character `commit` of the release and the hash of its `widget.json` (`sha256sum widget.json` at that commit). CI can't read other repositories: the reviewer checks the pin by hand, and every portal checks it again.

Once merged, portals show it within about ten minutes (their catalog cache), or at once with **Check the catalog again**.

## 3. Review checklist
A maintainer merges a widget only when all of these hold:
- [ ] `scripts/check.py` passes, so the portal will accept it.
- [ ] The id is namespaced to its author, and the folder matches it.
- [ ] `device_classes` fit what the widget is for. No sensitive classes; the schema refuses them anyway.
- [ ] What it can do, derived from its views (`permissions`, and the actions an admin will see), matches its description and README. Nothing surprising: a "display" widget has no controls.
- [ ] Text is honest and plain. No impersonation of Hermes UI or of other authors, and no misleading names.
- [ ] A licence is stated (`license`).
- [ ] It looks right at every size it declares, light and dark, in a dev portal (docs/AUTHORING.md §7).
- [ ] The pin (step 2) points at the reviewed commit.

A rejected submission gets the reasons in the pull request and can be resubmitted.

## 4. New versions
1. Change `widget.json` and raise its `version`.
2. Submit and review as in step 1. Pay attention to any change in what it can do.
3. Pin the new commit as in step 2. The entry keeps its `id`; `version`, `commit` and `manifest_sha256` change.

Portals show installed copies as **Update** in the Store tab. Admins review the new version, including any new actions, before updating. Nothing updates automatically.

## 5. Taking a widget down
Removing its entry from `catalog/index.json` stops new installs at once. Installed copies keep working until an admin removes them: the Store tab shows them as "no longer listed". For a widget with a problem, say so in the pull request and the release notes, so admins know to remove it. Hermes UI has no remote kill switch in this version.
