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
  python3 mail_readonly.py send --to a@b.jp --subject 件名 --body-file 本文.txt
                                                 # 送らずに確認用の中身と「確認番号」を返す
  python3 mail_readonly.py send ... --confirm <確認番号>
                                                 # 受講者が中身を見て「送って」と言ったら、その番号で送る
Windows は python3 の代わりに `py -3`。出力はすべて JSON（UTF-8）。
"""
import argparse
import email
import getpass
import hashlib
import html
import imaplib
import json
import os
import re
import smtplib
import ssl
import sys
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import formatdate, getaddresses, make_msgid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _secret  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "bootcamp-company")
CONFIG_PATH = os.path.join(CONFIG_DIR, "mail.json")
KEYCHAIN_SERVICE = "bootcamp-company-mail"

# 呼んではいけない IMAP コマンド（読み取り専用を機械的に保証する）
FORBIDDEN_IMAP = {"STORE", "EXPUNGE", "COPY", "MOVE", "DELETE", "RENAME", "APPEND"}
FORBIDDEN_UID = {"STORE", "COPY", "MOVE", "EXPUNGE"}

# よくあるサーバー（ドメイン → IMAP / SMTP）。無いものは受講者の Outlook の設定画面から写す
KNOWN_SERVERS = {
    "yahoo.co.jp": ("imap.mail.yahoo.co.jp", 993, "smtp.mail.yahoo.co.jp", 465),
    "ymail.ne.jp": ("imap.mail.yahoo.co.jp", 993, "smtp.mail.yahoo.co.jp", 465),
    "ocn.ne.jp": ("imap.ocn.ne.jp", 993, "smtp.ocn.ne.jp", 465),
}

# 個人の Outlook.com は 2024-09-16 から ID・パスワードでのログインを Microsoft が止めている（OAuth のみ）
# → この道具ではつながらない。setup の最初で止めて、別の道を案内する
MICROSOFT_PERSONAL = ("outlook.com", "outlook.jp", "hotmail.com", "hotmail.co.jp", "live.com", "live.jp", "msn.com")

# 日本のメールでよく見る文字コードの呼び名 → Python が分かる名前（①や～が崩れないよう cp932 系に寄せる）
CHARSET_ALIASES = {
    "shift_jis": "cp932", "shift-jis": "cp932", "sjis": "cp932", "x-sjis": "cp932", "ms_kanji": "cp932",
    "windows-31j": "cp932", "iso-2022-jp": "iso2022_jp_ext", "iso-2022-jp-ms": "iso2022_jp_ext",
    "x-unknown": "utf-8", "unknown-8bit": "utf-8",
}


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.exit(code)


def decode_bytes(payload, charset):
    """文字コードの名前が変・不明でも落ちずに読む。"""
    names = []
    if charset:
        c = charset.strip().lower()
        names.append(CHARSET_ALIASES.get(c, c))
    names += ["utf-8", "cp932", "iso2022_jp_ext"]
    for n in names:
        try:
            return payload.decode(n)
        except (LookupError, UnicodeDecodeError):
            continue
    return payload.decode("utf-8", errors="replace")


def dec(value):
    """件名・差出人などの =?...?= を読める文字にする。"""
    if not value:
        return ""
    try:
        parts = []
        for chunk, cs in decode_header(value):
            parts.append(decode_bytes(chunk, cs) if isinstance(chunk, bytes) else chunk)
        return "".join(parts)
    except Exception:
        try:
            return str(make_header(decode_header(value)))
        except Exception:
            return value


def html_to_text(src):
    src = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", src)
    src = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", src)
    return html.unescape(re.sub(r"<[^>]+>", " ", src))


# ---------------------------------------------------------------------------
# 設定とパスワード
# ---------------------------------------------------------------------------

def load_config():
    if not os.path.exists(CONFIG_PATH):
        out({"ok": False, "error": "not_configured",
             "hint": "まだ設定されていません。受講者に別のターミナルで `setup` を実行してもらってください。"}, 2)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_password(cfg):
    env = os.environ.get("BOOTCAMP_MAIL_PASSWORD")
    if env:
        return env
    pw = _secret.load(KEYCHAIN_SERVICE, cfg["user"], cfg)
    if pw is None:
        out({"ok": False, "error": "password_not_found", "hint": "保存したパスワードが見つかりません。setup をやり直してください。"}, 2)
    return pw


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
            if cmd in FORBIDDEN_IMAP or (cmd == "UID" and args and str(args[0]).upper() in FORBIDDEN_UID):
                raise RuntimeError(f"読み取り専用のため {cmd} は実行しません")
            return guard(name, *args)

        self.conn._simple_command = guarded
        self.count = 0

    def login(self, password):
        self.conn.login(self.cfg["user"], password)

    def open_inbox(self):
        typ, data = self.conn.select("INBOX", readonly=True)  # = EXAMINE
        if typ != "OK":
            raise RuntimeError(f"受信箱を開けません: {data}")
        self.count = int(data[0] or 0)
        return self.count

    def recent_uids(self, n, unseen=False):
        """新しい順に最大 n 通の UID。大きな受信箱でも、最後の n 通の範囲だけを聞く。"""
        if self.count == 0:
            return []
        if unseen:
            typ, data = self.conn.uid("SEARCH", None, "UNSEEN")
            if typ != "OK":
                raise RuntimeError(f"未読の一覧を取れませんでした: {data}")
            uids = data[0].split() if data and data[0] else []
            return list(reversed(uids[-n:]))
        lo = max(1, self.count - n + 1)
        typ, data = self.conn.fetch(f"{lo}:{self.count}", "(UID)")
        if typ != "OK":
            raise RuntimeError(f"メールの一覧を取れませんでした: {data}")
        uids = []
        for line in data or []:
            raw = line.decode() if isinstance(line, bytes) else str(line)
            m = re.search(r"UID (\d+)", raw)
            if m:
                uids.append(m.group(1).encode())
        return list(reversed(uids))

    @staticmethod
    def _raw(data):
        raw = next((part[1] for part in (data or []) if isinstance(part, tuple)), None)
        if raw is None:
            raise RuntimeError("このメールは見つかりません（ほかのメールソフトで削除・移動された可能性があります）")
        return raw

    def headers(self, uid):
        typ, data = self.conn.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        raw = self._raw(data)
        msg = email.message_from_bytes(raw)
        return {"uid": uid.decode() if isinstance(uid, bytes) else uid,
                "from": dec(msg.get("From")), "subject": dec(msg.get("Subject")), "date": msg.get("Date", "")}

    def body(self, uid, limit=8000):
        typ, data = self.conn.uid("FETCH", uid, "(BODY.PEEK[])")
        raw = self._raw(data)
        msg = email.message_from_bytes(raw)
        texts, htmls, attachments = [], [], []

        def own_parts(part):
            """このメール自身の本文の部品だけ（添付ファイルや、添付されたメールの中までは入らない）。"""
            if part.get_filename() or part.get_content_type() == "message/rfc822" \
                    or part.get_content_disposition() == "attachment":
                attachments.append(dec(part.get_filename()) or "（添付されたメール）")
                return
            if part.get_content_type() == "multipart/alternative":
                # 同じ本文の「文字だけ版」と「HTML版」。二重にしないよう、文字だけ版を1つ選ぶ
                subs = part.get_payload()
                pick = next((x for x in subs if x.get_content_type() == "text/plain"), None) \
                    or next((x for x in subs if x.is_multipart()), None) or (subs[-1] if subs else None)
                if pick is not None:
                    yield from own_parts(pick)
                return
            if part.is_multipart():
                for sub in part.get_payload():
                    yield from own_parts(sub)
            else:
                yield part

        for part in own_parts(msg):
            payload = part.get_payload(decode=True) or b""
            if part.get_content_type() == "text/plain":
                texts.append(decode_bytes(payload, part.get_content_charset()))
            elif part.get_content_type() == "text/html":
                htmls.append(html_to_text(decode_bytes(payload, part.get_content_charset())))
        text = "\n\n".join(texts) if texts else "\n\n".join(htmls)
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
    try:
        box = ReadOnlyIMAP(cfg)
    except Exception as e:
        out({"ok": False, "error": "connect_failed", "detail": str(e),
             "hint": "サーバーにつながりません。インターネット接続か、受信サーバー名を確かめてください。"}, 1)
    try:
        box.login(get_password(cfg))
    except imaplib.IMAP4.error as e:
        out({"ok": False, "error": "login_failed", "detail": str(e),
             "hint": "IDかパスワードが違うか、メール側で『外部のソフトから読む(IMAP)』がオフの可能性があります。"}, 1)
    return cfg, box


# ---------------------------------------------------------------------------
# 送信（確認番号つき）
# ---------------------------------------------------------------------------

def parse_recipients(value):
    # 末尾や連続のカンマがあると、新しい Python は全体を読めないもの扱いにするので先に整える
    cleaned = re.sub(r"(,\s*)+$", "", re.sub(r",\s*,", ",", (value or "").strip()))
    return [addr for _, addr in getaddresses([cleaned]) if addr and "@" in addr]


def confirm_code(sender, to, cc, bcc, subject, body):
    """下見した中身と送る中身が同じであることを確かめる番号（差出人・宛先・控え・件名・本文のどれが1文字変わっても別の番号）。"""
    h = hashlib.sha256("\x1f".join([sender, ",".join(to), ",".join(cc), ",".join(bcc), subject, body]).encode("utf-8")).hexdigest()
    return h[:8]


def smtp_login(cfg, password):
    port = int(cfg.get("smtp_port", 465))
    if port == 465:
        s = smtplib.SMTP_SSL(cfg["smtp_host"], port, context=ssl.create_default_context(), timeout=30)
    else:
        s = smtplib.SMTP(cfg["smtp_host"], port, timeout=30)
        s.starttls(context=ssl.create_default_context())
    s.login(cfg["user"], password)
    return s


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
    d_port = guess[3] if guess else 465
    print("※ サーバー名は、パソコンの Outlook の『アカウント設定』に書いてあるものを写してください。")
    imap_host = input(f"受信サーバー（IMAP） [{d_imap}]: ").strip() or d_imap
    user = input(f"ユーザー名（ID） [{address}]: ").strip() or address
    smtp_host = input(f"送信サーバー（SMTP） [{d_smtp}]: ").strip() or d_smtp
    while True:
        p = input(f"送信ポート（そのまま Enter でよい） [{d_port}]: ").strip() or str(d_port)
        if p.isdigit():
            smtp_port = int(p)
            break
        print("  数字で入れてください（例: 465 か 587）")
    password = getpass.getpass("パスワード（入力しても画面には出ません。入れたら Enter）: ")
    cfg = {"address": address, "user": user, "imap_host": imap_host, "imap_port": 993,
           "smtp_host": smtp_host, "smtp_port": smtp_port}
    box = None
    try:
        box = ReadOnlyIMAP(cfg)
        box.login(password)
        count = box.open_inbox()
    except Exception as e:
        print(f"\n× 受信サーバーにつながりませんでした: {e}")
        print("  サーバー名・ID・パスワードをもう一度確かめてください。何も保存していません。")
        sys.exit(1)
    finally:
        if box:
            box.close()
    send_ok = True
    try:
        smtp_login(cfg, password).quit()
    except Exception as e:
        send_ok = False
        print(f"\n△ 受信はつながりましたが、送信サーバーには入れませんでした: {e}")
        print("  読むことはできます。送信サーバー名とポートは、あとで秘書と確かめましょう。")
    cfg["send_verified"] = send_ok
    _secret.save(KEYCHAIN_SERVICE, user, password, cfg)
    write_config(cfg)
    print(f"\n○ つながりました（受信箱 {count} 通）。秘書の画面に戻って『連携チェック』と言ってください。")


def cmd_check(args):
    cfg, box = connect()
    try:
        count = box.open_inbox()
        uids = box.recent_uids(1)
        latest = box.headers(uids[0]) if uids else None
    finally:
        box.close()
    res = {"ok": True, "address": cfg.get("address"), "inbox_count": count,
           "latest_subject": latest["subject"] if latest else None,
           "latest_date": latest["date"] if latest else None,
           "send_verified": cfg.get("send_verified", False)}
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
    if not args.uid.isdigit():
        out({"ok": False, "error": "bad_uid", "hint": "UID は list で出た数字を1つだけ渡してください。"}, 1)
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
    to, cc = parse_recipients(args.to), parse_recipients(args.cc)
    if not to:
        out({"ok": False, "error": "no_recipient", "hint": "宛先のメールアドレスが読み取れません。"}, 1)
    bcc = [] if args.no_bcc_self else [cfg["address"]]  # 控え: Outlook の受信箱にも1通届くので、送った記録が残る
    code = confirm_code(cfg["address"], to, cc, bcc, args.subject, body)
    if args.confirm != code:
        out({"ok": False, "error": "not_confirmed", "confirm_code": code,
             "hint": ("まだ送っていません。受講者に下の中身を見せ、『送って』と言われたら、"
                      f"同じ命令に --confirm {code} を付けて実行します。中身を1文字でも変えたら番号も変わります。"),
             # 送るものは全部見せる（見せていない部分を送らない）
             "preview": {"from": cfg["address"], "to": to, "cc": cc, "bcc（控え）": bcc, "subject": args.subject, "body": body,
                         "body_chars": len(body)}}, 3)
    msg = EmailMessage()
    msg["From"] = cfg["address"]
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = args.subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=cfg["address"].split("@")[-1])
    msg.set_content(body)
    recipients = to + cc + bcc
    s = smtp_login(cfg, get_password(cfg))
    try:
        refused = s.send_message(msg, to_addrs=recipients)
    finally:
        try:
            s.quit()
        except Exception:
            pass
    if refused:
        out({"ok": False, "error": "partly_refused", "refused": {k: str(v) for k, v in refused.items()},
             "hint": "一部の宛先には届いていません。宛先を確かめてください。"}, 1)
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
    ps.add_argument("--confirm")
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
