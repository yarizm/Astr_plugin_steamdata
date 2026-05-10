from __future__ import annotations

import asyncio
from typing import Any

try:
    import aiohttp

    _AIOHTTP_AVAILABLE = True
except ModuleNotFoundError:
    _AIOHTTP_AVAILABLE = False

    class _MissingAiohttp:
        class ClientError(Exception):
            pass

        class ClientTimeout:
            def __init__(self, total: int):
                self.total = total

        class ClientSession:
            def __init__(self, *_args, **_kwargs):
                raise RuntimeError("aiohttp is required to make Steam API requests")

    aiohttp = _MissingAiohttp()

from ..compat import logger
from ..config import normalize_config
from ..models.game_data import GameData, ReviewItem
from ..models.user_data import InventoryItem, OwnedGame, PlayerSummary


class SteamAPIService:
    def __init__(self, api_key: str = "", price_region: str = "cn", review_count: int = 5, timeout: int = 15):
        config = normalize_config(
            {
                "steam_api_key": api_key,
                "price_region": price_region,
                "review_count": review_count,
                "request_timeout": timeout,
            }
        )
        self.api_key = config.steam_api_key
        self.price_region = config.price_region
        self.review_count = config.review_count
        self.timeout_seconds = config.request_timeout
        self.timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)

    async def search_game(self, game_name: str) -> int | None:
        if not game_name.strip():
            return None

        data = await self._get_json(
            "https://store.steampowered.com/api/storesearch/",
            params={"term": game_name, "l": "schinese", "cc": self.price_region},
            context="Steam 游戏搜索",
        )
        if not isinstance(data, dict):
            return None

        items = data.get("items", [])
        if not items:
            return None
        return items[0].get("id")

    async def fetch_game_data(self, game_name: str) -> GameData:
        appid = await self.search_game(game_name)
        if not appid:
            raise ValueError(f"未找到名为 '{game_name}' 的 Steam 游戏")

        game_data = GameData(
            appid=appid,
            name=game_name,
            store_url=f"https://store.steampowered.com/app/{appid}/",
        )

        tasks = [
            self._get_app_details(appid, game_data),
            self._get_reviews(appid, game_data),
        ]
        if self.api_key:
            tasks.append(self._get_player_count(appid, game_data))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Steam 数据子任务失败：{result}")

        return game_data

    async def _get_app_details(self, appid: int, game_data: GameData) -> None:
        data = await self._get_json(
            "https://store.steampowered.com/api/appdetails",
            params={"appids": appid, "cc": self.price_region, "l": "schinese"},
            context=f"Steam 游戏详情 {appid}",
        )
        if not isinstance(data, dict):
            return

        app_info = data.get(str(appid), {})
        if not app_info.get("success"):
            return

        app_data = app_info.get("data", {})
        game_data.name = app_data.get("name") or game_data.name
        game_data.short_description = app_data.get("short_description") or ""
        game_data.developers = app_data.get("developers") or []
        game_data.publishers = app_data.get("publishers") or []
        game_data.header_image_url = app_data.get("header_image") or ""
        game_data.genres = [genre.get("description", "") for genre in app_data.get("genres", [])]
        game_data.release_date = app_data.get("release_date", {}).get("date", "")
        game_data.platforms = app_data.get("platforms") or {}
        game_data.is_free = bool(app_data.get("is_free", False))

        price_info = app_data.get("price_overview") or {}
        if price_info:
            game_data.price_formatted = price_info.get("final_formatted") or ""
            game_data.discount_percent = int(price_info.get("discount_percent") or 0)
            game_data.original_price = price_info.get("initial_formatted") or ""

    async def _get_player_count(self, appid: int, game_data: GameData) -> None:
        if not self.api_key:
            return

        data = await self._get_json(
            "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/",
            params={"key": self.api_key, "appid": appid},
            context=f"Steam 在线人数 {appid}",
        )
        if isinstance(data, dict):
            player_count = data.get("response", {}).get("player_count")
            if isinstance(player_count, int):
                game_data.current_players = player_count

    async def _get_reviews(self, appid: int, game_data: GameData) -> None:
        data = await self._get_json(
            f"https://store.steampowered.com/appreviews/{appid}",
            params={"json": 1, "num_per_page": self.review_count, "language": "all"},
            context=f"Steam 评论 {appid}",
        )
        if not isinstance(data, dict):
            return

        summary = data.get("query_summary", {})
        game_data.total_reviews = int(summary.get("total_reviews") or 0)
        total_positive = int(summary.get("total_positive") or 0)
        if game_data.total_reviews > 0:
            game_data.positive_rate = round(total_positive / game_data.total_reviews * 100, 1)
        game_data.review_score_desc = summary.get("review_score_desc") or ""

        for review in data.get("reviews", []):
            author = review.get("author", {})
            playtime_hours = float(author.get("playtime_forever") or 0) / 60
            game_data.reviews.append(
                ReviewItem(
                    recommended=bool(review.get("voted_up", True)),
                    review_text=review.get("review") or "",
                    playtime_hours=playtime_hours,
                    language=review.get("language") or "",
                )
            )

    async def resolve_vanity_url(self, username: str) -> str | None:
        if not self.api_key or not username.strip():
            return None

        data = await self._get_json(
            "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/",
            params={"key": self.api_key, "vanityurl": username},
            context="Steam Vanity URL 解析",
        )
        if not isinstance(data, dict):
            return None

        response = data.get("response", {})
        if response.get("success") == 1:
            return response.get("steamid")
        return None

    async def get_player_summary(self, steam_id: str) -> PlayerSummary | None:
        if not self.api_key or not steam_id:
            return None

        data = await self._get_json(
            "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
            params={"key": self.api_key, "steamids": steam_id},
            context="Steam 玩家资料",
        )
        if not isinstance(data, dict):
            return None

        players = data.get("response", {}).get("players", [])
        if not players:
            return None

        player = players[0]
        return PlayerSummary(
            steamid=player.get("steamid", ""),
            personaname=player.get("personaname", ""),
            profileurl=player.get("profileurl", ""),
            avatar=player.get("avatarfull", ""),
            personastate=int(player.get("personastate") or 0),
            gameextrainfo=player.get("gameextrainfo", ""),
            gameid=player.get("gameid", ""),
        )

    async def get_owned_games(self, steam_id: str) -> list[OwnedGame]:
        if not self.api_key or not steam_id:
            return []

        data = await self._get_json(
            "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
            params={
                "key": self.api_key,
                "steamid": steam_id,
                "include_appinfo": "true",
                "include_played_free_games": "true",
            },
            context="Steam 游戏库",
        )
        if not isinstance(data, dict):
            return []

        games = data.get("response", {}).get("games", [])
        return [
            OwnedGame(
                appid=int(game.get("appid") or 0),
                name=game.get("name", ""),
                playtime_forever=int(game.get("playtime_forever") or 0),
                playtime_2weeks=int(game.get("playtime_2weeks") or 0),
            )
            for game in games
        ]

    async def get_user_inventory(self, steam_id: str, appid: int, limit: int = 50) -> list[InventoryItem]:
        if not steam_id or not appid:
            return []

        data = await self._get_json(
            f"https://steamcommunity.com/inventory/{steam_id}/{appid}/2",
            params={"l": "schinese", "count": 2000},
            context="Steam 用户库存",
        )
        if not isinstance(data, dict):
            return []

        descriptions = {
            f"{description.get('classid')}_{description.get('instanceid')}": description
            for description in data.get("descriptions", [])
        }
        items: list[InventoryItem] = []

        for asset in data.get("assets", []):
            classid = asset.get("classid", "")
            instanceid = asset.get("instanceid", "")
            description = descriptions.get(f"{classid}_{instanceid}", {})
            icon_url = description.get("icon_url") or ""
            items.append(
                InventoryItem(
                    appid=appid,
                    contextid=asset.get("contextid", "2"),
                    assetid=asset.get("assetid", ""),
                    classid=str(classid),
                    instanceid=str(instanceid),
                    name=description.get("name", ""),
                    market_name=description.get("market_name", ""),
                    type=description.get("type", ""),
                    icon_url=f"https://steamcommunity-a.akamaihd.net/economy/image/{icon_url}" if icon_url else "",
                    tradable=bool(description.get("tradable", 0)),
                    descriptions=[
                        desc.get("value", "")
                        for desc in description.get("descriptions", [])
                        if desc.get("value")
                    ],
                    tags=description.get("tags", []),
                )
            )
            if len(items) >= limit:
                break

        return items

    async def _get_json(self, url: str, params: dict[str, Any] | None = None, context: str = "Steam API") -> Any | None:
        if not _AIOHTTP_AVAILABLE:
            logger.warning(f"{context} 请求跳过：当前环境未安装 aiohttp。")
            return None

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 403:
                        logger.warning(f"{context} 请求被拒绝，可能是隐私设置或权限限制。")
                        return None
                    if response.status == 429:
                        logger.warning(f"{context} 请求触发 Steam 频率限制。")
                        return None
                    if response.status >= 400:
                        logger.warning(f"{context} 请求失败，HTTP 状态码：{response.status}。")
                        return None
                    return await response.json(content_type=None)
        except (TimeoutError, asyncio.TimeoutError):
            logger.warning(f"{context} 请求超时。")
        except aiohttp.ClientError:
            logger.warning(f"{context} 网络请求失败。")
        except ValueError:
            logger.warning(f"{context} JSON 解析失败。")
        return None
