# クイックスタート

入れ方の正本は [README の「受講者の方へ：入れ方」](https://github.com/inoshinichi/bootcamp-company#受講者の方へ入れ方) です。ここでは要点だけをまとめます。

## インストール

まず「自分の会社フォルダ」を1つ決めて、そこで作業します（秘書の記憶 `.company/` はこのフォルダの中に作られます）。
デスクトップ・書類（ドキュメント）・OneDrive・Dropbox・Google ドライブの中には作らないでください。

Mac（ターミナル）:

```bash
mkdir -p ~/my-company
cd ~/my-company
```

Windows（PowerShell。行の頭が `PS C:\` の画面）:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\my-company" | Out-Null
Set-Location "$HOME\my-company"
```

次に、プラグインを入れます。Claude Code の中で打つ場合:

```
/plugin marketplace add inoshinichi/bootcamp-company
/plugin install company@bootcamp-company
```

ターミナル・PowerShell で打つ場合（Mac も Windows も同じ）:

```bash
claude plugin marketplace add inoshinichi/bootcamp-company --scope user
claude plugin install company@bootcamp-company --scope user
```

`--scope user` は、どのフォルダで開いても `/company` が使えるように念のため付けています。
確認: `claude plugin list` で `company@bootcamp-company` の Scope が `user` になっていれば OK。
入れたら Claude Code を一度終了して、起動し直します。

## セットアップ（3ステップ）

### 1. `/company` を実行

```
> /company
```

### 2. 秘書の5つの質問に答える

1. 事業・活動
2. 目標・困りごと
3. お仕事のメールアドレス（メールの種類は秘書がアドレスから調べます）
4. パソコン（Windows / Mac）
5. 社内チャット（Teams / Slack / Chatwork / その他 / 使わない）

```
秘書: はじめまして！あなたの秘書になります。
      まず、事業や活動を教えてください。
あなた: フリーランスのWeb開発やってます

秘書: 今の目標や困りごとは？
あなた: SaaSを作って月10万目指してる。タスクが散らかるのが悩み

（このあと、メールアドレス・パソコン・社内チャットを聞かれます）
```

### 3. 完了！

```
→ .company/secretary/ が自動生成される

秘書: 秘書室のセットアップが完了しました！
      続けて、ブラウザの拡張機能と、メール・カレンダーのつなぎ方を案内しますね。
```

主に次のフォルダが作られます：

```
.company/
├── CLAUDE.md              ← 組織ルール
├── flow-map.md            ← 連携表（部署どうしの受け渡し）
└── secretary/
    ├── CLAUDE.md           ← 秘書の振る舞い
    ├── inbox/              ← クイックキャプチャ
    ├── todos/              ← 日次タスク管理
    ├── notes/              ← 壁打ち・相談メモ
    ├── experience/         ← ケースの記録
    ├── manuals/            ← 手順書
    └── work-log.md         ← 作業の記録
```

## 毎回の始め方

会社フォルダに移ってから `claude` を起動し、`/company` と打ちます（Mac: `cd ~/my-company`／Windows: `Set-Location "$HOME\my-company"`）。

## 次のステップ

- [秘書との日常](/guide/daily-usage) — 実際にどう使うか
- [部署を追加する](/guide/adding-departments) — 組織を育てる
