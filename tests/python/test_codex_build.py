"""コーデックス版 company スキル（codex/skills/company）の生成物の確かめ。"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "codex" / "skills" / "company"
SRC = ROOT / "plugins" / "company" / "skills" / "company"


def frontmatter(text):
    assert text.startswith("---\n")
    end = text.index("\n---\n", 4)
    return text[4:end]


def parse_fm(fm):
    """name と description（> の折り返し形も）を読む簡単な読み取り。"""
    out, key, buf = {}, None, []
    for line in fm.splitlines():
        if line and not line.startswith(" ") and ":" in line:
            if key:
                out[key] = " ".join(buf).strip()
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            buf = [] if val in (">", "|", ">-", "|-") else [val]
        elif key:
            buf.append(line.strip())
    if key:
        out[key] = " ".join(buf).strip()
    return out


class CodexBuildTest(unittest.TestCase):
    def test_check_passes(self):
        r = subprocess.run([sys.executable, str(ROOT / "codex" / "build.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_frontmatter(self):
        fm = parse_fm(frontmatter((OUT / "SKILL.md").read_text(encoding="utf-8")))
        self.assertEqual(fm.get("name"), "company")
        self.assertLessEqual(len(fm["name"]), 64)  # codex の上限（MAX_NAME_LEN）
        self.assertTrue(fm.get("description"))
        self.assertLessEqual(len(fm["description"]), 1024)  # agent skills の標準の上限
        self.assertNotIn("trigger", fm)

    def test_no_claude_trigger(self):
        text = (OUT / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("trigger:", text)
        self.assertEqual(text.count("\n---\n", 0, 2000) >= 1, True)
        self.assertIn("$company", text)
        self.assertIn("connections-codex.md", text)

    def test_body_included(self):
        text = (OUT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("# bootcamp-company（仮想カンパニー v3）", text)

    def test_references_and_scripts(self):
        for sub in ("references", "scripts"):
            want = {p.name for p in (SRC / sub).iterdir()
                    if p.name != "__pycache__" and not p.name.endswith(".pyc")}
            got = {p.name for p in (OUT / sub).iterdir()}
            self.assertTrue(want <= got, f"{sub}: 足りない {want - got}")
            self.assertFalse(any(n == "__pycache__" or n.endswith(".pyc") for n in got))


if __name__ == "__main__":
    unittest.main()
