import unittest

from astrbot_plugin_steamdata.config import normalize_config


class ConfigTests(unittest.TestCase):
    def test_default_config_can_be_loaded(self):
        config = normalize_config({})

        self.assertEqual(config.steam_api_key, "")
        self.assertEqual(config.price_region, "cn")
        self.assertEqual(config.review_count, 5)
        self.assertEqual(config.request_timeout, 15)
        self.assertTrue(config.enable_fallback_commands)

    def test_empty_api_key_does_not_crash(self):
        config = normalize_config({"steam_api_key": None})

        self.assertEqual(config.steam_api_key, "")

    def test_invalid_numeric_values_fall_back(self):
        config = normalize_config({"review_count": "bad", "request_timeout": object()})

        self.assertEqual(config.review_count, 5)
        self.assertEqual(config.request_timeout, 15)

    def test_numeric_values_are_clamped(self):
        config = normalize_config({"review_count": 1000, "request_timeout": 1})

        self.assertEqual(config.review_count, 50)
        self.assertEqual(config.request_timeout, 3)


if __name__ == "__main__":
    unittest.main()
