from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OwnedGame:
    appid: int
    name: str = ""
    playtime_forever: int = 0  # 游戏总时长（分钟）
    playtime_2weeks: int = 0   # 过去2周游戏时长（分钟）


@dataclass
class PlayerSummary:
    steamid: str
    personaname: str = ""
    profileurl: str = ""
    avatar: str = ""
    personastate: int = 0       # 0: 离线, 1: 在线, 2: 忙碌, 3: 离开, 4: 离开, 5: 准备交易, 6: 准备游戏
    gameextrainfo: str = ""     # 如果正在玩游戏，则是游戏的名称
    gameid: str = ""            # 正在玩游戏的 appid
    
    # 获取到的额外数据
    owned_games: list[OwnedGame] = field(default_factory=list)
    recent_games: list[OwnedGame] = field(default_factory=list)


@dataclass
class InventoryItem:
    appid: int
    contextid: str
    assetid: str
    classid: str
    instanceid: str
    
    # 具体物品信息 (来自 descriptions)
    name: str = ""
    market_name: str = ""
    type: str = ""
    icon_url: str = ""
    tradable: bool = False
    descriptions: list[str] = field(default_factory=list)
    tags: list[dict] = field(default_factory=list)  # 稀有度等信息通常在 tags 里
