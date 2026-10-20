# bootcamp-company

ブートキャンプ受講者向けの「AIの秘書」プラグイン（Claude Code 用）。
[Shin-sibainu/cc-company](https://github.com/Shin-sibainu/cc-company)（MIT License）を元に、AI を使い始めたばかりの経営者でも 5分で「自分専用のAI組織」が立ち上がるよう調整したものです（元のプラグインとは別物です。入れるのはこのページのものです）。

## 受講者の方へ：入れ方

上から順に進めてください。GitHub へのログインは要りません。

### 1. 画面を開く

- **Mac**: 「ターミナル」を開きます（Command + スペース →「ターミナル」と入力 → Enter）
- **Windows**: 「PowerShell」を開きます（スタートボタン →「PowerShell」と入力 →「Windows PowerShell」を開く）。行の頭が `PS C:\` で始まっていれば正しい画面です（「コマンドプロンプト」ではありません）

### 2. Claude Code 本体を入れる（まだ入っていない方だけ）

公式の入れ方です（公式の日本語ページ: https://code.claude.com/docs/ja/setup ）。管理者の権限は要りません。

Mac:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Windows（PowerShell）:

```powershell
irm https://claude.ai/install.ps1 | iex
```

入れたら、画面をいったん閉じて**新しく開き直し**、`claude --version` と打って番号が出れば成功です。
はじめて `claude` と打つとログインの画面が出ます。**Claude のアカウント（Pro・Max・Team・Enterprise のプラン）**を選んでください（API・Console は選びません。無料プランでは Claude Code は使えません）。

- 動く環境: macOS 13 以降／Windows 10（1809 以降）・Windows 11
- Windows で要るもの: Claude Code 本体は上の PowerShell だけで入ります
- **このプラグインを入れる（手順4）には「Git」が要ります**（Claude Code 本体には不要ですが、プラグインを GitHub から取ってくるときに使います）
  - Windows: PowerShell で `winget install --id Git.Git -e --source winget` と打ち、入ったら PowerShell を閉じて開き直します
  - Mac: ターミナルで `xcode-select --install` と打ち、画面の案内に従います（10〜30分。すでに入っていれば「already installed」と出ます）
  - `git --version` と打って番号が出れば準備できています。会社のパソコンで入れられないときは、下の「うまくいかないとき」の「Git が入れられない」の行を見てください
- 会社のパソコンで入れられないときは、情報システムの担当の方に相談してください（公式のトラブル対応: https://code.claude.com/docs/en/troubleshoot-install ）

### 3. 会社フォルダを作る（最初の1回だけ）

秘書の記憶（`.company/`）は **Claude Code を起動したフォルダの中**に作られます。置き場所を1つ決めて、毎回そこで起動します。

Mac:

```bash
mkdir -p ~/my-company
cd ~/my-company
```

Windows（PowerShell）:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\my-company" | Out-Null
Set-Location "$HOME\my-company"
```

> 📁 デスクトップ・書類（ドキュメント）・OneDrive・Dropbox・Google ドライブの中には作らないでください（同期でファイルが戻ったり壊れたりします）。上の書き方なら大丈夫です。

### 4. プラグインを入れる

**書き方A（Claude Code の中で打つ）**: 会社フォルダで `claude` と打って起動し、次の2つを1つずつ打ちます。

```
/plugin marketplace add inoshinichi/bootcamp-company
/plugin install company@bootcamp-company
```

**書き方B（ターミナル・PowerShell で打つ）**: Claude Code を起動する前に、次の2行を打ちます。Mac も Windows も同じです。

```bash
claude plugin marketplace add inoshinichi/bootcamp-company --scope user
claude plugin install company@bootcamp-company --scope user
```

どちらか一方で大丈夫です。入れたら Claude Code を一度終了して（`/exit`）、もう一度 `claude` で起動します。

> 💡 「company プラグイン」と表示されますが正常です（置き場の名前が `bootcamp-company`、中のプラグインの名前が `company`）。

### 5. 最初の一言

Claude Code の中で、次のように打ちます。

```
/company
```

秘書が5つの質問をして、秘書室を作ります。そのあとの連携（メール・カレンダーなど）も秘書が案内します。

### 毎回の始め方

Mac:

```bash
cd ~/my-company
claude
```

Windows（PowerShell）:

```powershell
Set-Location "$HOME\my-company"
claude
```

起動したら `/company` と打ちます。別のフォルダで起動すると、秘書が今までの記録を見つけられません。

### 前の版を入れている方（更新）

ターミナル・PowerShell で次の2行を打ち、Claude Code を一度終了して起動し直してから `/company` と打ちます。

```bash
claude plugin marketplace update bootcamp-company
claude plugin update company@bootcamp-company
```

`/company` と打ったあと、「連携チェック」と話しかけてください（新しく増えたブラウザの拡張機能の案内が出ます）。

### AI に入れてもらう方法

Claude Code を起動して、次の文をそのまま貼り付けて送ってください。Claude Code がこのページを読んで、上の命令を打ちます（命令を打つ前に確認が出たら、内容を見て許可してください）。

```
https://github.com/inoshinichi/bootcamp-company のプラグインを入れてください。
先に、このパソコンが Windows か Mac かを確かめ、Windows なら PowerShell、Mac ならターミナルの書き方で打ってください。
git --version で Git が入っているかを確かめ、無ければ README の「2. Claude Code 本体を入れる」の Git の入れ方を私に案内してください。
このページの README の「受講者の方へ：入れ方」の「4. プラグインを入れる」の書き方B
（claude plugin marketplace add inoshinichi/bootcamp-company --scope user と
claude plugin install company@bootcamp-company --scope user）を打ち、
入ったら claude plugin list で company@bootcamp-company が入っていることを確かめてください。
終わったら、README の「3. 会社フォルダを作る」の会社フォルダ（Mac は ~/my-company、Windows は $HOME\my-company）を作り、
Claude Code を一度終了して、そのフォルダで起動し直してから /company と打つように私に伝えてください（毎回そのフォルダで起動することも伝えてください）。
```

### うまくいかないとき

| 困っていること | よくある原因 | 直し方 |
|---|---|---|
| `claude` が見つからない・認識されない | 入れたあと画面を開き直していない | ターミナル・PowerShell を閉じて開き直し、`claude --version` を打つ |
| ログインで「API」や「Console」を選んでしまった | ログインの選び間違い | Claude Code の中で `/logout` → `/login` で、Claude のアカウント（Pro などのプラン）を選び直す |
| Windows で赤い文字が出て命令が通らない | 「コマンドプロンプト」で打っている | スタートから「PowerShell」を開き直す（行の頭が `PS C:\`） |
| `Executable not found in $PATH: "git"`・`Fetching the marketplace from GitHub failed` と出る | Git が入っていない | 手順2の「Git」を入れ、画面を開き直してから手順4をやり直す |
| 会社のパソコンで Git が入れられない | ソフトの導入が止められている | GitHub のこのページの「Code」→「Download ZIP」で取って解凍し、`claude plugin marketplace add "<解凍したフォルダ>" --scope user` → `claude plugin install company@bootcamp-company --scope user` と打つ（新しい版が出たら ZIP を取り直して同じことをします） |
| `/company` が出てこない・消えた | プラグインがフォルダ限定で入っている | `claude plugin list` で `company@bootcamp-company` の「Scope」を見る → `user` でなければ書き方B で入れ直す |
| 秘書が初対面のように振る舞う／今までの記録が無い | 前回と違うフォルダで起動している | 「毎回の始め方」のとおり会社フォルダで起動し直す。分からなければ `/company` と言えば、秘書が親フォルダとホームを探します |
| Cursor を再起動したら上の2つが起きた | Cursor が別のフォルダで開き直した | Cursor で「フォルダを開く」→ 会社フォルダ（`my-company`）を選び直す。Cursor は使わなくても大丈夫です（ターミナルだけで使えます） |

### 研修の前に配る「準備の紙」

[docs/guide/junbi.md](docs/guide/junbi.md) — アカウント作成・連携ボタン・メールのパスワード確認・Outlook の設定1か所・見せてよいフォルダ・ブラウザの拡張機能・Mac の準備。

### ブラウザの拡張機能（Claude in Chrome）

秘書がブラウザを操作するには、Google Chrome に拡張機能「Claude」を入れ、秘書と同じ Claude のアカウントでログインします（Chrome ウェブストアの [Claude](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) で「Chrome に追加」）。
Google Chrome がおすすめです。Chrome が入れられない会社のパソコンでは Microsoft Edge でも使えると Claude Code の公式文書にあります（Edge で動くかは未確認）。スマホは対象外です。Pro・Max・Team・Enterprise のプランで使えます。
事前に入れておくと当日が早く進みます。入れていなくても、最初の `/company` のときに秘書が「入れる → つなぐ → 確かめる」まで案内します。

### 秘書があとで案内すること

| 案内のタイミング | 内容 |
|---|---|
| `/company` 起動直後 | 5問の質問（事業・目標・**メールアドレス**・Windows/Mac・チャット）。メールの種類は秘書がアドレスから自動で調べる |
| 質問が終わったとき | ブラウザの拡張機能の案内と、環境に合った連携プラン（Microsoft 365・Google は**公式の連携ボタン**／レンタルサーバー・Yahoo は**サーバーに読みに行く道具**） |
| 「アプリ作って」と言ったとき | obra/superpowers プラグインが必要なら、その場でインストールコマンドを案内 |
| 「連携チェック」と言ったとき | メール・カレンダー・フォルダ・チャットのつながり具合を ○×の表で表示 |

URL や手順を覚える必要はありません。秘書に話しかけて進めてください。

---

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


## 5分で立ち上がる初回セットアップ

```
> /company

秘書: はじめまして！あなたの秘書になります。
      まず、あなたの事業や活動を教えてください。

あなた: 製造業で、地元のホテル向けのアメニティを作っています

秘書: 今の目標や、日々困っていることがあれば教えてください。

あなた: 売上を伸ばしたいけど、営業が手薄。あと請求書まわりが煩雑

秘書: お仕事で使っているメールアドレスを教えてください。
      メールの種類（Microsoft 365・Google など）はこちらで調べます。

あなた: taro@example.co.jp です

秘書: 調べたところ、Microsoft 365 のメールでした。
      お使いのパソコンは Windows ですか？ Mac ですか？

あなた: Windows です

秘書: 社内チャットは何を使っていますか？

あなた: Teams です

秘書: 秘書室のセットアップが完了しました！
      続けて、ブラウザの拡張機能と、Microsoft 365（Outlook・Teams・OneDrive）の
      つなぎ方を順番に案内しますね...
```

これで `.company/` フォルダが作られ、**あなただけの秘書** が立ち上がります。

## 中核機能

### 7ステップ判断フロー
秘書は依頼を受けたとき、過去経験の検索 → 意図理解 → インプット洗い出し → 自律 / 協議の判断 → （協議のときは）提案して承認をもらう → 実行 → ケース記録 の7つの流れで処理します。
都度の判断が積み上がり、組織が成長します。

### inbox/ システム
部署同士の通知や横断案件のステータス共有を `inbox/` で集約。秘書が定期的にサマリーします。

### 経験ファイル蓄積（自律成長の核）
ケース完了時に `secretary/experience/case-NNN-...md` を残します。同種ケースが3件以上溜まると、`patterns/<種別>.md` に統合知見が生成され、次回からの判断基準になります。

### 🔴 組織が本当に連携して動くための絶対ルール（2026-10）

部署を作っただけでは、組織は動きません。動くのは「書いてある手順」と「書いてある受け渡し」だけです。だから秘書は次を必ず守ります。

1. **同じ作業が2回目に来たら、必ず手順書にしようと提案する**（作業はすべて `secretary/work-log.md` に記録）
2. **手順書は必ずどこかの部署に置く。** 合う部署が無ければ「営業部を作って、この手順書をそこに置きます」と部署づくりとセットで提案。空っぽの部署は作らない
3. **手順書には「どの部署から受け取り、どの部署へ渡すか」を書き、連携表（`.company/flow-map.md`）に1行足す。** 秘書は連携表のとおりに部署をつなぐ

報告は「営業部が見積書を作り、経理部が請求書の下書きを用意しました」のように動いた部署の名前で。
「**組織の健康診断**」と話しかけると、動いていない部署・途切れた連携・手順書になっていない繰り返しを見つけて直し方を提案します（アフターフォローにも使えます）。
詳細: [plugins/company/skills/company/references/organization.md](plugins/company/skills/company/references/organization.md)

### 部署とエージェントの自然な追加
- 同じ作業が2回目 → 手順書にして部署に置く（合う部署が無ければ部署づくりとセットで提案）
- 同じ手順書が3回以上使われ、判断が多い → その部署の専門エージェント作成を提案

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
| 5（任意） | `superpowers:requesting-code-review` | 第三者視点でコードレビュー |
| 6 | Claude in Chrome（`/chrome` で接続） | 実機 UI テストで最終確認 |
| 任意 | `superpowers:dispatching-parallel-agents` | 独立タスクを並列実行 |
| バグ時 | `superpowers:systematic-debugging` | 体系的デバッグ |

ユーザーは「○○を作って」と言うだけ。秘書が上記のスキルを順に呼び出して進めます。

**注意**: superpowers プラグインが必要です。入っていなければ、そのときに秘書が入れ方を案内します。

## 5問の質問（あなたの環境に合わせて連携を提案）

`/company` を初回起動すると、秘書が5つの質問でお話を聞きます：

1. **事業・活動**（製造業？ コンサル？ EC？）
2. **目標・困りごと**（売上？ 業務効率？ 人手不足？）
3. **お仕事のメールアドレス** ← メールの種類（Microsoft 365／Google／レンタルサーバー等）は秘書がアドレスから自動で調べます
4. **パソコン** ← Windows / Mac
5. **社内チャット** ← Teams / Slack / Chatwork / その他 / 使わない

3〜5問目の回答と判定に応じて、**あなたの環境に合った連携プランを秘書が案内**します。

## 連携（メール・カレンダー・フォルダ・チャット）

| あなたの環境 | つなぎ方 |
|---|---|
| Microsoft 365（Outlook・Teams・OneDrive） | Claude の「コネクター」で **Microsoft 365** を押すだけ（最初に1回、会社の全体管理者の許可が要ります）。Teams は読むのが基本（会社の管理者が書き込みを有効にした場合だけ送れ、送る前に必ず確認が出ます） |
| Google（Gmail・カレンダー・ドライブ） | Claude の「コネクター」で各サービスを押すだけ |
| レンタルサーバー・プロバイダ・Yahoo のメール | プラグイン内蔵の**読むだけの道具**で、秘書がサーバーに読みに行きます（メールを消さない・既読にしない） |
| iPhone のカレンダー／パソコンの Outlook の予定表／Mac のカレンダー | プラグイン内蔵の読むだけの道具でつなぎます |
| フォルダ | パソコンに見えているフォルダ（OneDrive・Google ドライブ・Dropbox・社内の共有フォルダ）をそのまま秘書に見せます |
| Slack／Chatwork | Slack は公式の連携（Claude の Team / Enterprise プランで、Slack の管理者が承認しているときだけ・公式に書かれているのは検索まで。それ以外の方は届いた文を貼っていただきます）、Chatwork は API トークン |
| LINE WORKS／Google Chat | 今は直接つなげません（返信の文案づくりで使えます） |

### 連携の考え方（2026-10 改訂）

- **公式の連携（Claude の「コネクター」）が正。** Claude の WEB・デスクトップアプリで一度ボタンを押せば、同じアカウントでログインした秘書から使える。Google Cloud や Azure の管理画面での作業は不要になった（バージョン 1.1.0）
- 公式が無いメール・カレンダー（レンタルサーバー、Yahoo、iPhone、パソコンの Outlook の予定表）は、プラグインに入っている**読むだけの道具**でつなぐ。メールを消さない・既読にしない
- 詳細は [plugins/company/skills/company/references/connections.md](plugins/company/skills/company/references/connections.md)。古い手順（Google Cloud・Azure の鍵づくり）は本線から外し、`connections-legacy.md` に**予備**として残してある（通常は使いません）

「**連携チェック**」と話しかけると、つながり具合を ○×の表で確認できます。
詳しい手順は [plugins/company/skills/company/references/connections.md](plugins/company/skills/company/references/connections.md)。

### ブラウザ操作は Claude in Chrome（拡張機能）

ブラウザを触る作業は **Claude in Chrome（Chrome 拡張）** で行います。Playwright MCP は入れていません。

最初のセットアップの手順の1つです：**入れる → つなぐ → 確かめる → 「連携の状態」に記録**。

1. Google Chrome（入れられない会社のパソコンでは Microsoft Edge。Edge で動くかは未確認です。うまくいかないときは秘書に伝えてください）で Chrome ウェブストアの [Claude](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) を開き「Chrome に追加」
2. 拡張機能に、秘書と同じ Claude のアカウントでログイン
3. Claude Code で **`/chrome`** と入力し、つながりを確かめる

**あなたが普段使っている Chrome を、ログイン済みのまま**秘書が操作できます。自社の管理画面・SNS・仕入先サイトなど「ログインしていないと始まらない」作業がそのまま頼めます。
入れられないとき（プランが対象外・会社のパソコンの制限・ブラウザが無い）は、理由と代わりの道を秘書が伝え、`secretary/_resume.md` の「残り」に書きます。

## コーデックスで使う場合

OpenAI の Codex CLI でも、**同じ秘書・同じ会社フォルダ**が使えます（呼び方は `$company`）。入れ方は [codex/README.md](codex/README.md) を見てください。


## ライセンス・クレジット

- License: MIT
- Forked from: [Shin-sibainu/cc-company](https://github.com/Shin-sibainu/cc-company)
- 元プラグインの開発者 Shin-sibainu 氏に深く感謝します

## サポート

ブートキャンプ参加者向けのサポートチャンネルから質問してください。
