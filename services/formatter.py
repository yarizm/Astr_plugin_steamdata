from __future__ import annotations

from ..models.game_data import GameData
from ..models.user_data import InventoryItem, PlayerSummary


class MarkdownFormatter:
    """Convert Steam data models to user-facing Markdown."""

    def format(self, data: GameData) -> str:
        md: list[str] = [f"# {data.name}", ""]

        if data.short_description:
            md.extend([f"> {data.short_description}", ""])

        if data.store_url:
            md.extend([f"[Steam 商店页面]({data.store_url})", ""])

        md.append("## 基本信息")
        self._append_if(md, "开发商", ", ".join(data.developers))
        self._append_if(md, "发行商", ", ".join(data.publishers))
        self._append_if(md, "发行日期", data.release_date)
        self._append_if(md, "类型", ", ".join(data.genres))
        platforms = [platform.capitalize() for platform, enabled in data.platforms.items() if enabled]
        self._append_if(md, "平台", ", ".join(platforms))
        md.append("")

        md.append("## 价格")
        if data.is_free:
            md.append("- **当前价格**: 免费")
        elif data.discount_percent > 0:
            original = f"，原价 {data.original_price}" if data.original_price else ""
            md.append(f"- **当前价格**: {data.price_formatted or '未知'} (-{data.discount_percent}%{original})")
        else:
            md.append(f"- **当前价格**: {data.price_formatted or '未知'}")
        md.append("")

        if data.current_players is not None:
            md.extend(["## 在线人数", f"- **当前在线**: {data.current_players:,}", ""])

        if data.total_reviews > 0:
            md.append("## 评价")
            md.append(f"- **总评论数**: {data.total_reviews:,}")
            md.append(f"- **好评率**: {data.positive_rate}%")
            self._append_if(md, "总体评价", data.review_score_desc)
            md.append("")

        if data.reviews:
            md.append("## 最新评论摘录")
            for index, review in enumerate(data.reviews, 1):
                verdict = "推荐" if review.recommended else "不推荐"
                text = review.review_text.replace("\r", " ").replace("\n", " ").strip()
                if len(text) > 120:
                    text = text[:117] + "..."
                md.append(f"{index}. **{verdict}**：{text}（游玩 {review.playtime_hours:.1f} 小时）")
            md.append("")

        return "\n".join(md).strip()

    def format_user_status(self, summary: PlayerSummary) -> str:
        state_map = {
            0: "离线",
            1: "在线",
            2: "忙碌",
            3: "离开",
            4: "打盹",
            5: "想交易",
            6: "想玩游戏",
        }
        state = state_map.get(summary.personastate, "未知")

        md = [f"# 玩家：{summary.personaname or summary.steamid}"]
        if summary.profileurl:
            md.append(f"[Steam 个人主页]({summary.profileurl})")
        md.append(f"- **当前状态**: {state}")

        if summary.gameextrainfo:
            md.append(f"- **正在游玩**: {summary.gameextrainfo}")
        md.append("")

        if summary.recent_games:
            md.append("## 最近游玩（过去两周）")
            for game in summary.recent_games[:5]:
                md.append(
                    f"- **{game.name}**: {game.playtime_2weeks / 60:.1f} 小时"
                    f"（总计 {game.playtime_forever / 60:.1f} 小时）"
                )
            md.append("")

        if summary.owned_games:
            md.append("## 游戏库概览")
            md.append(f"- **拥有游戏数**: {len(summary.owned_games)}")
            md.append("")
            md.append("## 游玩时长 Top 5")
            top_games = sorted(summary.owned_games, key=lambda game: game.playtime_forever, reverse=True)[:5]
            for game in top_games:
                md.append(f"- **{game.name}**: {game.playtime_forever / 60:.1f} 小时")
            md.append("")

        return "\n".join(md).strip()

    def format_inventory(self, username: str, game_name: str, items: list[InventoryItem]) -> str:
        md = [f"# {username} 的 {game_name} 库存", f"共读取到 {len(items)} 件物品。", ""]

        if not items:
            md.append("> 暂无物品，或该库存被设置为私密。")
            return "\n".join(md).strip()

        for index, item in enumerate(items, 1):
            name = item.market_name or item.name or f"物品 {index}"
            md.append(f"{index}. **{name}**")
            if item.type:
                md.append(f"   - 类型: {item.type}")

            tag_names = []
            for tag in item.tags:
                if tag.get("category") in {"Rarity", "Quality", "Weapon", "Type"}:
                    tag_name = tag.get("localized_tag_name") or tag.get("name")
                    if tag_name:
                        tag_names.append(tag_name)

            if tag_names:
                md.append(f"   - 标签: {', '.join(tag_names)}")

        return "\n".join(md).strip()

    @staticmethod
    def _append_if(md: list[str], label: str, value: str | None) -> None:
        if value:
            md.append(f"- **{label}**: {value}")
