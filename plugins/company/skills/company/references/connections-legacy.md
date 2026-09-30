# 予備: 古い連携手順（Google Cloud・Azure・Slack Bot）

⚠️ **最初からこの手順を案内しない。** 正は `references/connections.md`（公式の連携＋サーバーに取りに行く道具）。
この手順を使うのは、次のような**どうしても公式の連携が使えない**ときだけ:

- Claude のアカウントではなく APIキーでしかログインできない
- 以前この手順で連携済みで、そのまま使い続けたい受講者（2026-10 より前の受講者）

同梱の `.mcp.json`（gmail / google-calendar / google-drive / ms-365 / slack）は、この古い手順のためのもの。
公式の連携でつないだ受講者は、これらを使わない（公式の `mcp__claude_ai_...` を使う）。

---

## Google 連携セットアップ（Gmail + Calendar + Drive 一括 / 初回のみ）

ユーザーが「Google 連携セットアップして」「Gmail 使いたい」「Drive 使いたい」「Calendar 連携」等と言ったら、**ステップバイステップで案内** する。
1つの Google Cloud プロジェクトで Gmail/Calendar/Drive すべての OAuth クライアントを共用できる。

**秘書はステップ毎に「次に進みますか？」と確認しながら進める。Claude が自動でできる部分（コマンド実行など）は秘書が代行する。**

### Step 1: Google Cloud Console でプロジェクト作成（人間操作）
1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. プロジェクト名を任意で（例: `my-company-mcp`）作成

### Step 2: 必要な API を有効化（人間操作）
「APIとサービス」→「ライブラリ」で以下を順に有効化:
- Gmail API
- Google Calendar API
- Google Drive API

### Step 3: OAuth 同意画面の設定（人間操作）
「OAuth 同意画面」→ User Type: **外部** を選択 → 必須項目入力（アプリ名・サポートメール等）。
公開ステータスは **「テスト」のままで OK**（本番公開・Google審査は不要）。

### 🟥 Step 3.5: テストユーザーに自分のメールアドレスを追加（人間操作・**最重要・絶対に飛ばさない**）

「OAuth 同意画面」→「テストユーザー」→「ADD USERS / ユーザーを追加」→ **自分の Gmail アドレスを入力** → 保存。

> ⚠️ **ここを飛ばすと、後で必ず `アクセスをブロック: …が Google の審査プロセスを完了していません`／`access_denied` エラーになります。**
> これは受講者が最もつまずく原因No.1です。秘書はこのステップを必ず明示し、「自分のアドレスを追加しましたか？」と確認してから次に進むこと。
>
> 📌 補足（持ち帰り知識）: 公開ステータスが「テスト」の間は、Google の機密スコープ（Gmail等）の認証が **約7日で失効** します。失効したら「Gmail 連携を再認証して」と秘書に言えば 30秒で復旧できます（同意画面をブラウザでもう一度許可するだけ）。

### Step 4: OAuth クライアント ID 作成（人間操作）
「認証情報」→「OAuth クライアント ID 作成」
- アプリの種類: **デスクトップアプリ**（⚠️「ウェブアプリケーション」を選ぶと `redirect_uri_mismatch` になります。必ずデスクトップアプリ）
- 名前: `bootcamp-company-mcp`（任意）
- 作成後、鍵ファイル（JSON）を **ダウンロード**

### Step 5: 鍵ファイルを配置（**ここから秘書が自動で代行**）

Gmail・Calendar・Drive の3つは **同じ1つの鍵ファイル（`gcp-oauth.keys.json`）を共用** します。
だから配置は **1ファイルを1箇所に置くだけ**。秘書がダウンロードしたファイルのパスを聞いて、Bash で実行:

```bash
mkdir -p ~/.gmail-mcp
cp "<ダウンロードした鍵ファイルのパス>" ~/.gmail-mcp/gcp-oauth.keys.json
echo "配置完了。HOME は $HOME です（次の Step 5.5 で使います）"
```

> Calendar(@cocal)と Drive(@isaacphi)は固定パスを持たず、環境変数で鍵の場所を教える方式です（各 MCP の公式仕様）。
> Gmail と同じ `~/.gmail-mcp/gcp-oauth.keys.json` を指せば共用でき、**追加のコピーは不要**です。

### Step 5.5: .mcp.json の絶対パスを実ユーザー名に置換（**秘書が自動で代行**）

プラグイン同梱の `.mcp.json` は Calendar/Drive 向けに `GOOGLE_OAUTH_CREDENTIALS` / `GDRIVE_CREDS_DIR` を持つが、
**MCP の環境変数は `~` や `$HOME` を展開しない**ため、絶対パスの `REPLACE_ME` を実ユーザー名へ置き換える必要がある。
秘書は `echo $HOME` で確認した上で、ユーザー設定の `.mcp.json`（`~/.claude.json` 等の該当 mcpServers）または該当環境変数に
`/Users/<実ユーザー名>/.gmail-mcp/gcp-oauth.keys.json`（Drive は `/Users/<実ユーザー名>/.gmail-mcp`）を反映する。

> 💡 実装メモ: 同梱 `plugins/company/.mcp.json` の `REPLACE_ME` はプレースホルダ。受講者環境の HOME に合わせて秘書が置換する。

### Step 6: Claude Code を再起動（人間操作）

🔖 **再起動を案内する前に、必ず `secretary/_resume.md` にしおりを書く**（「再起動しおりプロトコル」参照）。
その上でユーザーに「Claude Code を一度終了して再起動してください」と案内。

### Step 7: 初回 OAuth 認証（半自動）

