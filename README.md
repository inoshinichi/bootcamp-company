# bootcamp-company

ブートキャンプ受講者向け 仮想組織プラグイン（Claude Code）。
[Shin-sibainu/cc-company](https://github.com/Shin-sibainu/cc-company)（MIT License）を fork し、AI初学者の中小企業経営者でも 5分で「自分専用のAI組織」が立ち上がるよう調整。

## このプラグインで何ができる？

`/company` を実行すると、**あなた専用の秘書** が窓口になります。

- 「今日やることは？」 → 秘書が TODO を整理
- 「○○について調べて」 → 必要に応じてリサーチ部門を提案・作成
- 「LP作って」 → マーケティング部門に振り分け
- 「決算書類どうしたら？」 → 経理部門で対応

**最初は秘書だけ。仕事を進める中で部署が自然に増えていきます。**
さらに、同じ依頼が繰り返されると「専門エージェント」を提案して、その分野のプロが自動で立ち上がるようになります。

## こんな人におすすめ

- 中小企業の経営者で、自分の手と時間が足りないと感じている方
- AI を使い始めたばかりで、「結局何ができるの？」がつかめていない方
- ChatGPT に毎回 1から指示するのに疲れている方
- 業種は問いません（製造業、飲食、コンサル、士業、IT、EC、不動産、教育 など）

## インストール（招待された方限定）

このリポジトリは Private です。GitHub アカウントを Outside Collaborator として招待された方のみアクセス可能です。

### 受講者がやること: 3コマンドだけ

Claude Code を開いて、以下の3行を順に実行してください。**それ以降は秘書が全部案内します。**

```
/plugin marketplace add inoshinichi/bootcamp-company
/plugin install company@bootcamp-company
/company
```

> 💡 **「company プラグイン」と表示されますが正常です**
> マーケットプレイス名が `bootcamp-company`、その中の本体プラグイン名が `company` という構造です。

### 秘書が後で案内すること（受講者は事前に何も入れなくて OK）

| 案内タイミング | 内容 |
|---|---|
| `/company` 起動直後 | 5問オンボーディング（事業・目標・基盤・チャット・ダッシュボード） |
| オンボーディング完了時 | 環境に応じた連携プラン（Google / Microsoft / Slack） |
| 「アプリ作って」と言ったとき | obra/superpowers プラグインが必要なら、その場でインストールコマンドを案内 |
| 「Gmail 連携セットアップして」等で | OAuth 設定をステップバイステップで伴走 |

URL や手順を覚える必要はありません。秘書に話しかけて進めてください。

## 5分で立ち上がる初回セットアップ

```
> /company

秘書: はじめまして！あなたの秘書になります。
      まず、あなたの事業や活動を教えてください。

あなた: 製造業で、地元のホテル向けのアメニティを作っています

秘書: 今の目標や、日々困っていることがあれば教えてください。

あなた: 売上を伸ばしたいけど、営業が手薄。あと請求書まわりが煩雑

秘書: メール・カレンダー・ストレージは Google ベースですか？
      Microsoft ベースですか？

あなた: Microsoft です

秘書: 社内チャットは何を使っていますか？

あなた: Teams です

秘書: ブラウザで状況を確認できるダッシュボードがあります。
      セットアップしますか？

あなた: あとで

秘書: 秘書室のセットアップが完了しました！
      Microsoft 連携（Outlook + OneDrive + Teams）の手順を
      ステップバイステップで案内しますね...
```

これで `.company/` フォルダが作られ、**あなただけの秘書** が立ち上がります。

## 中核機能

### 7ステップ判断フロー
秘書は依頼を受けたとき、過去経験の検索 → 意図理解 → インプット洗い出し → 自律 / 協議判断 → 実行 → ケース記録 の流れで処理します。
都度の判断が積み上がり、組織が成長します。

### inbox/ システム
部署同士の通知や横断案件のステータス共有を `inbox/` で集約。秘書が定期的にサマリーします。

### 経験ファイル蓄積（自律成長の核）
ケース完了時に `secretary/experience/case-NNN-...md` を残します。同種ケースが3件以上溜まると、`patterns/<種別>.md` に統合知見が生成され、次回からの判断基準になります。

### 部署とエージェントの自然な追加
- 同領域のタスクが2回以上 → 部署作成を提案
- 同部署の同種専門作業が3回以上 → 専門エージェント作成を提案

最初は秘書ひとりからスタートし、使い込むほど組織が成長します。

## 部署テンプレート（必要に応じて秘書が提案）

| 部署 | キーワード |
|---|---|
| PM | プロジェクト、進捗、スケジュール |
| リサーチ | 調査、競合、市場、トレンド |
| マーケティング | コンテンツ、SNS、広告、LP |
| 開発 | 実装、設計、デバッグ |
| 経理 | 請求、経費、売上、確定申告 |
| 営業 | クライアント、提案、見積 |
| クリエイティブ | デザイン、ロゴ、ブランド |
| 人事 | 採用、チーム、オンボーディング |

## ハーネス開発（プロダクト開発機能）

「LP作って」「アプリ作って」「○○のシステム作って」と頼まれたら、秘書が **obra/superpowers** プラグインの各スキルを順に起動してハーネス開発を回します：

| Step | 使用スキル | 役割 |
|---|---|---|
| 1 | `superpowers:brainstorming` | アイデア（1〜4行）から要件をブレインストーミングで詰める |
| 2 | `superpowers:writing-plans` | 詳細な実装計画（plan.md）を生成 |
| 3 | `superpowers:executing-plans` + `superpowers:test-driven-development` | 計画通りに TDD で実装 |
| 4 | `superpowers:verification-before-completion` | 完了前に必ず検証コマンドを実行 |
| 5 | Playwright MCP（同梱） | 実機 UI テストで最終確認 |
| 任意 | `superpowers:requesting-code-review` | 第三者視点でコードレビュー |
| 任意 | `superpowers:dispatching-parallel-agents` | 独立タスクを並列実行 |
| バグ時 | `superpowers:systematic-debugging` | 体系的デバッグ |

ユーザーは「○○を作って」と言うだけ。秘書が上記のスキルを順に呼び出して進めます。

**注意**: superpowers プラグインを先にインストールしてください（上記のインストール手順 Step 1 参照）。

## 5問オンボーディング（あなたの環境に合わせて連携を提案）

`/company` を初回起動すると、秘書が5つの質問でお話を聞きます：

1. **事業・活動**（製造業？ コンサル？ EC？）
2. **目標・困りごと**（売上？ 業務効率？ 人手不足？）
3. **メール・カレンダー・ストレージの基盤** ← Google / Microsoft / 両方 / 使わない
4. **社内チャット** ← Teams / Google Chat / Slack / Chatwork / 使わない
5. ダッシュボード（任意）

3問目と4問目の回答に応じて、**あなたの環境に合った連携プランを秘書が動的に提案**します。

## 同梱 MCP サーバー（環境に応じて使い分け）

プラグインインストール時にすべての MCP が利用可能な状態になり、OAuth 設定が完了したものから順に動き始めます。

### 即利用可（OAuth不要）

| MCP | 用途 |
|---|---|
| **Playwright** | ブラウザ自動操作・スクレイピング・UIテスト |

### Google ベース利用者向け

| MCP | 用途 | OAuth設定 |
|---|---|---|
| **Gmail** | メール送受信・検索・下書き | Google Cloud Console |
| **Google Calendar** | 予定確認・追加・調整 | 同じ Google Cloud プロジェクト |
| **Google Drive** | ファイル検索・読込・保存 | 同じ Google Cloud プロジェクト |

→ **3つ合わせて 1つの OAuth クライアント** で済みます（10分）

### Microsoft ベース利用者向け

| MCP | 用途 | OAuth設定 |
|---|---|---|
| **ms-365**（統合） | Outlook メール / Outlook Calendar / OneDrive / Teams | Azure AD で1回アプリ登録 |

→ **メール+カレンダー+ストレージ+チャット 全部** を1つの MCP でカバー（10分）

### 社内チャット連携

| MCP | 用途 | OAuth設定 |
|---|---|---|
| **Slack** | Slack ワークスペースへの投稿・読込 | Slack Bot Token（5分） |

Teams 利用者は ms-365 MCP に含まれます。
Google Chat / Chatwork は専用 MCP が限定的なため、必要に応じて API キー経由で個別案内します。

## OAuth セットアップ手順（ステップバイステップ・秘書が伴走）

`/company` 起動後に「Google 連携セットアップして」「Microsoft 連携セットアップして」「Slack 連携セットアップして」と話しかけると、秘書がステップバイステップで案内します。**人間操作が必要な部分は明示し、Claude が自動でできる部分（コマンド実行・ファイル配置）は秘書が代行します。**

### Google 連携（Gmail + Calendar + Drive）の流れ

1. Google Cloud Console でプロジェクト作成（人間操作）
2. Gmail API / Calendar API / Drive API を有効化（人間操作）
3. OAuth 同意画面 + クライアントID（デスクトップアプリ）作成（人間操作）
4. credentials.json をダウンロード（人間操作）
5. **配置 → 秘書が自動代行**（Bashでコピー）
6. Claude Code 再起動（人間操作）
7. 初回 MCP 利用時にブラウザで Google ログイン（人間操作）

### Microsoft 連携（Outlook + Calendar + OneDrive + Teams）の流れ

1. Azure Portal → アプリの登録（人間操作）
2. Mail/Calendars/Files/Chat の API 権限を追加（人間操作）
3. パブリッククライアントフローを許可（人間操作）
4. クライアント ID をコピー（人間操作）
5. **環境変数設定 → 秘書が自動代行**（Bashで .env 作成）
6. Claude Code 再起動 → 初回 OAuth 認証（ブラウザでログイン）

### Slack 連携の流れ

1. Slack App を作成（人間操作）
2. Bot Token Scopes 追加 → ワークスペースインストール（人間操作）
3. Bot Token (`xoxb-...`) と Team ID をコピー（人間操作）
4. **環境変数設定 → 秘書が自動代行**（Bashで .env 作成）
5. Claude Code 再起動 → 利用開始

### 追加 MCP（任意）

「Notion使いたい」「Chatwork連携したい」と話しかけると、秘書が手順を案内します。
Notion / GitHub などが追加可能です。

MCP がなくても、`.company/` 内のファイル管理だけで完全に動作します。

## ブラウザでダッシュボード

```bash
npx cc-company-dashboard
```

部署別の TODO・Inbox・Activity・Graph をブラウザで一覧できます。

## ライセンス・クレジット

- License: MIT
- Forked from: [Shin-sibainu/cc-company](https://github.com/Shin-sibainu/cc-company)
- 元プラグインの開発者 Shin-sibainu 氏に深く感謝します

## サポート

ブートキャンプ参加者向けのサポートチャンネルから質問してください。
