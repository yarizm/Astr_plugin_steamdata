from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger

from .services.steam_api import SteamAPIService
from .services.formatter import MarkdownFormatter
from .tools.game_info_tool import SteamGameInfoTool
from .tools.user_status_tool import SteamUserStatusTool
from .tools.user_inventory_tool import SteamInventoryTool

class AstrBotPluginSteamData(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        
        # 使用 AstrBot 原生注入的 config 字典
        plugin_config = config or {}
        
        self.api_key = plugin_config.get("steam_api_key", "")
        self.price_region = plugin_config.get("price_region", "cn")
        self.review_count = plugin_config.get("review_count", 5)
        self.timeout = plugin_config.get("request_timeout", 15)
        self.enable_fallback = plugin_config.get("enable_fallback_commands", True)
        
        logger.info(f"DEBUG: 依赖注入配置状态: {'成功' if self.api_key else '失败'}")
        if not self.api_key:
            logger.info(f"DEBUG: 当前工作目录: {os.getcwd()}")
        
        # 初始化服务层
        self.steam_service = SteamAPIService(
            api_key=self.api_key,
            price_region=self.price_region,
            review_count=self.review_count,
            timeout=self.timeout,
        )
        self.formatter = MarkdownFormatter()
        
        # 注册 LLM Tool
        self.context.add_llm_tools(
            SteamGameInfoTool(steam_service=self.steam_service, formatter=self.formatter),
            SteamUserStatusTool(steam_service=self.steam_service, formatter=self.formatter),
            SteamInventoryTool(steam_service=self.steam_service, formatter=self.formatter)
        )
        
        if self.api_key:
            logger.info(f"AstrBot Steam Data 插件已加载。Steam API Key 读取成功: {self.api_key[:4]}...{self.api_key[-4:]}")
        else:
            logger.warning("AstrBot Steam Data 插件已加载。警告: Steam API Key 未配置，部分功能（在线人数、玩家状态、库存）将降级。")

    @filter.command("steam")
    async def steam_query(self, event: AstrMessageEvent):
        """兜底命令: /steam <游戏名>"""
        if not self.enable_fallback:
            return

        game_name = event.message_str.strip()
        if not game_name:
            yield event.plain_result("请输入游戏名称，例如: /steam Elden Ring")
            return
        
        try:
            yield event.plain_result(f"🔍 正在查询 Steam 上的 [{game_name}] ...")
            data = await self.steam_service.fetch_game_data(game_name)
            md = self.formatter.format(data)
            yield event.plain_result(md)
        except Exception as e:
            logger.error(f"Steam 查询失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {e}")

    @filter.command("steam_user")
    async def steam_user_query(self, event: AstrMessageEvent):
        """兜底命令: /steam_user <SteamID或自定义URL>"""
        if not self.enable_fallback:
            return

        user_identifier = event.message_str.strip()
        if not user_identifier:
            yield event.plain_result("请输入玩家ID，例如: /steam_user yarizm")
            return
            
        try:
            yield event.plain_result(f"🔍 正在查询玩家 [{user_identifier}] 的状态 ...")
            
            steam_id = user_identifier
            if not steam_id.isdigit() or len(steam_id) != 17:
                steam_id = await self.steam_service.resolve_vanity_url(user_identifier)
                if not steam_id:
                    yield event.plain_result(f"❌ 无法解析用户 '{user_identifier}'")
                    return
            
            summary = await self.steam_service.get_player_summary(steam_id)
            if not summary:
                yield event.plain_result(f"❌ 获取不到该玩家资料，可能是私密账户。")
                return
                
            owned_games = await self.steam_service.get_owned_games(steam_id)
            if owned_games:
                summary.owned_games = owned_games
                recent_games = [g for g in owned_games if g.playtime_2weeks > 0]
                summary.recent_games = sorted(recent_games, key=lambda x: x.playtime_2weeks, reverse=True)
                
            md = self.formatter.format_user_status(summary)
            yield event.plain_result(md)
        except Exception as e:
            logger.error(f"Steam 用户查询失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {e}")

    @filter.command("steam_inv")
    async def steam_inv_query(self, event: AstrMessageEvent):
        """兜底命令: /steam_inv <SteamID或自定义URL> <游戏名>"""
        if not self.enable_fallback:
            return

        args = event.message_str.strip().split(" ", 1)
        if len(args) < 2:
            yield event.plain_result("格式错误，请使用: /steam_inv <玩家ID> <游戏名>。例如: /steam_inv yarizm CS2")
            return
            
        user_identifier = args[0]
        game_name = args[1]
        
        try:
            yield event.plain_result(f"🔍 正在查询玩家 [{user_identifier}] 的 [{game_name}] 库存 ...")
            
            appid = await self.steam_service.search_game(game_name)
            if not appid:
                yield event.plain_result(f"❌ 找不到游戏 '{game_name}'")
                return
                
            steam_id = user_identifier
            if not steam_id.isdigit() or len(steam_id) != 17:
                steam_id = await self.steam_service.resolve_vanity_url(user_identifier)
                if not steam_id:
                    yield event.plain_result(f"❌ 无法解析用户 '{user_identifier}'")
                    return
            
            items = await self.steam_service.get_user_inventory(steam_id, appid, limit=40)
            if not items:
                yield event.plain_result(f"❌ 库存为空或设为私密。")
                return
                
            md = self.formatter.format_inventory(user_identifier, game_name, items)
            yield event.plain_result(md)
        except Exception as e:
            logger.error(f"Steam 库存查询失败: {e}")
            yield event.plain_result(f"❌ 查询失败: {e}")
