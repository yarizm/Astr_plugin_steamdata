from pydantic import Field
from pydantic.dataclasses import dataclass
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.astr_agent_context import AstrAgentContext


@dataclass
class SteamUserStatusTool(FunctionTool[AstrAgentContext]):
    name: str = "steam_user_status"
    description: str = (
        "查询某个 Steam 玩家的状态信息，"
        "包括在线状态、当前正在玩的游戏、最近两周游玩的游戏时长以及库存里的常玩游戏。"
        "当用户询问某个玩家（或给出好友链接）玩了什么游戏、状态如何时使用此工具。"
    )
    parameters: dict = Field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "user_identifier": {
                "type": "string",
                "description": "玩家的 Steam ID (17位纯数字) 或自定义 URL 名称 (vanity url)",
            },
        },
        "required": ["user_identifier"],
    })
    
    steam_service: object = Field(default=None, exclude=True)
    formatter: object = Field(default=None, exclude=True)
    
    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        user_identifier = kwargs.get("user_identifier", "")
        if not user_identifier:
            return "请提供要查询的玩家 ID 或自定义 URL 名称。"
            
        if not self.steam_service.api_key:
            return "获取玩家状态失败：Steam API Key 未配置，此功能受限。请联系管理员配置插件 API Key。"
        
        try:
            # 解析 17位 SteamID64
            steam_id = user_identifier
            if not steam_id.isdigit() or len(steam_id) != 17:
                steam_id = await self.steam_service.resolve_vanity_url(user_identifier)
                if not steam_id:
                    return f"无法解析用户 '{user_identifier}'，请检查名称是否正确。"
            
            # 获取基本状态
            summary = await self.steam_service.get_player_summary(steam_id)
            if not summary:
                return f"未找到 SteamID 为 {steam_id} 的玩家资料，可能不存在或设置为完全私密。"
            
            # 获取拥有的游戏库
            owned_games = await self.steam_service.get_owned_games(steam_id)
            if not owned_games:
                return (
                    f"玩家 '{summary.personaname}' 的游戏状态获取为空。\n"
                    "这通常是因为该玩家的 Steam 隐私设置中「游戏详情」被设置为了“私密”。"
                )
            
            summary.owned_games = owned_games
            
            # 提取最近游玩 (按 2weeks 排序)
            recent_games = [g for g in owned_games if g.playtime_2weeks > 0]
            recent_games = sorted(recent_games, key=lambda x: x.playtime_2weeks, reverse=True)
            summary.recent_games = recent_games
            
            # 格式化
            md = self.formatter.format_user_status(summary)
            
            return (
                f"以下是玩家 [{summary.personaname}] 的 Steam 状态数据，"
                f"请根据这些信息为用户生成一份简洁的玩家档案总结：\n\n{md}"
            )
        except Exception as e:
            return f"查询玩家 '{user_identifier}' 时出错: {str(e)}"
