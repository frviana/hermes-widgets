# hermes-widgets

The widget store for [Hermes UI](https://github.com/frviana/hermes-ui)'s dashboard. This repository holds the catalog of widgets an admin can install from the dashboard's **Store** tab, without rebuilding or redeploying Hermes UI.

It plays the role [HACS](https://hacs.xyz/)'s default list plays for Home Assistant:
- **The catalog**, `catalog/index.json`: every listed widget, each pinned to a commit and to the SHA-256 of its manifest.
- **The widgets** themselves: one folder each in `widgets/` while the catalog is small, or their own repositories later.
- **Review:** every listing is a reviewed pull request.

## How it works
- **Widgets are declarative.** A widget is one `widget.json`: a view made of Hermes UI's own components, bound to one device the admin picks ([hermes-ui ADR 0008](https://github.com/frviana/hermes-ui/blob/main/docs/decisions/0008-installed-widgets-declarative-first.md)). It runs no code, loads no styles or images, can't reach the network and can't see other devices. Hermes UI builds every command itself, for the assigned device only, and shows the real outcome.
- **The portal reads this catalog server-side.** The browser never contacts GitHub.
  - The portal checks each widget's pinned commit and hash and validates its manifest again.
  - Anything that fails is left out of the store, with a reason.
  - Admins review exactly what a widget can do, in plain words, before installing or updating it.
- **Installed widgets keep working if this repository changes.** Portals store the exact bytes that were reviewed. A new version shows up as **Update**, never as an automatic change.

## Layout
```
catalog/index.json      the listing every portal reads (pinned entries)
widgets/<name>/         one widget: widget.json and a README
schema/                 JSON Schemas for widget.json and the index (copies from hermes-ui; do not edit)
scripts/check.py        the portal's checks, for authors and CI; also prints entries and builds a dev catalog
docs/AUTHORING.md       building a widget, step by step
CONTRIBUTING.md         submitting, pinning, reviewing, new versions, taking a widget down
```

## Building and listing a widget
- **Build it:** [docs/AUTHORING.md](docs/AUTHORING.md) works through the starter widget, [`widgets/simple-switch`](widgets/simple-switch/).
- **Check it:** `pip install jsonschema && python3 scripts/check.py`.
- **List it:** [CONTRIBUTING.md](CONTRIBUTING.md). Submit the widget, then pin its merged commit in the catalog. The review checklist is in §3.

## Configuring a portal
Hermes UI reads `frviana/hermes-widgets` at `main` by default (`HERMES_UI_WIDGETS_CATALOG_REPO`, `…_REF`). While this repository is private, the portal needs a read-only token (fine-grained, *Contents: read*, this repository only) in a 0600 file named by `HERMES_UI_WIDGETS_GITHUB_TOKEN_FILE`. Details are in hermes-ui's `docs/smart-home/WIDGET_STORE.md`.

## License
Private, all rights reserved. Not for redistribution. A listed widget states its own licence in its manifest.
