import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from ..models.game_data import GameData, ReviewItem
from ..models.user_data import PlayerSummary, OwnedGame, InventoryItem
from astrbot.api import logger


class SteamAPIService:
    def __init__(self, api_key: str = "", price_region: str = "cn", review_count: int = 5, timeout: int = 15):
        self.api_key = api_key
        self.price_region = price_region
        self.review_count = review_count
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    async def search_game(self, game_name: str) -> Optional[int]:
        """根据游戏名搜索 appid（使用 storesearch API）"""
        url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc={self.price_region}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get("items", [])
                        if not items:
                            return None
                        # 返回第一个匹配结果的 id
                        return items[0].get("id")
                    else:
                        logger.error(f"Steam storesearch 失败，状态码: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"获取 Steam storesearch 出错: {e}")
            return None

    async def fetch_game_data(self, game_name: str) -> GameData:
        appid = await self.search_game(game_name)
        if not appid:
            raise Exception(f"未找到名为 '{game_name}' 的 Steam 游戏。")

        # 构造 GameData 实例，基本信息
        game_data = GameData(
            appid=appid,
            name=game_name,  # 稍后会被 Store API 返回的确切名字覆盖
            store_url=f"https://store.steampowered.com/app/{appid}/"
        )

        # 并发获取各个数据源
        tasks = [
            self._get_app_details(appid, game_data),
            self._get_reviews(appid, game_data)
        ]
        if self.api_key:
            tasks.append(self._get_player_count(appid, game_data))

        await asyncio.gather(*tasks, return_exceptions=True)
        return game_data

    async def _get_app_details(self, appid: int, game_data: GameData) -> None:
        """获取游戏详情（简介、价格、平台等）"""
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={self.price_region}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        str_appid = str(appid)
                        if data.get(str_appid, {}).get("success"):
                            app_data = data[str_appid]["data"]
                            
                            game_data.name = app_data.get("name", game_data.name)
                            game_data.short_description = app_data.get("short_description", "")
                            game_data.developers = app_data.get("developers", [])
                            game_data.publishers = app_data.get("publishers", [])
                            game_data.header_image_url = app_data.get("header_image", "")
                            
                            genres = app_data.get("genres", [])
                            game_data.genres = [g.get("description", "") for g in genres]
                            
                            release_date = app_data.get("release_date", {})
                            game_data.release_date = release_date.get("date", "")
                            
                            game_data.platforms = app_data.get("platforms", {})
                            
                            game_data.is_free = app_data.get("is_free", False)
                            if not game_data.is_free and "price_overview" in app_data:
                                price_info = app_data["price_overview"]
                                game_data.price_formatted = price_info.get("final_formatted", "")
                                game_data.discount_percent = price_info.get("discount_percent", 0)
                                game_data.original_price = price_info.get("initial_formatted", "")
        except Exception as e:
            logger.error(f"获取游戏详情失败 ({appid}): {e}")

    async def _get_player_count(self, appid: int, game_data: GameData) -> None:
        """获取在线人数（需要 API Key）"""
        if not self.api_key:
            return
            
        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?key={self.api_key}&appid={appid}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        game_data.current_players = data.get("response", {}).get("player_count")
        except Exception as e:
            logger.error(f"获取在线人数失败 ({appid}): {e}")

    async def _get_reviews(self, appid: int, game_data: GameData) -> None:
        """获取评论及总体评分"""
        url = f"https://store.steampowered.com/appreviews/{appid}?json=1&num_per_page={self.review_count}&language=all"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        query_summary = data.get("query_summary", {})
                        
                        game_data.total_reviews = query_summary.get("total_reviews", 0)
                        
                        total_positive = query_summary.get("total_positive", 0)
                        if game_data.total_reviews > 0:
                            game_data.positive_rate = round((total_positive / game_data.total_reviews) * 100, 1)
                            
                        game_data.review_score_desc = query_summary.get("review_score_desc", "")
                        
                        reviews_data = data.get("reviews", [])
                        for rev in reviews_data:
                            author = rev.get("author", {})
                            playtime_forever = author.get("playtime_forever", 0)
                            playtime_hours = playtime_forever / 60.0
                            
                            game_data.reviews.append(ReviewItem(
                                recommended=rev.get("voted_up", True),
                                review_text=rev.get("review", ""),
                                playtime_hours=playtime_hours,
                                language=rev.get("language", "")
                            ))
        except Exception as e:
            logger.error(f"获取评论失败 ({appid}): {e}")

    async def resolve_vanity_url(self, username: str) -> Optional[str]:
        """将自定义 URL 转换为 SteamID64"""
        if not self.api_key:
            return None
        url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={self.api_key}&vanityurl={username}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data.get("response", {})
                        if response.get("success") == 1:
                            return response.get("steamid")
        except Exception as e:
            logger.error(f"解析 VanityURL 失败 ({username}): {e}")
        return None

    async def get_player_summary(self, steam_id: str) -> Optional[PlayerSummary]:
        """获取玩家概要信息"""
        if not self.api_key:
            return None
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={self.api_key}&steamids={steam_id}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        players = data.get("response", {}).get("players", [])
                        if players:
                            p = players[0]
                            return PlayerSummary(
                                steamid=p.get("steamid", ""),
                                personaname=p.get("personaname", ""),
                                profileurl=p.get("profileurl", ""),
                                avatar=p.get("avatarfull", ""),
                                personastate=p.get("personastate", 0),
                                gameextrainfo=p.get("gameextrainfo", ""),
                                gameid=p.get("gameid", "")
                            )
        except Exception as e:
            logger.error(f"获取玩家概要失败 ({steam_id}): {e}")
        return None

    async def get_owned_games(self, steam_id: str) -> List[OwnedGame]:
        """获取拥有的游戏列表"""
        if not self.api_key:
            return []
        url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={self.api_key}&steamid={steam_id}&include_appinfo=true&include_played_free_games=true"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        games = data.get("response", {}).get("games", [])
                        owned_games = []
                        for g in games:
                            owned_games.append(OwnedGame(
                                appid=g.get("appid", 0),
                                name=g.get("name", ""),
                                playtime_forever=g.get("playtime_forever", 0),
                                playtime_2weeks=g.get("playtime_2weeks", 0)
                            ))
                        return owned_games
        except Exception as e:
            logger.error(f"获取玩家拥有的游戏失败 ({steam_id}): {e}")
        return []

    async def get_user_inventory(self, steam_id: str, appid: int, limit: int = 50) -> List[InventoryItem]:
        """获取用户指定游戏的库存（提取前 limit 个）"""
        url = f"https://steamcommunity.com/inventory/{steam_id}/{appid}/2?l=english&count=2000"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        descriptions = {f"{d['classid']}_{d['instanceid']}": d for d in data.get("descriptions", [])}
                        assets = data.get("assets", [])
                        
                        items = []
                        for asset in assets:
                            classid = asset.get("classid")
                            instanceid = asset.get("instanceid")
                            desc = descriptions.get(f"{classid}_{instanceid}", {})
                            
                            tags = desc.get("tags", [])
                            
                            items.append(InventoryItem(
                                appid=appid,
                                contextid=asset.get("contextid", "2"),
                                assetid=asset.get("assetid", ""),
                                classid=str(classid),
                                instanceid=str(instanceid),
                                name=desc.get("name", ""),
                                market_name=desc.get("market_name", ""),
                                type=desc.get("type", ""),
                                icon_url=f"https://steamcommunity-a.akamaihd.net/economy/image/{desc.get('icon_url')}" if desc.get('icon_url') else "",
                                tradable=bool(desc.get("tradable", 0)),
                                descriptions=[d.get("value", "") for d in desc.get("descriptions", []) if d.get("value")],
                                tags=tags
                            ))
                            if len(items) >= limit:
                                break
                        return items
                    elif resp.status == 429:
                        logger.error("获取库存触发频率限制 (429)")
                    elif resp.status == 403:
                        logger.error("获取库存被拒绝 (可能设置了私密)")
                    else:
                        logger.error(f"获取库存失败，状态码: {resp.status}")
        except Exception as e:
            logger.error(f"获取库存出错 ({steam_id}, {appid}): {e}")
        return []
