#!/usr/bin/env python3
"""コーデックス版 company スキルを作る。

plugins/company/skills/company/ の本文・references・scripts と
codex/src/header.md（読み替えの節）・codex/src/connections-codex.md から
codex/skills/company/ を作り直す。codex/skills/company 以外は触らない。

    python3 codex/build.py          # 作り直す
    python3 codex/build.py --check  # 最新かだけを確かめる（違えば終了コード 1）
"""
from __future__ import annotations

import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

CODEX = Path(__file__).resolve().parent
ROOT = CODEX.parent
SRC_SKILL = ROOT / "plugins" / "company" / "skills" / "company"
HEADER = CODEX / "src" / "header.md"
CONN_CODEX = CODEX / "src" / "connections-codex.md"
OUT = CODEX / "skills" / "company"


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + len("\n---\n"):].lstrip("\n")
    return text


def _ignore(_dir, names):
    return [n for n in names if n == "__pycache__" or n.endswith(".pyc") or n == ".DS_Store"]


def build(dest: Path, quiet: bool = False) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    header = HEADER.read_text(encoding="utf-8").rstrip("\n") + "\n\n"
    body = strip_frontmatter((SRC_SKILL / "SKILL.md").read_text(encoding="utf-8"))
    (dest / "SKILL.md").write_text(header + body, encoding="utf-8")
    shutil.copytree(SRC_SKILL / "references", dest / "references", ignore=_ignore)
    shutil.copytree(SRC_SKILL / "scripts", dest / "scripts", ignore=_ignore)
    if CONN_CODEX.exists():
        shutil.copy2(CONN_CODEX, dest / "references" / "connections-codex.md")
    elif not quiet:
        print("codex/src/connections-codex.md はまだ無い（別の係が作っています）。それ以外を作ります。")


def same_tree(a: Path, b: Path) -> bool:
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__", ".DS_Store"])
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    if mismatch or errors:
        return False
    return all(same_tree(a / d, b / d) for d in cmp.common_dirs)


def main(argv: list[str]) -> int:
    if "--check" in argv:
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "company"
            build(fresh, quiet=True)
            if OUT.exists() and same_tree(fresh, OUT):
                print("codex/skills/company は最新です。")
                return 0
        print("codex/skills/company が古いです。python3 codex/build.py を流してください。")
        return 1
    build(OUT)
    print(f"作りました: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
