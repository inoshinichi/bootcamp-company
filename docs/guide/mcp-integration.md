# MCP連携ガイド

> **2026-10 改訂**: メール・カレンダー・ファイル・Slack は、まず Claude の公式の連携（claude.ai の「コネクター」）でつなぎます。レンタルサーバーのメールや iPhone のカレンダーなどは、プラグイン内蔵の読むだけの道具を使います。受講者は準備の紙（[研修の前の準備](./junbi)）を、秘書はプラグイン内の `references/connections.md` を正としてください。このページの下の方法は、公式の連携に無いサービスを追加するときの参考です。

cc-company は MCP（Model Context Protocol）サーバーと連携できます。MCP サーバーを設定すると、秘書が外部サービスを直接操作できるようになります。

## 仕組み

cc-company 側に特別な設定は不要です。Claude Code に MCP サーバーを追加するだけで、秘書が自動的に活用します。

```
あなた: 明日の14時にA社とミーティング入れて

秘書: カレンダーに追加しました！
      TODOにも「A社ミーティング資料準備」を入れておきますね。
```

## おすすめ MCP サーバー

### Notion（公式）

ナレッジベースやデータベースとの連携。秘書がNotionのページを参照・更新できます。

**方法1: OAuth（おすすめ）**

```bash
claude mcp add-json --scope user notion '{"type":"http","url":"https://mcp.notion.com/mcp"}'
```

実行後、ブラウザで OAuth 認証が開きます。API キーの手動設定は不要です。

**方法2: API トークン**

```bash
claude mcp add --scope user notion -e NOTION_TOKEN=ntn_YOUR_TOKEN -- npx -y @notionhq/notion-mcp-server
```

[Notion Integrations](https://www.notion.so/my-integrations) で API トークンを作成してください。

**できること:**
- Notion ページの参照・作成・更新
- データベースの検索・更新
- 既存のナレッジベースを秘書が参照

---

### Google Calendar（予備）

> ⚠️ **通常は使いません。** Google カレンダーは Claude の「コネクター」のボタンでつなぎます（[準備の紙](./junbi)）。下は、コネクターが使えない特別な事情があるときの**予備の手順**です（Google Cloud での鍵づくりが必要で、初心者には難しいです）。

スケジュール管理。秘書がミーティングの登録やリマインダーを設定できます。

```bash
claude mcp add --scope user google-calendar \
  -e GOOGLE_OAUTH_CREDENTIALS=/path/to/gcp-oauth.keys.json \
  -- npx -y @cocal/google-calendar-mcp
```

**事前準備:**
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. Calendar API を有効化
3. OAuth 2.0 認証情報を作成（デスクトップアプリ）
4. 認証情報の JSON をダウンロード

**できること:**
- 予定の作成・確認・変更・削除
- 今日・今週のスケジュール表示
- 空き時間の確認
- 繰り返し予定の管理

---

### GitHub（公式）

リポジトリ管理。開発部門と相性が良いです。

**方法1: HTTP（おすすめ）**

```bash
claude mcp add-json --scope user github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer YOUR_GITHUB_PAT"}}'
```

**方法2: Docker**

```bash
claude mcp add --scope user github \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=YOUR_PAT \
  -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server
```

[GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) でトークンを作成してください。

**できること:**
- Issue の作成・確認・検索
- PR の管理・レビュー
- リポジトリの状況確認
- コード検索

---

### Slack（公式）

> まずは Claude の「コネクター」（https://claude.ai/customize/connectors ）で Slack を探してください。使えないときだけ、下の方法を使います。

チームコミュニケーション。営業部門やPM部門と連携して活用できます。

**方法1: OAuth（おすすめ）**

```bash
claude mcp add-json --scope user slack '{"type":"http","url":"https://mcp.slack.com/mcp","oauth":{"clientId":"1601185624273.8899143856786","callbackPort":3118}}'
```

実行後、ブラウザで Slack の OAuth 認証が開きます。

**方法2: プラグインとしてインストール**

```bash
claude plugin install slack
```

**できること:**
- メッセージの送信・確認
- チャンネルの状況把握
- ユーザー情報の参照
- クライアントへの連絡リマインダー

::: warning 注意
ワークスペースの管理者が MCP 連携を許可している必要があります。
:::

---

## 設定方法

### コマンドで追加（おすすめ）

上記の `claude mcp add` コマンドを実行するだけです。設定後、Claude Code を再起動してください。

`--scope user` を付けると、どのフォルダで開いても使えます。付けないと、そのとき開いていたフォルダだけで使える設定（local）になり、会社フォルダ以外で開くと見えなくなります。

### 設定ファイルの場所

MCP サーバーの設定は `~/.claude/settings.json` には書きません。

- **自分のパソコンのどのフォルダでも使う（`--scope user`）・そのフォルダだけで使う（local）:** `~/.claude.json`（`claude mcp add` が書き込みます。手で直す必要はありません）
- **フォルダの中に置いて共有する（`--scope project`）:** そのフォルダの `.mcp.json`

```json
{
  "mcpServers": {
    "notion": {
      "type": "http",
      "url": "https://mcp.notion.com/mcp"
    }
  }
}
```

（上は `.mcp.json` の書き方の例です）

---

## 秘書との連携例

MCP サーバーを設定すると、秘書が自然に活用します。

```
> 今週のスケジュール教えて
秘書: カレンダーを確認しますね。
      - 月曜 10:00 A社定例
      - 水曜 14:00 B社ヒアリング
      - 金曜 終日 確定申告締切
      水曜のB社、提案書の準備は大丈夫ですか？

> A社との議事録をNotionにまとめて
秘書: 承知しました。Notionに議事録ページを作成しました。
      secretary/notes/ にもサマリーを保存しておきますね。

> このバグのIssue立てて
秘書: GitHubにIssueを作成しました。
      engineering/debug-log/ にもログを残しておきます。
```

## MCP なしでも問題なし

MCP サーバーがなくても cc-company は完全に動作します。秘書は `.company/` フォルダ内でのファイル管理だけでも十分に機能します。

MCP は「あるともっと便利」なオプションです。
