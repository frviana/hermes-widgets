# hermes-widgets

The widget store for [Hermes UI](https://github.com/frviana/hermes-ui)'s dashboard: a catalog of
installable widgets that can be added to the dashboard **without rebuilding or redeploying the
portal**, alongside the widgets that ship built into the app.

This repository is the development-phase **catalog** — the index Hermes UI's portal backend reads
to know which widgets exist, where to fetch each one from, and at which pinned release. It plays
the same role [HACS](https://hacs.xyz/)'s default-repositories list plays for Home Assistant: one
widget per repository (or per entry here while the catalog is small), each with its own manifest
and versioned releases, reviewed before being listed.

**Status: planning.** Tracked by [hermes-ui#118](https://github.com/frviana/hermes-ui/issues/118)
(epic) and its sub-issues. Nothing here is installable yet — the trust/sandbox model
([#119](https://github.com/frviana/hermes-ui/issues/119)) and the manifest standard
([#120](https://github.com/frviana/hermes-ui/issues/120)) need an owner decision and an
implementation in `hermes-ui` before this catalog's format is final. The structure below is a
starting point, not a frozen contract.

## How this fits together

| Piece | Lives in | Tracked by |
|---|---|---|
| Trust model and sandbox (iframe + scoped SDK) | `hermes-ui` (portal + frontend) | [#119](https://github.com/frviana/hermes-ui/issues/119) |
| Widget manifest standard (`widget.json`) | Documented here and in `hermes-ui` docs | [#120](https://github.com/frviana/hermes-ui/issues/120) |
| Catalog fetch, cache, validation | `hermes-ui` backend reads **this repo** | [#121](https://github.com/frviana/hermes-ui/issues/121) |
| Install / update / remove UI | `hermes-ui` frontend + backend | [#122](https://github.com/frviana/hermes-ui/issues/122) |
| Sandboxed runtime widgets execute in | `hermes-ui` frontend | [#123](https://github.com/frviana/hermes-ui/issues/123) |
| Installed-widget storage and admin API | `hermes-ui` backend | [#124](https://github.com/frviana/hermes-ui/issues/124) |
| Built-in widget catalog (ships with the app, no store needed) | `hermes-ui` frontend | [#125](https://github.com/frviana/hermes-ui/issues/125) |
| Author guide and submission process for this repo | Documented here | [#126](https://github.com/frviana/hermes-ui/issues/126) |

## Repository layout

```
catalog/        The index Hermes UI's backend fetches: catalog/index.json
                 lists every available widget, its repo/release and identity
                 fields. One entry per widget while the catalog is small;
                 may move to one-repo-per-widget as it grows (HACS's model).
widgets/        Each widget's own folder: its widget.json manifest, source,
                 and built bundle for a release (added as the first real
                 widgets are built, once #119/#120 land).
schema/         JSON Schema for widget.json and for catalog/index.json, so
                 hermes-ui and anyone authoring a widget validate the same
                 shape. Placeholder until #120 is decided.
docs/           Author-facing documentation: how to build, package and
                 submit a widget (#126), and the standard itself (#120).
```

## Device-assignment standard

Every widget that targets a device type (thermostat, light, switch, …) follows the same pattern
Hermes UI's own built-in widgets use — a device picker scoped to the device class, generic
`/api/home/*` routes for state and commands, and display/limits derived from the device's own
capability descriptor, never hardcoded to one gateway. See
[`docs/smart-home/ARCHITECTURE.md` §8](https://github.com/frviana/hermes-ui/blob/main/docs/smart-home/ARCHITECTURE.md)
in `hermes-ui` for the full standard. A widget built this way works against Home Assistant today
and any other connected gateway later, with no widget-side change.

## Security model (summary)

Widgets from this catalog are **not trusted the way built-in widgets are**. The plan
([#119](https://github.com/frviana/hermes-ui/issues/119)) is for installed widgets to run inside a
sandboxed iframe with a narrow, versioned `postMessage` SDK that can only read and command the
specific device(s) a widget instance was assigned — never the full dashboard session, never other
devices, never voice. Listing in this catalog is a first filter (manifest validation, a maintainer
review of the submission), not the security boundary; the sandbox is.

## Contributing a widget

Not open yet — the manifest standard and sandbox SDK it must be written against don't exist yet.
Once [#120](https://github.com/frviana/hermes-ui/issues/120) and
[#123](https://github.com/frviana/hermes-ui/issues/123) land, `docs/AUTHORING.md` (tracked by
[#126](https://github.com/frviana/hermes-ui/issues/126)) will cover the full process: building a
widget against the manifest and SDK, and submitting it here for listing.

## License

Private, all rights reserved. Not for redistribution.
