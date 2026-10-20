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

## インストール

GitHub へのログインは要りません。下のコマンドだけで入れられます。

### 事前に決めること: 「自分の会社フォルダ」を1つ作る

秘書の記憶（`.company/`）は **Claude Code を起動したフォルダの中**に作られます。
毎回バラバラのフォルダで開くと秘書が組織を見つけられないので、**最初に置き場所を1つ決めてください**。

```bash
mkdir -p ~/my-company
cd ~/my-company
```

> 📁 Cursor を使う場合も、**「フォルダを開く」でこの `my-company` を開いてから**ターミナルで `claude` と入力します。
> （プラグインのリポジトリを開いて作業しないでください。フォルダが変わると秘書が見つかりません）

### 受講者がやること: 3コマンドだけ

**ターミナル**（Cursor の内蔵ターミナルで OK）で、以下の2行を実行します。

```bash
claude plugin marketplace add inoshinichi/bootcamp-company --scope user
claude plugin install company@bootcamp-company --scope user
```

そのあと `claude` を起動して、

```
/company
```

> 🌐 **あわせて Chrome と「Claude in Chrome」を入れておいてください**（秘書と同じ Claude のアカウントでログイン）。
> Google Chrome を入れる → Chrome ウェブストアの [Claude](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) で「Chrome に追加」→ 拡張機能にログイン。Pro・Max・Team・Enterprise のプランで使えます（Chrome 以外のブラウザ・スマホは対象外）。
> 最初の `/company` のとき、秘書が「入れる → つなぐ → 確かめる」まで案内します。入れられない事情（プラン・会社のパソコンの制限）があれば、そのまま伝えれば代わりの道を案内します。

**それ以降は秘書が全部案内します。**

### すでに前の版を入れている方（更新）

```bash
claude plugin marketplace update bootcamp-company
claude plugin update company@bootcamp-company
```

更新したら Claude Code を一度終了して起動し直し、`/company` と入力してください。

> 🔴 **`--scope user` は必ず付けてください（超重要）**
> プラグインには `user` / `project` / `local` の3つのスコープがあり、
> `project` や `local` で入れると **インストールしたフォルダでしか使えません**。
> 別のフォルダで Claude Code を開いた瞬間に `/company` が消えます。
> `--scope user` なら、どのフォルダで開いても秘書が使えます。
>
> 確認コマンド: `claude plugin list` → `company@bootcamp-company` が **`Scope: user`** になっていれば OK。

> 💡 **「company プラグイン」と表示されますが正常です**
> マーケットプレイス名が `bootcamp-company`、その中の本体プラグイン名が `company` という構造です。

### ❓ うまくいかないとき

| 症状 | 原因 | 直し方 |
|---|---|---|
| **`/company` が出てこない・消えた** | プラグインが `local` / `project` スコープで入っている（フォルダに紐づいている） | `claude plugin list` でスコープを確認 → `claude plugin install company@bootcamp-company --scope user` で入れ直す |
| **秘書が初対面のように振る舞う／今までの記録が無い** | 前回と**違うフォルダ**で Claude Code を開いている（`.company/` は起動フォルダの中にある） | 前回のフォルダで開き直す。分からなければ `/company` と言えば、秘書が親フォルダとホームを探して見つけてくれます |
| **Cursor を再起動したら上の2つが起きた** | Cursor が別のフォルダで開き直した | Cursor で「フォルダを開く」→ 自分の会社フォルダ（例 `~/my-company`）を選び直す |

### 秘書が後で案内すること（受講者は事前に何も入れなくて OK）

| 案内タイミング | 内容 |
|---|---|
| `/company` 起動直後 | 6問オンボーディング（事業・目標・**メールアドレス**・Windows/Mac・チャット・ダッシュボード）。メールの種類は秘書がアドレスから自動で調べる |
| オンボーディング完了時 | 環境に応じた連携プラン（Microsoft 365・Google は**公式の連携ボタン**／レンタルサーバー・Yahoo は**サーバーに読みに行く道具**） |
| 「アプリ作って」と言ったとき | obra/superpowers プラグインが必要なら、その場でインストールコマンドを案内 |
| 「連携チェック」と言ったとき | メール・カレンダー・フォルダ・チャットのつながり具合を ○×の表で表示 |

URL や手順を覚える必要はありません。秘書に話しかけて進めてください。

### 研修の前に配る「準備の紙」

[docs/guide/junbi.md](docs/guide/junbi.md) — アカウント作成・連携ボタン・メールのパスワード確認・Outlook の設定1か所・見せてよいフォルダ。

### 連携の考え方（2026-10 改訂）

