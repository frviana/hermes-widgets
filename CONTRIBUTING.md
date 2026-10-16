# Contributing a widget

**Not open yet.** This catalog depends on work still in progress in `hermes-ui`:

- [hermes-ui#119](https://github.com/frviana/hermes-ui/issues/119) — the trust model and sandbox a
  widget runs in (owner decision needed before anything here is final).
- [hermes-ui#120](https://github.com/frviana/hermes-ui/issues/120) — the `widget.json` manifest
  standard a submission must follow.
- [hermes-ui#121](https://github.com/frviana/hermes-ui/issues/121) — the backend that actually
  reads `catalog/index.json` from this repo.
- [hermes-ui#123](https://github.com/frviana/hermes-ui/issues/123) — the sandboxed runtime and SDK
  a widget's code is written against.

Once those land, this file (and `docs/AUTHORING.md`, tracked by
[hermes-ui#126](https://github.com/frviana/hermes-ui/issues/126)) will cover:

1. Building a widget against the manifest and SDK, with a worked example.
2. What a submission PR to `catalog/index.json` must include (a working release, a validating
   manifest, declared permissions that match what the code actually calls).
3. The review checklist before a maintainer merges a listing.
4. How a version bump is submitted and reviewed.

Until then, treat anything in `catalog/` and `schema/` as a draft that will change.
