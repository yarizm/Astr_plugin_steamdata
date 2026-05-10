from __future__ import annotations

from compat import AstrAgentContext, ContextWrapper, Field, FunctionTool, ToolExecResult, dataclass


@dataclass
class SteamGameInfoTool(FunctionTool[AstrAgentContext]):
    name: str = "steam_game_info"
    description: str = (
        "查询指定 Steam 游戏的基础信息、价格、在线人数、评价和最新评论。"
        "当用户想了解某个 Steam 游戏时调用。"
    )
    parameters: dict = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "game_name": {
                    "type": "string",
                    "description": "要查询的 Steam 游戏名称，例如 Elden Ring、CS2、黑神话：悟空",
                },
            },
            "required": ["game_name"],
        }
    )
    steam_service: object = Field(default=None, exclude=True)
    formatter: object = Field(default=None, exclude=True)

    async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs) -> ToolExecResult:
        game_name = str(kwargs.get("game_name") or "").strip()
        if not game_name:
            return "请提供要查询的 Steam 游戏名称。"

        try:
            data = await self.steam_service.fetch_game_data(game_name)
            markdown = self.formatter.format(data)
            return f"以下是 [{game_name}] 的 Steam 数据，请据此给用户生成简洁总结：\n\n{markdown}"
        except ValueError as exc:
            return f"查询游戏失败：{exc}"
        except Exception:
            return "查询游戏失败：Steam 服务暂时不可用，请稍后再试。"
