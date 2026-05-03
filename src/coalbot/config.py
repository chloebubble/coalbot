from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CUSTOM_EMOJI_RE = re.compile(r"^<a?:[^:]+:(?P<id>\d+)>$")


@dataclass(frozen=True)
class Config:
    discord_token: str
    coal_emoji: str
    coal_threshold: int
    ignored_channel_ids: frozenset[int]
    log_channel_id: int | None


def load_config(path: str | Path = "config.json") -> Config:
    config_path = Path(path)
    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Config file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Config file is not valid JSON: {config_path}") from exc

    if not isinstance(raw_config, dict):
        raise RuntimeError("Config file must contain a JSON object")

    token = _required_str(raw_config, "discord_token")
    coal_emoji = _required_str(raw_config, "coal_emoji")
    threshold = _positive_int(raw_config.get("coal_threshold", 3), "coal_threshold")

    return Config(
        discord_token=token,
        coal_emoji=_normalize_emoji(coal_emoji),
        coal_threshold=threshold,
        ignored_channel_ids=_id_set(
            raw_config.get("ignored_channel_ids", []),
            "ignored_channel_ids",
        ),
        log_channel_id=_optional_id(raw_config.get("log_channel_id"), "log_channel_id"),
    )


def _required_str(config: dict[str, Any], name: str) -> str:
    value = config.get(name)
    if not isinstance(value, str):
        raise RuntimeError(f"{name} must be a string")
    value = value.strip()
    if not value:
        raise RuntimeError(f"{name} must be set")
    return value


def _positive_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RuntimeError(f"{name} must be an integer")
    if value < 1:
        raise RuntimeError(f"{name} must be at least 1")
    return value


def _id_set(value: Any, name: str) -> frozenset[int]:
    if value is None:
        return frozenset()

    if not isinstance(value, list):
        raise RuntimeError(f"{name} must be a list of channel ids")

    ids: set[int] = set()
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int | str):
            raise RuntimeError(f"{name} must contain only integers or strings")
        try:
            channel_id = int(item)
        except ValueError as exc:
            raise RuntimeError(f"{name} must contain only valid channel ids") from exc
        if channel_id < 1:
            raise RuntimeError(f"{name} must contain only positive channel ids")
        ids.add(channel_id)
    return frozenset(ids)


def _optional_id(value: Any, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise RuntimeError(f"{name} must be an integer, string, or null")
    try:
        item_id = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a valid id") from exc
    if item_id < 1:
        raise RuntimeError(f"{name} must be a positive id")
    return item_id


def _normalize_emoji(value: str) -> str:
    value = value.strip()
    match = CUSTOM_EMOJI_RE.fullmatch(value)
    if match:
        return match.group("id")
    return value
