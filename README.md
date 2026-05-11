# coalbot

Discord bot that deletes a user's message after it receives enough coal reactions.

## Setup

1. Create a Discord application and bot at <https://discord.com/developers/applications>.
2. Invite it with:
   - `Read Message History`
   - `Manage Messages`
   - `View Channels`
3. Enable `Message Content Intent` in the Discord Developer Portal.
4. Create local secrets and config:

```bash
cp .env.example .env
cp config.example.json config.json
```

5. Edit `.env` and `config.json`.
6. Run:

```bash
uv sync
uv run coalbot
```

## Config

```json
{
  "coal_emoji": "123456789012345678",
  "coal_threshold": 3,
  "ignored_channel_ids": [],
  "log_channel_id": null
}
```

Set `DISCORD_TOKEN` in `.env`.
`coal_emoji` may be a custom emoji id, a custom emoji mention, or a unicode emoji.
Set `log_channel_id` to a channel id to log deletions.

Use another config path with:

```bash
uv run coalbot --config /path/to/config.json
```

## Development

```bash
uv run ruff check .
```

`.env` and `config.json` are ignored. Commit `.env.example` and `config.example.json`,
not real tokens.
