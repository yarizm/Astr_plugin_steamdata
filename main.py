from __future__ import annotations

from .compat import AstrMessageEvent, Context, Star, filter, logger
from .config import normalize_config
from .services.formatter import MarkdownFormatter
from .services.steam_api import SteamAPIService
from .tools.game_info_tool import SteamGameInfoTool
from .tools.user_inventory_tool import SteamInventoryTool
from .tools.user_status_tool import SteamUserStatusTool


class AstrBotPluginSteamData(Star):
    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context)

        plugin_config = normalize_config(config or {})

        self.api_key = plugin_config.steam_api_key
        self.price_region = plugin_config.price_region
        self.review_count = plugin_config.review_count
        self.timeout = plugin_config.request_timeout
        self.enable_fallback = plugin_config.enable_fallback_commands

        self.steam_service = SteamAPIService(
            api_key=self.api_key,
            price_region=self.price_region,
            review_count=self.review_count,
            timeout=self.timeout,
        )
        self.formatter = MarkdownFormatter()

        self._register_llm_tools()

        if self.api_key:
            logger.info("AstrBot Steam Data 插件已加载，Steam API Key 已配置。")
        else:
            logger.warning(
                "AstrBot Steam Data 插件已加载，但未配置 Steam API Key；"
                "在线人数、玩家状态、游戏库和 Vanity URL 解析等功能会降级。"
            )

    def _register_llm_tools(self) -> None:
        tools = (
            SteamGameInfoTool(steam_service=self.steam_service, formatter=self.formatter),
            SteamUserStatusTool(steam_service=self.steam_service, formatter=self.formatter),
            SteamInventoryTool(steam_service=self.steam_service, formatter=self.formatter),
        )

        add_llm_tools = getattr(self.context, "add_llm_tools", None)
        if callable(add_llm_tools):
            add_llm_tools(*tools)
            return

        tool_manager = getattr(getattr(self.context, "provider_manager", None), "llm_tools", None)
        func_list = getattr(tool_manager, "func_list", None)
        if isinstance(func_list, list):
            func_list.extend(tools)
            return

        logger.warning("当前 AstrBot Context 不支持 LLM Tool 注册，已跳过 Steam 工具注册。")

    @filter.command("steam")
    async def steam_query(self, event: AstrMessageEvent):
        """兜底命令: /steam <游戏名>"""
        if not self.enable_fallback:
            return

        game_name = event.message_str.strip()
        if not game_name:
            yield event.plain_result("请输入游戏名称，例如：/steam Elden Ring")
            return

        try:
            yield event.plain_result(f"正在查询 Steam 游戏 [{game_name}] ...")
            data = await self.steam_service.fetch_game_data(game_name)
            yield event.plain_result(self.formatter.format(data))
        except ValueError as exc:
            yield event.plain_result(f"查询失败：{exc}")
        except Exception:
            logger.error("Steam 游戏查询失败。")
            yield event.plain_result("查询失败：Steam 服务暂时不可用，请稍后再试。")

    @filter.command("steam_user")
    async def steam_user_query(self, event: AstrMessageEvent):
        """兜底命令: /steam_user <SteamID 或 Vanity URL>"""
        if not self.enable_fallback:
            return

        user_identifier = event.message_str.strip()
        if not user_identifier:
            yield event.plain_result("请输入玩家 SteamID64 或 Vanity URL，例如：/steam_user yarizm")
            return

        if not self.api_key:
            yield event.plain_result("玩家状态查询需要配置 Steam Web API Key，请联系管理员配置插件。")
            return

        try:
            yield event.plain_result(f"正在查询玩家 [{user_identifier}] 的状态 ...")

            steam_id = await self._resolve_steam_id(user_identifier)
            if not steam_id:
                yield event.plain_result(f"无法解析用户 '{user_identifier}'，请检查 SteamID 或 Vanity URL 是否正确。")
                return

            summary = await self.steam_service.get_player_summary(steam_id)
            if not summary:
                yield event.plain_result("获取不到该玩家资料，可能是 SteamID 不存在或个人资料不可见。")
                return

            owned_games = await self.steam_service.get_owned_games(steam_id)
            summary.owned_games = owned_games
            summary.recent_games = sorted(
                [game for game in owned_games if game.playtime_2weeks > 0],
                key=lambda game: game.playtime_2weeks,
                reverse=True,
            )

            yield event.plain_result(self.formatter.format_user_status(summary))
        except Exception:
            logger.error("Steam 玩家查询失败。")
            yield event.plain_result("查询失败：Steam 服务暂时不可用，或玩家隐私设置不允许读取。")

    @filter.command("steam_inv")
    async def steam_inv_query(self, event: AstrMessageEvent):
        """兜底命令: /steam_inv <SteamID 或 Vanity URL> <游戏名>"""
        if not self.enable_fallback:
            return

        args = event.message_str.strip().split(" ", 1)
        if len(args) < 2 or not args[0].strip() or not args[1].strip():
            yield event.plain_result(
                "格式错误，请使用：/steam_inv <玩家 SteamID 或 Vanity URL> <游戏名>，"
                "例如：/steam_inv yarizm CS2"
            )
            return

        user_identifier = args[0].strip()
        game_name = args[1].strip()

        try:
            yield event.plain_result(f"正在查询玩家 [{user_identifier}] 的 [{game_name}] 库存 ...")

            appid = await self.steam_service.search_game(game_name)
            if not appid:
                yield event.plain_result(f"找不到 Steam 游戏 '{game_name}'。")
                return

            steam_id = await self._resolve_steam_id(user_identifier)
            if not steam_id:
                yield event.plain_result(f"无法解析用户 '{user_identifier}'，请检查 SteamID 或 Vanity URL 是否正确。")
                return

            items = await self.steam_service.get_user_inventory(steam_id, appid, limit=40)
            if not items:
                yield event.plain_result("库存为空，或该玩家的 Steam 库存隐私设置不允许读取。")
                return

            yield event.plain_result(self.formatter.format_inventory(user_identifier, game_name, items))
        except Exception:
            logger.error("Steam 库存查询失败。")
            yield event.plain_result("查询失败：Steam 服务暂时不可用，或玩家库存隐私设置不允许读取。")

    async def _resolve_steam_id(self, user_identifier: str) -> str | None:
        if user_identifier.isdigit() and len(user_identifier) == 17:
            return user_identifier

        if not self.api_key:
            return None

        return await self.steam_service.resolve_vanity_url(user_identifier)
