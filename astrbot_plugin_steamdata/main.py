from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger

from .services.steam_api import SteamAPIService
from .services.formatter import MarkdownFormatter
from .tools.game_info_tool import SteamGameInfoTool


class AstrBotPluginSteamData(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 解析配置
        cfg = context.get_config()
        self.api_key = cfg.get("steam_api_key", "")
        self.price_region = cfg.get("price_region", "cn")
        self.review_count = cfg.get("review_count", 5)
        self.timeout = cfg.get("request_timeout", 15)
        self.enable_fallback = cfg.get("enable_fallback_commands", True)
        
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
            SteamGameInfoTool(
                steam_service=self.steam_service,
                formatter=self.formatter,
            )
        )
        logger.info("AstrBot Steam Data 插件已加载")

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
