#!/usr/bin/env python3
"""
bootcamp-company: レンタルサーバー / プロバイダ / Yahoo のメールを
「サーバーに取りに行って読む」ための道具（Python 標準ライブラリだけで動く）。

絶対に守ること（この道具の存在理由）:
  - 受信箱は EXAMINE（読み取り専用）でしか開かない
  - 本文やヘッダーは BODY.PEEK で取る（既読にしない）
  - STORE / EXPUNGE / COPY / MOVE / DELETE は一切呼ばない（呼べないようにしてある）
  => 秘書が触っても、パソコンの Outlook 側のメールは消えない・既読にもならない

使い方（秘書が実行する。パスワード入力だけは受講者本人が別のターミナルで行う）:
  python3 mail_readonly.py setup                 # 受講者が自分で実行（パスワードは画面に出ない）
  python3 mail_readonly.py check                 # 連携チェック（最新1通の件名だけ）
  python3 mail_readonly.py list --n 10           # 最新10通の差出人・件名・日時
  python3 mail_readonly.py read <UID>            # 1通の本文（既読にしない）
  python3 mail_readonly.py send --to a@b.jp --subject 件名 --body-file 本文.txt --yes
                                                 # 送信（--yes が無いと送らない。控えは自分にBCC）
出力はすべて JSON（UTF-8）。
"""
import argparse
import email
import getpass
import imaplib
import json
import os
import platform
import re
import smtplib
import ssl
import subprocess
import sys
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "bootcamp-company")
CONFIG_PATH = os.path.join(CONFIG_DIR, "mail.json")
KEYCHAIN_SERVICE = "bootcamp-company-mail"

# 呼んではいけない IMAP コマンド（読み取り専用を機械的に保証する）
FORBIDDEN_IMAP = {"STORE", "EXPUNGE", "COPY", "MOVE", "DELETE", "RENAME", "APPEND", "UID STORE", "UID COPY", "UID MOVE", "UID EXPUNGE"}

# よくあるサーバー（ドメイン → IMAP / SMTP）。無いものは受講者の Outlook の設定画面から写す
KNOWN_SERVERS = {
    "yahoo.co.jp": ("imap.mail.yahoo.co.jp", 993, "smtp.mail.yahoo.co.jp", 465),
    "ymail.ne.jp": ("imap.mail.yahoo.co.jp", 993, "smtp.mail.yahoo.co.jp", 465),
    "ocn.ne.jp": ("imap.ocn.ne.jp", 993, "smtp.ocn.ne.jp", 465),
}

# 個人の Outlook.com は 2024-09-16 から ID・パスワードでのログインを Microsoft が止めている（OAuth のみ）
# → この道具ではつながらない。setup の最初で止めて、別の道を案内する
MICROSOFT_PERSONAL = ("outlook.com", "outlook.jp", "hotmail.com", "hotmail.co.jp", "live.com", "live.jp", "msn.com")


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.exit(code)


