from __future__ import annotations

import logging
from pathlib import Path

import discord

from coalbot.config import Config, load_config

LOGGER = logging.getLogger("coalbot")


class CoalBot(discord.Client):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.reactions = True
        intents.guilds = True

        super().__init__(intents=intents)
        self.config = config

    async def on_ready(self) -> None:
        LOGGER.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "unknown")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None:
            return

        if payload.member is not None and payload.member.bot:
            return

        if payload.channel_id in self.config.ignored_channel_ids:
            return

        if not self._is_coal_emoji(payload.emoji):
            return

        channel = self.get_channel(payload.channel_id)
        if channel is None:
            channel = await self.fetch_channel(payload.channel_id)

        if not isinstance(
            channel,
            discord.TextChannel | discord.Thread | discord.VoiceChannel | discord.StageChannel,
        ):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
        except discord.Forbidden:
            LOGGER.warning("Missing permission to fetch message %s", payload.message_id)
            return

        if message.author.bot:
            return

        coal_count = sum(
            reaction.count
            for reaction in message.reactions
            if self._is_coal_emoji(reaction.emoji)
        )

        if coal_count < self.config.coal_threshold:
            return

        try:
            await message.delete()
        except discord.NotFound:
            return
        except discord.Forbidden:
            LOGGER.warning("Missing permission to delete message %s", payload.message_id)
            return

        LOGGER.info(
            "Deleted message %s in channel %s after %s coal reactions (threshold %s)",
            payload.message_id,
            payload.channel_id,
            coal_count,
            self.config.coal_threshold,
        )

    def _is_coal_emoji(self, emoji: discord.PartialEmoji | discord.Emoji | str) -> bool:
        configured = self.config.coal_emoji
        if isinstance(emoji, str):
            return emoji == configured
        if emoji.id is not None:
            return str(emoji.id) == configured
        return emoji.name == configured


def run(config_path: str | Path = "config.json") -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = load_config(config_path)
    CoalBot(config).run(config.discord_token)