再起動後、最初に Gmail/Calendar/Drive の MCP ツールを使うと、ブラウザが自動で開いて Google ログイン → 許可 → 完了。
（この Step が完了したら `_resume.md` を削除してしおりを閉じる。）
**Step 3.5 でテストユーザーに追加したのと同じアカウントでログインすること**（別アカウントだと空のメールボックスに繋がって「動いてるのに何も出ない」状態になる）。

完了後、「メール送って」「予定確認して」「Drive のあの資料」など試してみる。

> ❗ うまくいかないとき（秘書の対処手順）:
> 1. まず `test -f ~/.gmail-mcp/gcp-oauth.keys.json && echo OK` で鍵の配置を確認。
> 2. 実際に Gmail MCP を1回叩いてエラー文字列を取得する（推測で断定しない）。
> 3. `access_denied`／`403`／`審査プロセス` を含む → **Step 3.5 のテストユーザー追加漏れ**。追加すれば再起動不要でもう一度試すだけ。
> 4. `redirect_uri_mismatch` → Step 4 を「ウェブアプリ」で作った疑い。デスクトップアプリで作り直し。
> 5. 鍵は正しいのに繋がらず、現セッションで一度も成功していない → 設定前に起動した Claude Code のまま。再起動を案内。
> 6. 原因が確定するまで「テストユーザー漏れだと思います」等の**確率での断定はしない**。必ず実エラーで確定してから案内する。

---

## Microsoft 連携セットアップ（Outlook + Calendar + OneDrive + Teams 一括 / 初回のみ）

ユーザーが「Microsoft 連携セットアップして」「Outlook 使いたい」等と言ったら、ステップバイステップで案内する。
ms-365-mcp-server は Outlook（メール+カレンダー）+ OneDrive + Teams を1つでカバーする統合 MCP。

### Step 1: Azure Portal でアプリ登録（人間操作）
1. [Azure Portal](https://portal.azure.com/) → 「アプリの登録」→ 新規登録
2. 名前: `bootcamp-company-mcp`（任意）
3. サポートされるアカウントの種類: **このディレクトリのアカウントのみ**（個人MS365アカウントなら **個人 Microsoft アカウント**）
4. リダイレクト URI: パブリッククライアント / `http://localhost`

### Step 2: API のアクセス許可を追加（人間操作）
「APIのアクセス許可」→ Microsoft Graph → **委任されたアクセス許可** で以下を追加:
- `Mail.ReadWrite` （Outlook メール）
- `Calendars.ReadWrite` （Outlook カレンダー）
- `Files.ReadWrite` または `Files.ReadWrite.All` （OneDrive）
- `Chat.ReadWrite` （Teams、Q4 で teams 選択時のみ）
- `User.Read` （基本）

### Step 3: 認証設定 → 公開クライアントフロー (人間操作)

「認証」タブで「**パブリッククライアントフローを許可する**」を **はい** に切り替え。

### Step 4: アプリ（クライアント）ID をコピー（人間操作）

「概要」タブからクライアントID（GUID）をコピー。

### Step 5: 環境変数を設定（**秘書が自動で代行可**）

ユーザーがクライアントIDを伝えてくれたら、秘書が以下を Bash で実行:
```bash
mkdir -p ~/.config/ms-365-mcp
cat > ~/.config/ms-365-mcp/.env <<'EOL'
MS365_MCP_CLIENT_ID=<コピーしたクライアントID>
EOL
```

### Step 6: Claude Code 再起動 → ログイン

🔖 **再起動を案内する前に `secretary/_resume.md` にしおりを書く**（「再起動しおりプロトコル」参照）。
再起動後、秘書が ms-365 の `login` ツールを呼ぶ（デバイスコード/ブラウザでMicrosoftログインのURLが出る）→ ログイン後 `verify-login` で確認。
利用可能になったら `_resume.md` を削除してしおりを閉じる。

---

## Slack 連携セットアップ（Bot Token 方式 / 初回のみ）

ユーザーが「Slack 連携セットアップして」と言ったら、以下を案内する。

### Step 1: Slack App を作成（人間操作）
1. [Slack API: Your Apps](https://api.slack.com/apps) → Create New App → From scratch
2. App 名: `bootcamp-company-bot`（任意）

### Step 2: Bot Token Scopes を設定（人間操作）
「OAuth & Permissions」→ Bot Token Scopes で以下を追加:
- `chat:write`
- `channels:read`
- `channels:history`
- `users:read`

### Step 3: ワークスペースにインストール（人間操作）
「Install to Workspace」をクリック → Bot User OAuth Token (`xoxb-...`) をコピー

### Step 4: Team ID を取得（人間操作）
ワークスペースの URL から Team ID を確認、または「Settings & administration → Workspace settings → About Settings」で確認

### Step 5: 環境変数を設定（**秘書が自動で代行可**）

ユーザーが Bot Token と Team ID を伝えてくれたら、秘書が以下を Bash で実行:
```bash
mkdir -p ~/.config/slack-mcp
cat > ~/.config/slack-mcp/.env <<'EOL'
SLACK_BOT_TOKEN=<xoxb-で始まるToken>
SLACK_TEAM_ID=<Team ID>
EOL
```

### Step 6: Claude Code 再起動 → 利用開始

「#general に投稿して」「DM 送って」など試す。

---

## Google Chat / Chatwork / Teams（Microsoft 連携経由）の補足

- **Teams**: 上記「Microsoft 連携セットアップ」で `Chat.ReadWrite` を追加すれば一緒に使える
- **Google Chat**: 専用 MCP は限定的。Google Workspace API + curl 経由の対応を `secretary/notes/` に書き留めて、必要に応じて手動連携を案内する
- **Chatwork**: API トークンを発行 → ChatWork API を curl/HTTP 経由で呼ぶ簡易連携を案内（フル MCP なし）

