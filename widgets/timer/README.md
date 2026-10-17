# Timer (`hermes.timer`)

A kitchen timer. Set how long it runs, start it, pause it or reset it. When it's done, the tile says so, the page plays a
bell and, if it isn't in front, shows a notification. Hermes UI keeps the timer, so it shows the same time on every
screen and after a reload.

- **Works with:** nothing: it isn't tied to a device (a `none` binding with a timer, runtime 3).
- **It can:** start, pause and reset its timer, and set how long it runs (`timer.start`, `timer.pause`, `timer.reset`,
  `timer.set`). These never reach a device, and it has no permissions.
- **Timer:** 5 minutes when added, up to 2 hours, with the bell.
- **Sizes:** Small (default: the countdown, Start or Pause, and Reset) and Medium (adds "Done!" and the duration stepper).
