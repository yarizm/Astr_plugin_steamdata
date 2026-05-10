import unittest

from models.game_data import GameData, ReviewItem
from models.user_data import InventoryItem, OwnedGame, PlayerSummary
from services.formatter import MarkdownFormatter


class FormatterTests(unittest.TestCase):
    def setUp(self):
        self.formatter = MarkdownFormatter()

    def test_game_data_formats_to_markdown(self):
        data = GameData(
            appid=1245620,
            name="Elden Ring",
            short_description="An action RPG.",
            developers=["FromSoftware"],
            publishers=["Bandai Namco"],
            genres=["RPG"],
            release_date="25 Feb, 2022",
            platforms={"windows": True, "mac": False, "linux": False},
            price_formatted="¥298",
            current_players=12345,
            total_reviews=100,
            positive_rate=92.5,
            review_score_desc="特别好评",
            store_url="https://store.steampowered.com/app/1245620/",
            reviews=[ReviewItem(True, "Great game\nwith bosses.", 10.5, "schinese")],
        )

        output = self.formatter.format(data)

        self.assertIn("# Elden Ring", output)
        self.assertIn("## 基本信息", output)
        self.assertIn("¥298", output)
        self.assertIn("12,345", output)
        self.assertIn("Great game with bosses.", output)

    def test_player_status_formats_to_markdown(self):
        summary = PlayerSummary(
            steamid="76561198000000000",
            personaname="Alice",
            profileurl="https://steamcommunity.com/id/alice",
            personastate=1,
            gameextrainfo="CS2",
            owned_games=[
                OwnedGame(730, "CS2", 1200, 300),
                OwnedGame(570, "Dota 2", 600, 0),
            ],
            recent_games=[OwnedGame(730, "CS2", 1200, 300)],
        )

        output = self.formatter.format_user_status(summary)

        self.assertIn("# 玩家：Alice", output)
        self.assertIn("在线", output)
        self.assertIn("CS2", output)
        self.assertIn("拥有游戏数", output)

    def test_inventory_formats_to_markdown(self):
        items = [
            InventoryItem(
                appid=730,
                contextid="2",
                assetid="1",
                classid="10",
                instanceid="20",
                market_name="AK-47 | Redline",
                type="Rifle",
                tags=[{"category": "Rarity", "localized_tag_name": "Classified"}],
            )
        ]

        output = self.formatter.format_inventory("Alice", "CS2", items)

        self.assertIn("# Alice 的 CS2 库存", output)
        self.assertIn("AK-47 | Redline", output)
        self.assertIn("Classified", output)


if __name__ == "__main__":
    unittest.main()
