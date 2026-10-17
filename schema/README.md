# Schemas

Copies of the schemas Hermes UI generates from its models. **Do not edit them here.**

| File | What it describes | Source in hermes-ui |
|---|---|---|
| `widget.schema.json` | A widget's `widget.json` manifest | `backend/schema/widget.schema.json` |
| `catalog-index.schema.json` | `catalog/index.json` | `backend/schema/catalog-index.schema.json` |

Both come from `python -m hermes_ui.widgets.codegen` in hermes-ui. When Hermes UI changes the standard, a maintainer copies
the two files here unchanged, in the same change that relies on them. Last copied from hermes-ui `440325c` (PR #156, the Timer); updated to its merge commit once merged.

The schemas cover the shape. `scripts/check.py` adds the rules a schema can't express, which are the same ones the portal
applies:
- a version 2 manifest has a `binding`, and version 1 has `device_classes` instead;
- views use only their binding's fields and controls: a device's `device.*` and `state.*`, a data source's `source.*` and
  `source.open`, or a timer's `timer.*` and its buttons and stepper;
- a source needs runtime 2 and a timer runtime 3;
- permissions must match the binding and the controls;
- a view must exist for `default_size`;
- lists must have unique values;
- the component limits apply.

The data sources' fields (`SOURCE_FIELDS` in `scripts/check.py`) are copied from hermes-ui's `SOURCE_PROVIDERS` too.
