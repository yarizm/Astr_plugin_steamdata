from ..models.game_data import GameData
from ..models.user_data import PlayerSummary, InventoryItem


class MarkdownFormatter:
    """负责将 GameData 转换为 Markdown 文本"""
    
    def format(self, data: GameData) -> str:
        md = []
        # 游戏名
        md.append(f"# 🎮 {data.name}")
        md.append("")
        
        # 简介
        if data.short_description:
            md.append(f"> {data.short_description}")
            md.append("")
        
        # 商店链接
        if data.store_url:
            md.append(f"🔗 [Steam 商店页面]({data.store_url})")
            md.append("")

        # 基本信息
        md.append("## 📊 基本信息")
        if data.developers:
            md.append(f"- **开发商**: {', '.join(data.developers)}")
        if data.publishers:
            md.append(f"- **发行商**: {', '.join(data.publishers)}")
        if data.release_date:
            md.append(f"- **发行日期**: {data.release_date}")
        if data.genres:
            md.append(f"- **类型**: {', '.join(data.genres)}")
        
        platforms = [p.capitalize() for p, v in data.platforms.items() if v]
        if platforms:
            md.append(f"- **平台**: {', '.join(platforms)}")
        md.append("")

        # 价格
        md.append("## 💰 价格")
        if data.is_free:
            md.append("- **当前价格**: 免费 (Free to Play)")
        else:
            if data.discount_percent > 0:
                md.append(f"- **当前价格**: {data.price_formatted} (-{data.discount_percent}%，原价 {data.original_price})")
            else:
                price_text = data.price_formatted if data.price_formatted else "未知"
                md.append(f"- **当前价格**: {price_text}")
        md.append("")

        # 在线人数
        if data.current_players is not None:
            md.append("## 👥 在线人数")
            md.append(f"- **当前在线**: {data.current_players:,}")
            md.append("")

        # 评分
        if data.total_reviews > 0:
            md.append("## ⭐ 评分")
            md.append(f"- **总评论数**: {data.total_reviews:,}")
            md.append(f"- **好评率**: {data.positive_rate}%")
            if data.review_score_desc:
                md.append(f"- **总体评价**: {data.review_score_desc}")
            md.append("")

        # 评论
        if data.reviews:
            md.append("## 💬 最新评论 (摘录)")
            for i, r in enumerate(data.reviews, 1):
                icon = "👍" if r.recommended else "👎"
                playtime = f"{r.playtime_hours:.1f}"
                text = r.review_text.replace('\n', ' ')
                if len(text) > 100:
                    text = text[:97] + "..."
                md.append(f"{i}. {icon} \"{text}\" — 游玩 {playtime} 小时")
            md.append("")

        return "\n".join(md)

    def format_user_status(self, summary: PlayerSummary) -> str:
        md = []
        state_map = {0: "离线", 1: "在线", 2: "忙碌", 3: "离开", 4: "离开", 5: "准备交易", 6: "准备游戏"}
        state_str = state_map.get(summary.personastate, "未知")
        
        md.append(f"# 👤 玩家: {summary.personaname}")
        md.append(f"🔗 [Steam 个人主页]({summary.profileurl})")
        md.append(f"🟢 **当前状态**: {state_str}")
        
        if summary.gameextrainfo:
            md.append(f"🎮 **正在游玩**: {summary.gameextrainfo}")
        md.append("")
        
        if summary.recent_games:
            md.append("## 🕒 最近游玩 (过去2周)")
            for g in summary.recent_games[:5]:
                md.append(f"- **{g.name}**: {g.playtime_2weeks / 60:.1f} 小时 (总计 {g.playtime_forever / 60:.1f} 小时)")
            md.append("")
            
        if summary.owned_games:
            md.append("## 🏆 游戏库总览")
            md.append(f"- **总拥有游戏数**: {len(summary.owned_games)}")
            md.append("### 🎖️ 游玩时长 Top 5")
            top_games = sorted(summary.owned_games, key=lambda x: x.playtime_forever, reverse=True)[:5]
            for g in top_games:
                md.append(f"- **{g.name}**: {g.playtime_forever / 60:.1f} 小时")
            md.append("")
            
        return "\n".join(md)

    def format_inventory(self, username: str, game_name: str, items: list[InventoryItem]) -> str:
        md = []
        md.append(f"# 🎒 {username} 的 [{game_name}] 库存")
        md.append(f"共提取了前 {len(items)} 件物品。")
        md.append("")
        
        if not items:
            md.append("> 暂无物品，或者库存设置为私密。")
            return "\n".join(md)
            
        for i, item in enumerate(items, 1):
            name = item.market_name or item.name
            md.append(f"{i}. **{name}**")
            if item.type:
                md.append(f"   - 类型: {item.type}")
            
            # 提取 tags 中的稀有度或品质 (只提取内部分类描述为 Rarity 或 Quality 的)
            rarity_tags = []
            for tag in item.tags:
                cat = tag.get("category", "")
                if cat in ("Rarity", "Quality", "Weapon"):
                    rarity_tags.append(tag.get("localized_tag_name", ""))
            
            if rarity_tags:
                md.append(f"   - 标签: {', '.join(rarity_tags)}")
                
        return "\n".join(md)
