from pydantic import Field
from pydantic.dataclasses import dataclass
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.astr_agent_context import AstrAgentContext


@dataclass
class SteamGameInfoTool(FunctionTool[AstrAgentContext]):
    name: str = "steam_game_info"
    description: str = (
        "在 Steam 平台上查询指定游戏的详细信息，"
        "包括游戏简介、当前在线人数、价格、评分和最新评论。"
        "当用户想了解某个 Steam 游戏的信息时调用此工具。"
    )
    parameters: dict = Field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "game_name": {
                "type": "string",
                "description": "要查询的 Steam 游戏名称，如 Elden Ring、CS2、黑神话悟空",
            },
        },
        "required": ["game_name"],
    })
    
    # 运行时注入的服务实例（不参与 schema）
    steam_service: object = Field(default=None, exclude=True)
    formatter: object = Field(default=None, exclude=True)
    
    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        game_name = kwargs.get("game_name", "")
        if not game_name:
            return "请提供要查询的游戏名称。"
        
        try:
            data = await self.steam_service.fetch_game_data(game_name)
            md = self.formatter.format(data)
            
            return (
                f"以下是关于 [{game_name}] 的 Steam 数据，"
                f"请根据这些信息为用户生成一份简洁的游戏概况总结：\n\n{md}"
            )
        except Exception as e:
            return f"查询游戏 '{game_name}' 时出错: {str(e)}"
