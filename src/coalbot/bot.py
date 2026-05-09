from __future__ import annotations

import logging
from pathlib import Path

import discord
from rich.console import Console
from rich.logging import RichHandler

from coalbot.config import Config, load_config

LOGGER = logging.getLogger("coalbot")


class CoalBot(discord.Client):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.reactions = True
        intents.guilds = True
        intents.message_content = config.request_message_content_intent

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

        deleted_content = message.content
        deleted_author = message.author
        deleted_attachment_urls = [attachment.url for attachment in message.attachments]

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
        await self._send_deletion_log(
            author=deleted_author,
            channel_id=payload.channel_id,
            message_id=payload.message_id,
            content=deleted_content,
            content_available=self.config.request_message_content_intent,
            attachment_urls=deleted_attachment_urls,
            coal_count=coal_count,
        )

    def _is_coal_emoji(self, emoji: discord.PartialEmoji | discord.Emoji | str) -> bool:
        configured = self.config.coal_emoji
        if isinstance(emoji, str):
            return emoji == configured
        if emoji.id is not None:
            return str(emoji.id) == configured
        return emoji.name == configured

    async def _send_deletion_log(
        self,
        *,
        author: discord.User | discord.Member,
        channel_id: int,
        message_id: int,
        content: str,
        content_available: bool,
        attachment_urls: list[str],
        coal_count: int,
    ) -> None:
        if self.config.log_channel_id is None:
            return

        log_channel_id = self.config.log_channel_id
        log_channel = self.get_channel(log_channel_id)
        if log_channel is None:
            try:
                log_channel = await self.fetch_channel(log_channel_id)
            except discord.NotFound:
                LOGGER.warning("Configured log channel %s was not found", log_channel_id)
                return
            except discord.Forbidden:
                LOGGER.warning("Missing permission to fetch log channel %s", log_channel_id)
                return

        if not isinstance(log_channel, discord.TextChannel | discord.Thread | discord.VoiceChannel):
            LOGGER.warning("Configured log channel %s is not messageable", log_channel_id)
            return

        embed = discord.Embed(
            title="Coal deletion",
            description=_log_description(content, content_available),
            color=discord.Color.dark_grey(),
        )
        embed.add_field(name="Author", value=f"<@{author.id}> (`{author.id}`)", inline=False)
        embed.add_field(name="Channel", value=f"<#{channel_id}>", inline=True)
        embed.add_field(name="Coal", value=str(coal_count), inline=True)
        embed.add_field(name="Message ID", value=str(message_id), inline=False)
        if attachment_urls:
            embed.add_field(
                name="Attachments",
                value=_truncate("\n".join(attachment_urls)),
                inline=False,
            )

        try:
            await log_channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            LOGGER.warning("Missing permission to send logs to channel %s", log_channel_id)


def _truncate(value: str, limit: int = 1000) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _log_description(content: str, content_available: bool) -> str:
    if content:
        return _truncate(content)
    if content_available:
        return "No text content."
    return "Message content logging disabled."


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(message)s",
        handlers=[
            RichHandler(
                console=Console(stderr=True),
                rich_tracebacks=True,
                show_path=False,
                markup=False,
            )
        ],
        force=True,
    )
    logging.captureWarnings(True)


def run(config_path: str | Path = "config.json") -> None:
    _configure_logging()
    config = load_config(config_path)
    CoalBot(config).run(config.discord_token, log_handler=None)
