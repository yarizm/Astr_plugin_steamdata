from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

DEFAULT_STEAM_API_KEY = ""
DEFAULT_PRICE_REGION = "cn"
DEFAULT_REVIEW_COUNT = 5
DEFAULT_REQUEST_TIMEOUT = 15
DEFAULT_ENABLE_FALLBACK_COMMANDS = True


@dataclass(frozen=True)
class SteamPluginConfig:
    steam_api_key: str = DEFAULT_STEAM_API_KEY
    price_region: str = DEFAULT_PRICE_REGION
    review_count: int = DEFAULT_REVIEW_COUNT
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT
    enable_fallback_commands: bool = DEFAULT_ENABLE_FALLBACK_COMMANDS


def normalize_config(config: Mapping[str, Any] | None) -> SteamPluginConfig:
    config = config or {}
    return SteamPluginConfig(
        steam_api_key=str(config.get("steam_api_key") or "").strip(),
        price_region=_normalize_region(config.get("price_region")),
        review_count=_coerce_int(config.get("review_count"), DEFAULT_REVIEW_COUNT, minimum=1, maximum=50),
        request_timeout=_coerce_int(config.get("request_timeout"), DEFAULT_REQUEST_TIMEOUT, minimum=3, maximum=60),
        enable_fallback_commands=_coerce_bool(
            config.get("enable_fallback_commands"),
            DEFAULT_ENABLE_FALLBACK_COMMANDS,
        ),
    )


def _normalize_region(value: Any) -> str:
    if not isinstance(value, str):
        return DEFAULT_PRICE_REGION
    value = value.strip().lower()
    if not value:
        return DEFAULT_PRICE_REGION
    return value[:2]


def _coerce_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(result, minimum), maximum)


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    return default
