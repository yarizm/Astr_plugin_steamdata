from __future__ import annotations

from ..compat import AstrAgentContext, ContextWrapper, Field, FunctionTool, ToolExecResult, dataclass


@dataclass
class SteamUserStatusTool(FunctionTool[AstrAgentContext]):
    name: str = "steam_user_status"
    description: str = (
        "查询 Steam 玩家状态、正在游玩的游戏、最近两周游玩记录和游戏库概览。"
        "当用户询问某个玩家最近在玩什么或当前状态时调用。"
    )
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "user_identifier": {
                    "type": "string",
                    "description": "玩家 SteamID64（17 位数字）或 Vanity URL 名称",
                },
            },
            "required": ["user_identifier"],
        }
    )
    steam_service: object = Field(default=None, exclude=True)
    formatter: object = Field(default=None, exclude=True)

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        user_identifier = str(kwargs.get("user_identifier") or "").strip()
        if not user_identifier:
            return "请提供要查询的 SteamID64 或 Vanity URL。"

        if not self.steam_service.api_key:
            return "玩家状态查询需要配置 Steam Web API Key，请联系管理员配置插件。"

        try:
            steam_id = user_identifier
            if not steam_id.isdigit() or len(steam_id) != 17:
                steam_id = await self.steam_service.resolve_vanity_url(user_identifier)
                if not steam_id:
                    return f"无法解析用户 '{user_identifier}'，请检查 SteamID 或 Vanity URL 是否正确。"

            summary = await self.steam_service.get_player_summary(steam_id)
            if not summary:
                return f"未找到 SteamID 为 {steam_id} 的玩家资料，可能不存在或个人资料不可见。"

            owned_games = await self.steam_service.get_owned_games(steam_id)
            summary.owned_games = owned_games
            summary.recent_games = sorted(
                [game for game in owned_games if game.playtime_2weeks > 0],
                key=lambda game: game.playtime_2weeks,
                reverse=True,
            )

            markdown = self.formatter.format_user_status(summary)
            return (
                f"以下是玩家 [{summary.personaname or steam_id}] 的 Steam 状态数据，"
                f"请据此生成简洁总结：\n\n{markdown}"
            )
        except Exception:
            return "查询玩家状态失败：Steam 服务暂时不可用，或玩家隐私设置不允许读取。"
