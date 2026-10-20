# 仮想組織 company（コーデックス版）の入れ方

コーデックス（OpenAI の Codex）で、秘書から始める仮想組織を使うための説明です。
Claude 版と中身は同じで、**同じ会社フォルダ（.company）をどちらで開いても続きから動きます**。
呼び方だけちがいます（Claude 版＝`/company`、コーデックス版＝`$company`）。

## はじめに（前提）

- コーデックスがパソコンに入っていて、ChatGPT のアカウントでログインできていること。
  - 確かめ方: `codex login status` と打ち、ChatGPT でログインしていると出れば大丈夫です。API キー（API key）と出たら、`codex logout` → `codex login` で ChatGPT のアカウントを選び直してください（API キーのままだと、メールなどのアプリをつなげないことがあります）。
- GitHub へのログインは要りません（下の2行だけで入れられます）。

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
- Chrome の拡張機能（OpenAI の「ChatGPT」）を入れて、つないで、動くか確かめること
  （拡張機能は **ChatGPT のデスクトップアプリ**の設定から入れます。入れたあとは、いつものコーデックスのまま使えるかを秘書がその場で確かめます。公式の案内はデスクトップアプリから使う形で、黒い画面のコーデックスから使えることは講師のパソコンで確かめ済みです。使えないときはデスクトップアプリのチャットで使います）

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

- 「見つからない」などで止まる → インターネットにつながっているか、コマンドの打ち間違いがないかを確かめて、もう一度2行を実行してください。
- `$company` を入力しても秘書が出てこない → コーデックスを閉じて開き直し、`codex plugin list` で入っているか確かめてください。
- Windows で一部の道具（Mac 用の読み取りの道具など）は使えません。秘書が代わりのやり方を案内します。