- **公式の連携（Claude の「コネクター」）が正。** Claude の WEB・デスクトップアプリで一度ボタンを押せば、同じアカウントでログインした秘書から使える。Google Cloud や Azure の管理画面での作業は不要になった（バージョン 1.1.0）
- 公式が無いメール・カレンダー（レンタルサーバー、Yahoo、iPhone、パソコンの Outlook の予定表）は、プラグインに入っている**読むだけの道具**でつなぐ。メールを消さない・既読にしない
- 詳細は [plugins/company/skills/company/references/connections.md](plugins/company/skills/company/references/connections.md)。古い手順（Google Cloud・Azure の鍵づくり）は本線から外し、`connections-legacy.md` に**予備**として残してある（通常は使いません）

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
| 5 | Claude in Chrome（`/chrome` で接続） | 実機 UI テストで最終確認 |
| 任意 | `superpowers:requesting-code-review` | 第三者視点でコードレビュー |
| 任意 | `superpowers:dispatching-parallel-agents` | 独立タスクを並列実行 |
| バグ時 | `superpowers:systematic-debugging` | 体系的デバッグ |

ユーザーは「○○を作って」と言うだけ。秘書が上記のスキルを順に呼び出して進めます。

**注意**: superpowers プラグインを先にインストールしてください（上記のインストール手順 Step 1 参照）。

## 6問オンボーディング（あなたの環境に合わせて連携を提案）

`/company` を初回起動すると、秘書が6つの質問でお話を聞きます：

1. **事業・活動**（製造業？ コンサル？ EC？）
2. **目標・困りごと**（売上？ 業務効率？ 人手不足？）
3. **お仕事のメールアドレス** ← メールの種類（Microsoft 365／Google／レンタルサーバー等）は秘書がアドレスから自動で調べます
4. **パソコン** ← Windows / Mac
5. **社内チャット** ← Teams / Slack / Chatwork / その他 / 使わない
6. ダッシュボード（任意）

3〜5問目の回答と判定に応じて、**あなたの環境に合った連携プランを秘書が案内**します。

## 連携（メール・カレンダー・フォルダ・チャット）

| あなたの環境 | つなぎ方 |
|---|---|
| Microsoft 365（Outlook・Teams・OneDrive） | Claude の「コネクター」で **Microsoft 365** を押すだけ（最初に1回、会社の全体管理者の許可が要ります）。Teams は読むだけ |
| Google（Gmail・カレンダー・ドライブ） | Claude の「コネクター」で各サービスを押すだけ |
| レンタルサーバー・プロバイダ・Yahoo のメール | プラグイン内蔵の**読むだけの道具**で、秘書がサーバーに読みに行きます（メールを消さない・既読にしない） |
| iPhone のカレンダー／パソコンの Outlook の予定表／Mac のカレンダー | プラグイン内蔵の読むだけの道具でつなぎます |
| フォルダ | パソコンに見えているフォルダ（OneDrive・Google ドライブ・Dropbox・社内の共有フォルダ）をそのまま秘書に見せます |
| Slack／Chatwork | Slack は公式の連携、Chatwork は API トークン |
| LINE WORKS／Google Chat | 今は直接つなげません（返信の文案づくりで使えます） |

「**連携チェック**」と話しかけると、つながり具合を ○×の表で確認できます。
詳しい手順は [plugins/company/skills/company/references/connections.md](plugins/company/skills/company/references/connections.md)。

### ブラウザ操作は Claude in Chrome（拡張機能）

ブラウザを触る作業は **Claude in Chrome（Chrome 拡張）** で行います。Playwright MCP は入れていません。

最初のセットアップの手順の1つです：**入れる → つなぐ → 確かめる → 「連携の状態」に記録**。

1. Google Chrome で Chrome ウェブストアの [Claude](https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn) を開き「Chrome に追加」
2. 拡張機能に、秘書と同じ Claude のアカウントでログイン
3. Claude Code で **`/chrome`** と入力し、つながりを確かめる

**あなたが普段使っている Chrome を、ログイン済みのまま**秘書が操作できます。自社の管理画面・SNS・仕入先サイトなど「ログインしていないと始まらない」作業がそのまま頼めます。
入れられないとき（プランが対象外・会社のパソコンの制限・Chrome が無い）は、理由と代わりの道を秘書が伝え、`secretary/_resume.md` の「残り」に書きます。

## コーデックスで使う場合

OpenAI の Codex CLI でも、**同じ秘書・同じ会社フォルダ**が使えます（呼び方は `$company`）。入れ方は [codex/README.md](codex/README.md) を見てください。

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
