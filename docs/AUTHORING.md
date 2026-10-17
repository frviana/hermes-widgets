# Building a widget for Hermes UI

This guide builds a widget from scratch, checks it, tries it in a Hermes UI dev portal and gets it ready to list. The worked example is [`widgets/simple-switch`](../widgets/simple-switch/widget.json), the starter widget: one switch or plug with a toggle. Submitting is in [CONTRIBUTING.md](../CONTRIBUTING.md).

## 1. What a store widget is
A store widget is **one file, `widget.json`**: data, not code. It describes a view made of Hermes UI's own components (text, values, toggles, sliders…). Hermes UI draws that view, bound to **one device** that the person adding the widget picks from the device classes you name.

That is the trust model ([hermes-ui ADR 0008](https://github.com/frviana/hermes-ui/blob/main/docs/decisions/0008-installed-widgets-declarative-first.md)). A widget:
- **can't** run code, load styles, fonts or images, reach the network, see other devices or other widgets, or use voice;
- **can't** target a lock, garage door, gate, alarm or camera;
- **can't** build its own commands. A control hands a value to Hermes UI, which sends the command for the assigned device as the person using the dashboard, with their permissions, and shows the real outcome: pending, then confirmed, failed or not confirmed.

Listing here is a first filter: a maintainer reviews every submission. The real boundary is that nothing in a widget is executed.

## 2. Start from the starter
```sh
cp -r widgets/simple-switch widgets/porch-switch
```
The folder is named after the second part of your widget's id (`yourname.porch-switch` → `widgets/porch-switch`).

## 3. Identity
```json
{
  "$schema": "../../schema/widget.schema.json",
  "manifest_version": 1,
  "id": "yourname.porch-switch",
  "name": "Porch switch",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "The porch light's switch, big enough to hit from the doorway.",
  "license": "MIT",
  "icon": "bolt",
  "tint": "green",
  "runtime": { "kind": "declarative", "version": 1 },
```
- **`id`:** `author.widget-name`, lowercase letters, digits and hyphens. Never change it after listing: dashboards refer to it.
- **`version`:** semantic versioning, raised with every change you submit.
- **`name`, `author`, `description`:** plain text, with no line breaks.
- **`license`:** an SPDX identifier. The review asks for one.
- **`icon`:** one of `bolt`, `box`, `bulb`, `check`, `clock`, `fan`, `home`, `leaf`, `minus`, `music`, `pause`, `play`, `plus`, `sparkles`, `speaker`, `sun` or `thermo`.
- **`tint`:** one of `blue`, `red`, `orange`, `amber`, `pink`, `violet`, `indigo`, `green`, `teal`, `yellow` or `brown`.
- **`runtime`:** the lowest declarative runtime your views need. Version 1 is everything in this guide except a data source (version 2) and a timer (version 3), below.

## 4. Devices and permissions
```json
  "device_classes": ["switch", "plug"],
  "permissions": ["device:read", "device:command"],
  "default_size": "s",
```
- **`device_classes`:** what the device picker offers (1 to 4 of `light`, `switch`, `plug`, `fan`, `sensor`, `thermostat`, `cover`, `media_player`, `other`). Each widget instance gets one device.
- **`permissions`:** `device:read` always; add `device:command` only if a view has a control. Asking for more than the views use is refused. Admins see what the widget can do, worked out from your views, before they install it, for example "Turn on and off".

### Widgets that aren't tied to a device
Manifest version 2 says what a widget is tied to with a **`binding`** instead of `device_classes` ([hermes-ui ADR 0010](https://github.com/frviana/hermes-ui/blob/main/docs/decisions/0010-widget-bindings-beyond-devices.md)). The starter is version 1, which Hermes UI still reads as a device widget.

| `binding` | `permissions` | Views can use | Example |
|---|---|---|---|
| `{"kind": "device", "device_classes": ["switch", "plug"]}` | as above | `device.*`, `state.*` and device controls | the starter, as version 2 |
| `{"kind": "source", "provider": "youtube_oembed"}` (runtime 2) | `["source:read"]` | `source.title`, `source.channel`, and a `button` with `source.open` | [`widgets/video`](../widgets/video/widget.json) |
| `{"kind": "none", "timer": {"default_duration_s": 300, "max_duration_s": 7200, "chime": "bell"}}` (runtime 3) | `[]` | the `timer` component, `timer.remaining`, `timer.duration`, `timer.running`, `timer.finished`, buttons `timer.start`, `timer.pause`, `timer.reset`, and a `stepper` on `timer.duration` | [`widgets/timer`](../widgets/timer/widget.json) |
| `{"kind": "none"}` | `[]` | fixed text and icons only | |

A data source is code in Hermes UI: a widget only names one, never a URL. Hermes UI makes the calls, and the person adding the widget fills in the source's settings (for YouTube, a link or a video ID). A timer is Hermes UI's too: it keeps the time, plays the chime (`bell`, `chime` or `beep`) and shows the notification. The full rules are in Hermes UI's `docs/smart-home/WIDGET_STANDARD.md`.

## 5. Views
One view per dashboard size you support (`s`, `m`, `l`). A view is a tree of components. The starter's Small view:

```json
  "views": {
    "s": {
      "kind": "stack",
      "children": [
        { "kind": "value", "field": "device.name", "style": "title" },
        { "kind": "spacer" },
        { "kind": "row", "justify": "between", "children": [
          { "kind": "value", "field": "state.on", "style": "display" },
          { "kind": "toggle", "field": "state.on" }
        ] },
        { "kind": "status" }
      ]
    },
```
Reading top to bottom: the device's name; a spacer that pushes the rest to the bottom; a row with "On" or "Off" in large type and a toggle; and the status line. The status line is where Hermes UI says "Turning it off…", "Couldn't turn it on: …" or "Porch Light is offline".

The Medium view (see the [file](../widgets/simple-switch/widget.json)) adds an icon, the room shown only when the device has one, and when it last reported:
```json
{ "kind": "value", "field": "device.room", "style": "caption", "when": { "field": "device.room", "op": "ne", "value": null } }
{ "kind": "value", "field": "state.updated_at", "label": "Updated", "style": "caption" }
```

### Components
| `kind` | Fields | |
|---|---|---|
| `stack` / `row` | `children`, `gap` (`none` `s` `m` `l`); stack `align` (`start` `center` `end` `stretch`); row `justify` (`start` `center` `end` `between`) and `align` (`start` `center` `end` `baseline`) | Top to bottom / left to right |
| `spacer` | | Takes the free space |
| `text` | `text`, `style` | Fixed text |
| `value` | `field`, `style`, `label` | A device field, formatted by Hermes UI; `--` when not reported |
| `icon` | `name`, `tint` | |
| `status` | | Offline, connection down, and the last change's outcome. Added at the end if you leave it out |
| `toggle` | `field`: `state.on` or `state.muted`; `label` | |
| `slider` | `field`: `state.brightness`, `state.volume`, `state.position` or `state.color_temp_kelvin`; `label` | Within the device's own range |
| `stepper` | `field`: `state.target_temperature`; `label` | − and + on the device's own step |
| `choice` | `field`: `state.thermostat_mode`; `label` | The device's own modes |
| `button` | `action`, `label`, `icon` | `on_off.turn_on`/`turn_off`, `media_player.play`/`pause`/`stop`/`next`/`previous`, `cover.open`/`close`/`stop` |

`style` is `display` (the big number), `title`, `body` or `caption`. Controls show only when the assigned device can do them: a brightness slider never appears for a light without brightness.

### Fields
- **Device:** `device.name`, `device.room`, `device.availability`.
- **State:**
  - `state.on`, `state.brightness`, `state.color_mode`, `state.hue`, `state.saturation`, `state.color_temp_kelvin`;
  - `state.temperature`, `state.humidity`, `state.contact_open`, `state.motion`;
  - `state.current_temperature`, `state.target_temperature`, `state.thermostat_mode`, `state.hvac_action`;
  - `state.position`, `state.cover_state`;
  - `state.playback`, `state.volume`, `state.muted`, `state.media_title`, `state.media_artist`;
  - `state.updated_at`.

Hermes UI formats each one: units come from the device (°C or °F), percentages, "On"/"Off", "Heating", "3 min ago".

### Conditions
Any component can carry `when`:
- `{ "field": …, "op": "eq" | "ne", "value": … }` compares one field with a constant (`null` means "not reported");
- `{ "has": "brightness" }` checks that the device has a capability.

### Limits
A manifest is at most 32 KiB. A view has at most 60 components, nested at most 6 deep.

The JSON Schema in [`schema/widget.schema.json`](../schema/widget.schema.json) is the authority. Point your editor at it with the `$schema` line.

## 6. Check it
```sh
pip install jsonschema
python3 scripts/check.py
```
This runs the checks Hermes UI's portal applies: the schema, permissions against controls, a view for `default_size`, unique values and the limits. CI runs the same script on every pull request.

## 7. Try it in Hermes UI
With a checkout of Hermes UI, its simulator portal and the fake smart home connector (invented devices) can install your widget from a local catalog:
```sh
python3 scripts/check.py dev-catalog /tmp/my-widgets
```
Then start the Hermes UI dev portal (its `docs/DEV_ENVIRONMENT.md`) with `HERMES_UI_WIDGETS_CATALOG_DIR=/tmp/my-widgets`.
1. Sign in as the dev admin.
2. Choose **Edit**, then **Add widget**, then **Store**.
3. Review your widget and install it.
4. Add it from the **Widgets** tab and pick a device.

Hermes UI's dev preview (`/preview.html?installed=1`) shows how its example widgets look in every state, for comparison.

## 8. Submit
See [CONTRIBUTING.md](../CONTRIBUTING.md): a pull request with your widget folder; then, once it is merged, its pinned entry in `catalog/index.json`.
