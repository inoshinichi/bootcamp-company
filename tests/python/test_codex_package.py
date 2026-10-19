"""コーデックス版の入れ物（マーケットプレイスとプラグインの定義）の形を確かめる。"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_ROOT = ROOT / "codex"
PLUGIN_JSON = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
README = PLUGIN_ROOT / "README.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CodexMarketplaceTest(unittest.TestCase):
    def setUp(self):
        self.mp = load(MARKETPLACE)

    def test_name_matches_claude_marketplace(self):
        # 同じリポジトリを Claude でもコーデックスでも同じ名前で呼べるようにする
        self.assertEqual(self.mp["name"], load(CLAUDE_MARKETPLACE)["name"])
        self.assertEqual(self.mp["name"], "bootcamp-company")

    def test_single_company_plugin_with_local_source(self):
        plugins = self.mp["plugins"]
        self.assertEqual(len(plugins), 1)
        p = plugins[0]
        self.assertEqual(p["name"], "company")
        src = p["source"]
        self.assertEqual(src["source"], "local")
        # コーデックスはローカルの場所が "./" で始まり、根の外へ出ないことを求める
        self.assertTrue(src["path"].startswith("./"))
        self.assertNotIn("..", src["path"])
        self.assertEqual((ROOT / src["path"]).resolve(), PLUGIN_ROOT.resolve())

    def test_policy_values_are_known(self):
        policy = self.mp["plugins"][0].get("policy", {})
        if "installation" in policy:
            self.assertIn(
                policy["installation"],
                {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"},
            )
        if "authentication" in policy:
            self.assertIn(policy["authentication"], {"ON_INSTALL", "ON_USE"})


class CodexPluginManifestTest(unittest.TestCase):
    def setUp(self):
        self.pj = load(PLUGIN_JSON)

    def test_name_and_version(self):
        self.assertEqual(self.pj["name"], "company")
        self.assertRegex(self.pj["version"], r"^\d+\.\d+\.\d+$")
        claude_version = load(CLAUDE_MARKETPLACE)["plugins"][0]["version"]
        self.assertEqual(self.pj["version"], claude_version)

    def test_skills_points_to_codex_skills(self):
        skills = self.pj["skills"]
        self.assertTrue(skills.startswith("./"))
        self.assertEqual(
            (PLUGIN_ROOT / skills).resolve(), (PLUGIN_ROOT / "skills").resolve()
        )

    def test_does_not_reference_claude_paths(self):
        text = PLUGIN_JSON.read_text(encoding="utf-8")
        self.assertNotIn(".claude-plugin", text)
        self.assertNotIn("plugins/company", text)

    def test_interface_has_display_fields(self):
        iface = self.pj["interface"]
        for key in ("displayName", "shortDescription", "developerName", "category"):
            self.assertTrue(iface.get(key), key)


class CodexReadmeTest(unittest.TestCase):
    def setUp(self):
        self.text = README.read_text(encoding="utf-8")

    def test_install_commands_match_names(self):
        mp_name = load(MARKETPLACE)["name"]
        plugin_name = load(PLUGIN_JSON)["name"]
        self.assertIn("codex plugin marketplace add inoshinichi/bootcamp-company", self.text)
        self.assertIn(f"codex plugin add {plugin_name}@{mp_name}", self.text)
        self.assertIn(f"codex plugin marketplace upgrade {mp_name}", self.text)

    def test_mentions_invocation_and_connections_doc(self):
        self.assertIn("$company", self.text)
        self.assertIn("skills/company/references/connections-codex.md", self.text)

    def test_has_mac_and_windows_sections(self):
        self.assertTrue(re.search(r"^### Mac", self.text, re.M))
        self.assertTrue(re.search(r"^### Windows", self.text, re.M))


if __name__ == "__main__":
    unittest.main()
