from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OwnedGame:
    appid: int
    name: str = ""
    playtime_forever: int = 0
    playtime_2weeks: int = 0


@dataclass
class PlayerSummary:
    steamid: str
    personaname: str = ""
    profileurl: str = ""
    avatar: str = ""
    personastate: int = 0
    gameextrainfo: str = ""
    gameid: str = ""

    owned_games: list[OwnedGame] = field(default_factory=list)
    recent_games: list[OwnedGame] = field(default_factory=list)


@dataclass
class InventoryItem:
    appid: int
    contextid: str
    assetid: str
    classid: str
    instanceid: str
    name: str = ""
    market_name: str = ""
    type: str = ""
    icon_url: str = ""
    tradable: bool = False
    descriptions: list[str] = field(default_factory=list)
    tags: list[dict] = field(default_factory=list)