def dec(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


# ---------------------------------------------------------------------------
# 設定とパスワード
# ---------------------------------------------------------------------------

def load_config():
    if not os.path.exists(CONFIG_PATH):
        out({"ok": False, "error": "not_configured",
             "hint": "まだ設定されていません。受講者に別のターミナルで `setup` を実行してもらってください。"}, 2)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def keychain_available():
    return platform.system() == "Darwin"


def save_password(user, password, cfg):
    if keychain_available():
        subprocess.run(["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE, "-a", user],
                       capture_output=True)
        subprocess.run(["security", "add-generic-password", "-s", KEYCHAIN_SERVICE, "-a", user, "-w", password],
                       check=True, capture_output=True)
        cfg["password_store"] = "keychain"
    else:
        # Windows: ユーザー本人しか読めないホームフォルダ配下に保存（標準ライブラリだけで使える保管庫が無いため）
        cfg["password_store"] = "file"
        cfg["password"] = password


def get_password(cfg):
    env = os.environ.get("BOOTCAMP_MAIL_PASSWORD")
    if env:
        return env
    if cfg.get("password_store") == "keychain":
        r = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", cfg["user"], "-w"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.rstrip("\n")
        out({"ok": False, "error": "password_not_found", "hint": "キーチェーンにパスワードがありません。setup をやり直してください。"}, 2)
    return cfg.get("password", "")


def write_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 読み取り専用の IMAP 接続
# ---------------------------------------------------------------------------

class ReadOnlyIMAP:
    """EXAMINE と PEEK だけを使う。禁止コマンドは送る前に止める。"""

    def __init__(self, cfg):
        self.cfg = cfg
        ctx = ssl.create_default_context()
        self.conn = imaplib.IMAP4_SSL(cfg["imap_host"], int(cfg.get("imap_port", 993)), ssl_context=ctx, timeout=30)
        guard = self.conn._simple_command

        def guarded(name, *args):
            cmd = name.upper()
            if cmd in FORBIDDEN_IMAP or (cmd == "UID" and args and str(args[0]).upper() in {"STORE", "COPY", "MOVE", "EXPUNGE"}):
                raise RuntimeError(f"読み取り専用のため {cmd} は実行しません")
            return guard(name, *args)

        self.conn._simple_command = guarded

    def login(self, password):
        self.conn.login(self.cfg["user"], password)

    def open_inbox(self):
        typ, data = self.conn.select("INBOX", readonly=True)  # = EXAMINE
        if typ != "OK":
            raise RuntimeError(f"受信箱を開けません: {data}")
        return int(data[0] or 0)

    def recent_uids(self, n, unseen=False):
        typ, data = self.conn.uid("SEARCH", None, "UNSEEN" if unseen else "ALL")
        uids = data[0].split() if data and data[0] else []
        return list(reversed(uids[-n:]))

    def headers(self, uid):
        typ, data = self.conn.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        raw = next((part[1] for part in data if isinstance(part, tuple)), b"")
        msg = email.message_from_bytes(raw)
        return {"uid": uid.decode() if isinstance(uid, bytes) else uid,
                "from": dec(msg.get("From")), "subject": dec(msg.get("Subject")), "date": msg.get("Date", "")}

    def body(self, uid, limit=8000):
        typ, data = self.conn.uid("FETCH", uid, "(BODY.PEEK[])")
        raw = next((part[1] for part in data if isinstance(part, tuple)), b"")
        msg = email.message_from_bytes(raw)
        text = ""
        attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            fname = part.get_filename()
            if fname:
                attachments.append(dec(fname))
                continue
            if part.get_content_type() == "text/plain" and not text:
                payload = part.get_payload(decode=True) or b""
                text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if not text:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True) or b""
                    html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    text = re.sub(r"<[^>]+>", " ", html)
                    break
        return {"uid": uid, "from": dec(msg.get("From")), "to": dec(msg.get("To")),
                "subject": dec(msg.get("Subject")), "date": msg.get("Date", ""),
                "attachments": attachments, "body": text[:limit], "truncated": len(text) > limit}

    def close(self):
        try:
            self.conn.logout()
        except Exception:
            pass


def connect():
    cfg = load_config()
    box = ReadOnlyIMAP(cfg)
    try:
        box.login(get_password(cfg))
    except imaplib.IMAP4.error as e:
        out({"ok": False, "error": "login_failed", "detail": str(e),
             "hint": "IDかパスワードが違うか、メール側で『外部のソフトから読む(IMAP)』がオフの可能性があります。"}, 1)
    return cfg, box


# ---------------------------------------------------------------------------
# コマンド
# ---------------------------------------------------------------------------

def cmd_setup(args):
    print("メールの連携設定をします。パスワードは画面に表示されません。")
    address = input("メールアドレス: ").strip()
    domain = address.split("@")[-1].lower()
    if domain in MICROSOFT_PERSONAL:
        print("\n× 個人の Outlook.com / Hotmail は、Microsoft がパスワードでのログインを止めているため、この方法ではつながりません。")
        print("  秘書の画面に戻って『Outlook.com はつながらなかった』と伝えてください。別の方法を相談します。")
        sys.exit(1)
    guess = KNOWN_SERVERS.get(domain)
    d_imap = guess[0] if guess else f"imap.{domain}"
    d_smtp = guess[2] if guess else f"smtp.{domain}"
    print("※ サーバー名は、パソコンの Outlook の『アカウント設定』に書いてあるものを写してください。")
    imap_host = input(f"受信サーバー（IMAP） [{d_imap}]: ").strip() or d_imap
    user = input(f"ユーザー名（ID） [{address}]: ").strip() or address
    smtp_host = input(f"送信サーバー（SMTP） [{d_smtp}]: ").strip() or d_smtp
    smtp_port = input(f"送信ポート [{guess[3] if guess else 465}]: ").strip() or str(guess[3] if guess else 465)
    password = getpass.getpass("パスワード（表示されません）: ")
    cfg = {"address": address, "user": user, "imap_host": imap_host, "imap_port": 993,
           "smtp_host": smtp_host, "smtp_port": int(smtp_port)}
    box = ReadOnlyIMAP(cfg)
    try:
        box.login(password)
        count = box.open_inbox()
    except Exception as e:
        print(f"\n× つながりませんでした: {e}")
        print("  サーバー名・ID・パスワードをもう一度確かめてください。何も保存していません。")
        sys.exit(1)
    finally:
        box.close()
    save_password(user, password, cfg)
    write_config(cfg)
    print(f"\n○ つながりました（受信箱 {count} 通）。秘書の画面に戻って『連携チェック』と言ってください。")


def cmd_check(args):
    cfg, box = connect()
    try:
        count = box.open_inbox()
        latest = box.headers(box.recent_uids(1)[0]) if count else None
    finally:
        box.close()
    res = {"ok": True, "address": cfg.get("address"), "inbox_count": count,
           "latest_subject": latest["subject"] if latest else None,
           "latest_date": latest["date"] if latest else None}
    if count == 0:
        res["warning"] = "pop_delete_suspected"
        res["hint"] = ("受信箱が0通です。パソコンの Outlook が『受け取ったらサーバーから消す』設定になっている可能性があります。"
                       "Outlook で『サーバーにメッセージのコピーを置く』にチェックを入れてもらってください。")
    out(res)


def cmd_list(args):
    cfg, box = connect()
    try:
        box.open_inbox()
        items = [box.headers(u) for u in box.recent_uids(args.n, unseen=args.unseen)]
    finally:
        box.close()
    out({"ok": True, "count": len(items), "messages": items})


def cmd_read(args):
    cfg, box = connect()
    try:
        box.open_inbox()
        res = box.body(args.uid.encode(), limit=args.limit)
    finally:
        box.close()
    res["uid"] = args.uid
    out({"ok": True, "message": res})


def cmd_send(args):
    cfg = load_config()
    with open(args.body_file, encoding="utf-8") as f:
        body = f.read()
    if not args.yes:
        out({"ok": False, "error": "not_confirmed",
             "hint": "送信は受講者が本文を見て『送って』と言ってから、--yes を付けて実行します。",
             "preview": {"to": args.to, "subject": args.subject, "body": body[:2000]}}, 3)
    msg = EmailMessage()
    msg["From"] = cfg["address"]
    msg["To"] = args.to
    if args.cc:
        msg["Cc"] = args.cc
    msg["Subject"] = args.subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=cfg["address"].split("@")[-1])
    msg.set_content(body)
    recipients = [parseaddr(a)[1] for a in (args.to.split(",") + (args.cc.split(",") if args.cc else []))]
    if not args.no_bcc_self:
        recipients.append(cfg["address"])  # 控え: Outlook の受信箱にも1通届くので、送った記録が残る
    port = int(cfg.get("smtp_port", 465))
    password = get_password(cfg)
    if port == 465:
        with smtplib.SMTP_SSL(cfg["smtp_host"], port, context=ssl.create_default_context(), timeout=30) as s:
            s.login(cfg["user"], password)
            s.send_message(msg, to_addrs=recipients)
    else:
        with smtplib.SMTP(cfg["smtp_host"], port, timeout=30) as s:
            s.starttls(context=ssl.create_default_context())
            s.login(cfg["user"], password)
            s.send_message(msg, to_addrs=recipients)
    out({"ok": True, "sent_to": recipients, "subject": args.subject})


def main():
    p = argparse.ArgumentParser(description="読み取り専用のメール連携（bootcamp-company）")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    sub.add_parser("check")
    pl = sub.add_parser("list")
    pl.add_argument("--n", type=int, default=10)
    pl.add_argument("--unseen", action="store_true")
    pr = sub.add_parser("read")
    pr.add_argument("uid")
    pr.add_argument("--limit", type=int, default=8000)
    ps = sub.add_parser("send")
    ps.add_argument("--to", required=True)
    ps.add_argument("--cc")
    ps.add_argument("--subject", required=True)
    ps.add_argument("--body-file", required=True)
    ps.add_argument("--yes", action="store_true")
    ps.add_argument("--no-bcc-self", action="store_true")
    args = p.parse_args()
    try:
        {"setup": cmd_setup, "check": cmd_check, "list": cmd_list, "read": cmd_read, "send": cmd_send}[args.cmd](args)
    except SystemExit:
        raise
    except Exception as e:
        out({"ok": False, "error": type(e).__name__, "detail": str(e)}, 1)


if __name__ == "__main__":
    main()
