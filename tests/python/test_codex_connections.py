"""
コーデックス版の連携の正本（codex/src/connections-codex.md）の形のテスト。
  python3 -m unittest discover -s tests/python -v
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "codex" / "src" / "connections-codex.md"
CLAUDE_DOC = ROOT / "plugins" / "company" / "skills" / "company" / "references" / "connections.md"


def section(text, n):
    """§n の見出しから次の §（または終わり）までを返す。"""
    m = re.search(rf"^## §{n}\..*?(?=^## §\d+\.|\Z)", text, re.S | re.M)
    return m.group(0) if m else ""


class TestCodexConnections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")

    def test_sections_0_to_9_in_order(self):
        heads = re.findall(r"^## §(\d+)\.", self.text, re.M)
        self.assertEqual(heads, [str(i) for i in range(10)])

    def test_section_titles_match_claude_version(self):
        claude = CLAUDE_DOC.read_text(encoding="utf-8")
        for n in range(9):
            c = re.search(rf"^## §{n}\.\s*(\S+)", claude, re.M)
            x = re.search(rf"^## §{n}\.\s*(\S+)", self.text, re.M)
            self.assertIsNotNone(c, f"Claude 版に §{n} が無い")
            self.assertIsNotNone(x, f"コーデックス版に §{n} が無い")
        self.assertRegex(self.text, re.compile(r"^## §9\. ブラウザ（拡張機能）", re.M))

    def test_top_rules_come_first(self):
        top = self.text.split("## §0.")[0]
        self.assertIn("🔴", top)
        for word in ["送信", "削除", "アーカイブ", "ラベル", "予定の追加", "投稿",
                     "購入", "「送って」", "「押して」", "パスワードは会話に貼らせない",
                     "~/.config/bootcamp-company"]:
            self.assertIn(word, top, word)

    def test_section7_has_browser_row(self):
        s7 = section(self.text, 7)
        self.assertRegex(s7, re.compile(r"^\| ブラウザ \|", re.M))

    def test_section8_has_browser_line(self):
        s8 = section(self.text, 8)
        self.assertIn("## 連携の状態", s8)
        self.assertRegex(s8, re.compile(r"^- ブラウザ:", re.M))
        self.assertIn(".company/CLAUDE.md", s8)

    def test_section0_covers_windows_login_and_tools(self):
        s0 = section(self.text, 0)
        self.assertIn("PowerShell", s0)
        self.assertIn("codex login status", s0)
        self.assertIn("py -3", s0)
        self.assertIn("Get-ChildItem", s0)

    def test_section1_has_dns_commands(self):
        s1 = section(self.text, 1)
        self.assertIn("nslookup -type=mx", s1)
        self.assertIn("Resolve-DnsName", s1)

    def test_section2_lists_apps(self):
        s2 = section(self.text, 2)
        for app in ["Gmail", "Google Calendar", "Google Drive", "Outlook Email",
                    "Outlook Calendar", "SharePoint", "Teams", "Slack", "/apps"]:
            self.assertIn(app, s2, app)
        self.assertIn("全体管理者", s2)

    def test_section9_has_store_url_and_steps(self):
        s9 = section(self.text, 9)
        self.assertIn("https://chromewebstore.google.com/detail/chatgpt/hehggadaopoacecdllhhajmbjkdcmajg", s9)
        for word in ["入れる", "つなぐ", "確かめる", "入れられないとき", "_resume.md"]:
            self.assertIn(word, s9, word)

    def test_no_claude_only_commands_for_windows(self):
        # PowerShell の節に Git Bash 専用の cygpath を残さない
        s4 = section(self.text, 4)
        self.assertNotIn("$(cygpath", s4)


if __name__ == "__main__":
    unittest.main()
