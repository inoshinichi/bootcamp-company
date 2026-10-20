# 前の版からの更新

すでに前の版（1.0.x・1.1.x）を入れている方の更新の手順です。

## 更新の2行

ターミナル（Windows は PowerShell）で次の2行を打ちます。

```bash
claude plugin marketplace update bootcamp-company
claude plugin update company@bootcamp-company
```

更新したら Claude Code を一度終了して起動し直し、会社フォルダで `/company` と打ってください。

## 今までの組織はそのまま使えます

前の版で作った `.company/` は消えません。前の版で作った組織に足りないものがあると、秘書が次を行います（今あるファイルは上書きしません）。

1. `secretary/work-log.md`（作業の記録）・`.company/flow-map.md`（連携表）・各部署の `manuals/INDEX.md`（手順書の一覧）を見出しだけで作る
2. `.company/CLAUDE.md` などの末尾に「組織の絶対ルール」の節を書き足す
3. 一度だけ「今日から、繰り返しの仕事を手順書にして部署に置いていきます」と伝える

## Google・Microsoft を古い手順でつないでいた方

バージョン 1.1.0 から、Google・Microsoft 365 は Claude の公式の連携ボタン（コネクター）でつなぎます。古い手順（Google Cloud・Azure）でつないでいた方には、秘書が一度だけ、ボタンを押し直す案内をします。
