from ..models.game_data import GameData


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
