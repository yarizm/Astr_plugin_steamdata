import unittest

from astrbot_plugin_steamdata.services.steam_api import SteamAPIService


class FakeSteamAPIService(SteamAPIService):
    def __init__(self, responses):
        super().__init__(api_key="test-key")
        self.responses = responses

    async def _get_json(self, url, params=None, context="Steam API"):
        for key, value in self.responses.items():
            if key in url:
                return value
        return None


class SteamAPIServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_game_data_uses_fake_responses(self):
        service = FakeSteamAPIService(
            {
                "storesearch": {"items": [{"id": 730}]},
                "appdetails": {
                    "730": {
                        "success": True,
                        "data": {
                            "name": "Counter-Strike 2",
                            "short_description": "A tactical shooter.",
                            "developers": ["Valve"],
                            "publishers": ["Valve"],
                            "genres": [{"description": "Action"}],
                            "release_date": {"date": "21 Aug, 2012"},
                            "platforms": {"windows": True},
                            "is_free": True,
                        },
                    }
                },
                "appreviews": {
                    "query_summary": {
                        "total_reviews": 10,
                        "total_positive": 8,
                        "review_score_desc": "Mostly Positive",
                    },
                    "reviews": [
                        {
                            "voted_up": True,
                            "review": "Good",
                            "language": "english",
                            "author": {"playtime_forever": 120},
                        }
                    ],
                },
                "GetNumberOfCurrentPlayers": {"response": {"player_count": 123}},
            }
        )

        data = await service.fetch_game_data("CS2")

        self.assertEqual(data.appid, 730)
        self.assertEqual(data.name, "Counter-Strike 2")
        self.assertTrue(data.is_free)
        self.assertEqual(data.current_players, 123)
        self.assertEqual(data.positive_rate, 80.0)
        self.assertEqual(len(data.reviews), 1)

    async def test_network_like_empty_responses_do_not_raise(self):
        service = FakeSteamAPIService({})

        self.assertIsNone(await service.search_game("missing"))
        self.assertIsNone(await service.resolve_vanity_url("alice"))
        self.assertIsNone(await service.get_player_summary("76561198000000000"))
        self.assertEqual(await service.get_owned_games("76561198000000000"), [])
        self.assertEqual(await service.get_user_inventory("76561198000000000", 730), [])


if __name__ == "__main__":
    unittest.main()
