# Schemas

Copies of the schemas Hermes UI generates from its models. **Do not edit them here.**

| File | What it describes | Source in hermes-ui |
|---|---|---|
| `widget.schema.json` | A widget's `widget.json` manifest | `backend/schema/widget.schema.json` |
| `catalog-index.schema.json` | `catalog/index.json` | `backend/schema/catalog-index.schema.json` |

Both come from `python -m hermes_ui.widgets.codegen` in hermes-ui. When Hermes UI changes the standard, a maintainer copies
the two files here unchanged, in the same change that relies on them. Last copied from hermes-ui `446e71f`.

The schemas cover the shape. `scripts/check.py` adds the rules a schema can't express, which are the same ones the portal
applies:
- permissions must match the controls;
- a view must exist for `default_size`;
- lists must have unique values;
- the component limits apply.
