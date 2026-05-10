from __future__ import annotations

from compat import AstrAgentContext, ContextWrapper, Field, FunctionTool, ToolExecResult, dataclass


@dataclass
class SteamInventoryTool(FunctionTool[AstrAgentContext]):
    name: str = "steam_user_inventory"
    description: str = (
        "查询某个 Steam 玩家在指定游戏中的公开库存物品，例如 CS2 或 Dota 2 库存。"
        "当用户想查看某人的指定游戏库存时调用。"
    )
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "user_identifier": {
                    "type": "string",
                    "description": "玩家 SteamID64（17 位数字）或 Vanity URL 名称",
                },
                "game_name": {
                    "type": "string",
                    "description": "要查询库存的 Steam 游戏名称，例如 CS2、Dota 2、Rust",
                },
            },
            "required": ["user_identifier", "game_name"],
        }
    )
    steam_service: object = Field(default=None, exclude=True)
    formatter: object = Field(default=None, exclude=True)

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        user_identifier = str(kwargs.get("user_identifier") or "").strip()
        game_name = str(kwargs.get("game_name") or "").strip()

        if not user_identifier or not game_name:
            return "请提供要查询的玩家 SteamID64 或 Vanity URL，以及游戏名称。"

        try:
            appid = await self.steam_service.search_game(game_name)
            if not appid:
                return f"未找到名为 '{game_name}' 的 Steam 游戏，无法查询库存。"

            steam_id = user_identifier
            if not steam_id.isdigit() or len(steam_id) != 17:
                steam_id = await self.steam_service.resolve_vanity_url(user_identifier)
                if not steam_id:
                    return f"无法解析用户 '{user_identifier}'，请检查 SteamID 或 Vanity URL 是否正确。"

            username = user_identifier
            if self.steam_service.api_key:
                summary = await self.steam_service.get_player_summary(steam_id)
                if summary and summary.personaname:
                    username = summary.personaname

            items = await self.steam_service.get_user_inventory(steam_id, appid, limit=40)
            if not items:
                return (
                    f"玩家 '{username}' 的 [{game_name}] 库存为空，或因 Steam 隐私设置无法读取。"
                    "请确认该玩家的库存设置为公开。"
                )

            markdown = self.formatter.format_inventory(username, game_name, items)
            return (
                f"以下是玩家 [{username}] 的 [{game_name}] 库存部分物品（最多 40 件），"
                f"请据此生成简洁总结：\n\n{markdown}"
            )
        except Exception:
            return "查询库存失败：Steam 服务暂时不可用，或玩家库存隐私设置不允许读取。"
