from pydantic import Field
from pydantic.dataclasses import dataclass
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.astr_agent_context import AstrAgentContext


@dataclass
class SteamInventoryTool(FunctionTool[AstrAgentContext]):
    name: str = "steam_user_inventory"
    description: str = (
        "查询某个 Steam 玩家在指定游戏中的库存物品（例如 CS2/CS:GO 的饰品、Dota2 饰品等）。"
        "当用户想看某人库存里有什么时调用。"
    )
    parameters: dict = Field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "user_identifier": {
                "type": "string",
                "description": "玩家的 Steam ID (17位纯数字) 或自定义 URL 名称 (vanity url)",
            },
            "game_name": {
                "type": "string",
                "description": "要查询库存的游戏名称，如 CS2, Dota 2, Rust 等",
            },
        },
        "required": ["user_identifier", "game_name"],
    })
    
    steam_service: object = Field(default=None, exclude=True)
    formatter: object = Field(default=None, exclude=True)
    
    async def call(
        self, context: ContextWrapper[AstrAgentContext], **kwargs
    ) -> ToolExecResult:
        user_identifier = kwargs.get("user_identifier", "")
        game_name = kwargs.get("game_name", "")
        
        if not user_identifier or not game_name:
            return "请提供要查询的玩家 ID 和游戏名称。"
            
        try:
            # 搜索游戏，获取 AppID
            appid = await self.steam_service.search_game(game_name)
            if not appid:
                return f"未找到名为 '{game_name}' 的 Steam 游戏，无法查询库存。"
                
            # 解析 17位 SteamID64
            steam_id = user_identifier
            if not steam_id.isdigit() or len(steam_id) != 17:
                steam_id = await self.steam_service.resolve_vanity_url(user_identifier)
                if not steam_id:
                    return f"无法解析用户 '{user_identifier}'，请检查名称是否正确。"
            
            # 获取玩家名字 (为了展示更友好)
            username = user_identifier
            summary = await self.steam_service.get_player_summary(steam_id)
            if summary and summary.personaname:
                username = summary.personaname
            
            # 拉取库存，默认提取前 40 个
            items = await self.steam_service.get_user_inventory(steam_id, appid, limit=40)
            
            if not items:
                return (
                    f"玩家 '{username}' 的 [{game_name}] 库存为空，或因隐私设置无法读取。\n"
                    "提醒用户：如果要查询库存，请确保 Steam 隐私设置中的「库存」设为了“公开”。"
                )
            
            md = self.formatter.format_inventory(username, game_name, items)
            
            return (
                f"以下是玩家 [{username}] 的 [{game_name}] 库存部分物品（已截断前40个），"
                f"请总结该玩家的库存有什么亮眼的物品：\n\n{md}"
            )
        except Exception as e:
            return f"查询库存出错: {str(e)}"
