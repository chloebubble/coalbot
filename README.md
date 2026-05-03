# coalbot

Discord bot that deletes a user's message after it receives enough coal reactions.

## Setup

1. Create a Discord application and bot at <https://discord.com/developers/applications>.
2. Invite it with:
   - `Read Message History`
   - `Manage Messages`
   - `View Channels`
3. Create local config:

```bash
cp config.example.json config.json
```

4. Edit `config.json`.
5. Run:

```bash
uv sync
uv run coalbot
```

## Config

```json
{
  "discord_token": "bot-token",
  "coal_emoji": "123456789012345678",
  "coal_threshold": 3,
  "ignored_channel_ids": []
}
```

`coal_emoji` may be a custom emoji id, a custom emoji mention, or a unicode emoji.

Use another config path with:

```bash
uv run coalbot --config /path/to/config.json
```

## Development

```bash
uv run ruff check .
```

`config.json` is ignored. Commit `config.example.json`, not real tokens.
