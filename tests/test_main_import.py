import py_compile
import unittest


class MainImportTests(unittest.TestCase):
    def test_main_py_compiles(self):
        py_compile.compile("main.py", doraise=True)

    def test_main_can_import_with_local_fallback(self):
        from main import AstrBotPluginSteamData

        self.assertEqual(AstrBotPluginSteamData.__name__, "AstrBotPluginSteamData")


if __name__ == "__main__":
    unittest.main()
