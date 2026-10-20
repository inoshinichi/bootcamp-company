# ファイル構成

## プラグインの構成

```
bootcamp-company/
├── .claude-plugin/
│   └── marketplace.json        ← マーケットプレース登録情報
├── .agents/                    ← コーデックス版の登録情報
├── .github/
│   └── workflows/
│       └── deploy-docs.yml     ← 説明サイトを作る（手で動かしたときだけ）
├── plugins/
│   └── company/
│       ├── .claude-plugin/
│       │   └── plugin.json     ← プラグインの情報
│       └── skills/
│           └── company/
│               ├── SKILL.md    ← スキル定義（ワークフロー全体）
│               ├── references/
│               │   ├── connections.md         ← 連携の手順（正本）
│               │   ├── connections-legacy.md  ← 古い連携の手順（予備）
│               │   ├── organization.md        ← 組織運営の絶対ルール
│               │   ├── departments.md         ← 部署テンプレート集
│               │   └── claude-md-template.md  ← CLAUDE.md 生成テンプレート
│               └── scripts/    ← 読むだけの道具（メール・カレンダーなど）
├── codex/                      ← コーデックス版
├── packages/                   ← ダッシュボードのコード（今は案内していない）
├── tests/
├── docs/                       ← 説明（VitePress）
├── package.json
├── README.md
└── LICENSE
```

## 生成される組織構成

`/company` 実行後に作られる `.company/` フォルダの構成です。

### 初期状態

```
.company/
├── CLAUDE.md              ← 組織ルール・オーナー情報
├── flow-map.md            ← 連携表（部署どうしの受け渡し）
└── secretary/
    ├── CLAUDE.md           ← 秘書の振る舞いルール
    ├── inbox/              ← クイックキャプチャ
    ├── todos/              ← 日次タスク管理
    │   └── YYYY-MM-DD.md
    ├── notes/              ← 壁打ち・相談メモ
    ├── manuals/            ← 秘書室の手順書 + INDEX.md
    ├── work-log.md         ← 作業の記録（1作業1行）
    └── experience/         ← ケース記録 + INDEX.md
```

### 部署追加後の例

```
.company/
├── CLAUDE.md
├── secretary/
│   ├── CLAUDE.md
│   ├── inbox/
│   ├── todos/
│   └── notes/
├── research/              ← 追加された部署
│   ├── CLAUDE.md
│   ├── manuals/
│   ├── inbox/
│   └── topics/
└── pm/                    ← 追加された部署
    ├── CLAUDE.md
    ├── manuals/
    ├── inbox/
    ├── projects/
    └── tickets/
```

## ファイル命名規則

| パターン | 形式 | 例 |
|---------|------|-----|
| 日次ファイル | `YYYY-MM-DD.md` | `2026-03-16.md` |
| トピックファイル | `kebab-case.md` | `competitor-analysis.md` |
| 意思決定ログ | `YYYY-MM-DD-decisions.md` | `2026-03-16-decisions.md` |
| テンプレート | `_template.md` | `_template.md` |

## TODO形式

```markdown
- [ ] タスク内容 | 優先度: 高/通常/低 | 期限: YYYY-MM-DD
- [x] 完了タスク | 完了: YYYY-MM-DD
```

## 運用ルール

- **同日1ファイル**: 同じ日付のファイルが存在する場合は追記する
- **日付チェック**: ファイル操作前に必ず今日の日付を確認
- **上書き禁止**: 既存ファイルは追記のみ
- **迷ったら inbox**: 分類に迷ったら `secretary/inbox/` に入れる


## 手順書・作業の記録・連携表

```
.company/
├── flow-map.md            ← 連携表（部署どうしの受け渡し）
├── secretary/
│   ├── work-log.md        ← 作業の記録（1作業1行）
│   └── manuals/           ← 秘書室の手順書 + INDEX.md
└── <部署>/
    └── manuals/           ← その部署の手順書 + INDEX.md
```

詳細はプラグイン内の `references/organization.md`（組織運営の絶対ルール）。
