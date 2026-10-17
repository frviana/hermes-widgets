# Video (`hermes.video`)

One YouTube video: its title and channel, with a button that opens it on YouTube. There's no player and no thumbnail.

- **Gets data from:** YouTube: a video's title and channel (a `source` binding with the `youtube_oembed` provider,
  runtime 2). Hermes UI reads it, never the widget; YouTube sees the host's address and the video's ID, nothing about
  who is watching.
- **Its setting:** a YouTube link or video ID.
- **It can:** open the video on YouTube (`source.open`), in a new tab. It sends nothing to devices.
- **Sizes:** Small and Medium (default).
