# 仮想組織 company（コーデックス版）の入れ方

コーデックス（OpenAI の Codex）で、秘書から始める仮想組織を使うための説明です。
Claude 版と中身は同じで、**同じ会社フォルダ（.company）をどちらで開いても続きから動きます**。
呼び方だけちがいます（Claude 版＝`/company`、コーデックス版＝`$company`）。

## はじめに（前提）

- コーデックスがパソコンに入っていて、ChatGPT のアカウントでログインできていること。
- このリポジトリは**非公開**です。入れる前に、パソコンの git が GitHub にログインできている必要があります
  （コーデックスは入れるときに途中でパスワードを聞いてきません。ログインできていないと「見つからない」「入れられない」で止まります）。
  - いちばんかんたんなのは GitHub CLI（`gh`）で `gh auth login` を一度だけ実行して、画面の案内どおりに進めることです。
  - 受講のご案内で招待された GitHub のアカウントでログインしてください。

## 入れ方

ターミナル（Mac）または PowerShell（Windows）を開いて、下の2行を順にコピーして貼り付けます。

### Mac

```bash
codex plugin marketplace add inoshinichi/bootcamp-company
codex plugin add company@bootcamp-company
```

### Windows（PowerShell）

```powershell
codex plugin marketplace add inoshinichi/bootcamp-company
codex plugin add company@bootcamp-company
```

入ったかどうかは `codex plugin list` で確かめられます。`company@bootcamp-company` の行が「installed」になっていれば入っています。

## 使い方

1. 会社フォルダ（仕事の記録を置くフォルダ）に移動して、コーデックスを起動します。

   ```bash
   cd 会社フォルダの場所
   codex
   ```

2. 入力欄に `$company` と入力して送ります。秘書が出てきて、最初の設定を案内します。

最初の設定では、秘書が次のことを順番に案内します。

- メール・予定表・チャットなどを、コーデックスの「アプリ（コネクター）」でつなぐこと
- Chrome の拡張機能（コーデックス用）を入れて、つないで、動くか確かめること

詳しくは [codex/skills/company/references/connections-codex.md](skills/company/references/connections-codex.md) を見てください。
会社のパソコンの決まりなどで入れられないものがあっても大丈夫です。秘書が理由と代わりのやり方を伝え、あとでやることとして記録しておきます。

## 更新のしかた

新しい版が出たら、下の2行を実行します（Mac・Windows とも同じ）。

```bash
codex plugin marketplace upgrade bootcamp-company
codex plugin add company@bootcamp-company
```

更新したあとは、コーデックスを一度閉じて開き直してください。

## Claude 版といっしょに使うとき

- 会社フォルダの中身（.company の中のファイルと名前）は Claude 版と同じです。
- 昨日は Claude、今日はコーデックス、のように切り替えても、秘書は記録（しおり）を読んで続きから始めます。

## うまくいかないとき

- 「見つからない」「認証」などで止まる → GitHub へのログインができていない可能性があります。`gh auth login` をもう一度実行してください。
- `$company` を入力しても秘書が出てこない → コーデックスを閉じて開き直し、`codex plugin list` で入っているか確かめてください。
- Windows で一部の道具（Mac 用の読み取りの道具など）は使えません。秘書が代わりのやり方を案内します。
