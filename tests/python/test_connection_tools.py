"""
連携の道具（scripts/*.py）のテスト。標準ライブラリだけで動く:
  python3 -m unittest discover -s tests/python -v

いちばん大事な確認: メールの道具が「消さない・既読にしない」こと。
"""
import imaplib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "company" / "skills" / "company" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mail = load("mail_readonly")
cal = load("caldav_readonly")

RAW = (
    b"From: =?UTF-8?B?5bGx55Sw5aSq6YOO?= <yamada@example.jp>\r\n"
    b"Subject: =?ISO-2022-JP?B?GyRCOCtAUSRON28bKEI=?=\r\n"
    b"Date: Wed, 01 Oct 2026 09:00:00 +0900\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
    + "本文です".encode("utf-8")
)


class FakeIMAP:
    """imaplib.IMAP4_SSL の代わり。送られたコマンドを全部記録する。"""

    def __init__(self, *a, **kw):
        self.sent = []
        self.messages = {b"1": RAW, b"2": RAW}

    def _simple_command(self, name, *args):
        self.sent.append((name,) + args)
        return "OK", [b""]

    def login(self, user, pw):
        self.sent.append(("LOGIN", user))
        return "OK", [b""]

    def select(self, mailbox="INBOX", readonly=False):
        self.sent.append(("EXAMINE" if readonly else "SELECT", mailbox))
        return "OK", [str(len(self.messages)).encode()]

    def uid(self, command, *args):
        self._simple_command("UID", command, *args)
        if command == "SEARCH":
            return "OK", [b" ".join(self.messages)]
        if command == "FETCH":
            return "OK", [(b"1 (UID 1 BODY[] {10}", self.messages[args[0]]), b")"]
        return "OK", [b""]

    def logout(self):
        pass


class MailReadOnlyTest(unittest.TestCase):
    def setUp(self):
        self.patch = mock.patch.object(imaplib, "IMAP4_SSL", FakeIMAP)
        self.patch.start()
        self.box = mail.ReadOnlyIMAP({"imap_host": "imap.example.jp", "user": "u@example.jp"})

    def tearDown(self):
        self.patch.stop()

    def test_inbox_is_opened_read_only(self):
        self.box.open_inbox()
        self.assertIn(("EXAMINE", "INBOX"), self.box.conn.sent)
        self.assertNotIn(("SELECT", "INBOX"), self.box.conn.sent)

    def test_fetch_uses_peek(self):
        self.box.open_inbox()
        self.box.headers(b"1")
        self.box.body(b"1")
        fetches = [s for s in self.box.conn.sent if s[0] == "UID" and s[1] == "FETCH"]
        self.assertEqual(len(fetches), 2)
        for f in fetches:
            self.assertIn("BODY.PEEK", f[3])

    def test_destructive_commands_are_blocked(self):
        for cmd in ["STORE", "EXPUNGE", "COPY", "MOVE", "DELETE", "APPEND"]:
            with self.assertRaises(RuntimeError, msg=cmd):
                self.box.conn._simple_command(cmd, "1")
        for cmd in ["STORE", "COPY", "MOVE", "EXPUNGE"]:
            with self.assertRaises(RuntimeError, msg=f"UID {cmd}"):
                self.box.conn.uid(cmd, b"1", "+FLAGS", "(\\Deleted)")

    def test_japanese_headers_are_decoded(self):
        h = self.box.headers(b"1")
        self.assertEqual(h["subject"], "見積の件")
        self.assertIn("山田太郎", h["from"])
        b = self.box.body(b"1")
        self.assertEqual(b["body"], "本文です")

    def test_source_never_calls_destructive_imap_methods(self):
        src = (SCRIPTS / "mail_readonly.py").read_text(encoding="utf-8")
        import re
        hits = re.findall(r"conn\.(store|expunge|copy|move|delete|append)\(", src)
        self.assertEqual(hits, [], "IMAP を書き換える呼び出しが見つかった")


class MailSendNeedsConfirmationTest(unittest.TestCase):
    def test_send_without_yes_does_not_send(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = os.path.join(d, "mail.json")
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump({"address": "u@example.jp", "user": "u", "smtp_host": "smtp.example.jp",
                           "smtp_port": 465, "password": "x"}, f)
            body = os.path.join(d, "body.txt")
            Path(body).write_text("こんにちは", encoding="utf-8")
            argv = ["mail_readonly.py", "send", "--to", "a@example.jp", "--subject", "件名", "--body-file", body]
            with mock.patch.object(mail, "CONFIG_PATH", cfg_path), mock.patch.object(sys, "argv", argv), \
                    mock.patch("smtplib.SMTP_SSL") as smtp, redirect_stdout(io.StringIO()) as buf:
                with self.assertRaises(SystemExit) as cm:
                    mail.main()
            self.assertEqual(cm.exception.code, 3)
            smtp.assert_not_called()
            self.assertEqual(json.loads(buf.getvalue())["error"], "not_confirmed")


ICS = """BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:定例会議
DTSTART:20261001T010000Z
DTEND:20261001T020000Z
LOCATION:本社
END:VEVENT
BEGIN:VEVENT
SUMMARY:お休み
DTSTART;VALUE=DATE:20261002
DTEND;VALUE=DATE:20261003
END:VEVENT
BEGIN:VEVENT
SUMMARY:ずっと先
DTSTART:20261201T010000Z
DTEND:20261201T020000Z
END:VEVENT
BEGIN:VEVENT
SUMMARY:長い件名が
 折り返されている
DTSTART;TZID=Asia/Tokyo:20261001T150000
DTEND;TZID=Asia/Tokyo:20261001T160000
END:VEVENT
END:VCALENDAR
"""


class CalendarParseTest(unittest.TestCase):
    def test_parse_range_timezone_allday_and_folding(self):
        start = datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc)  # = 10/1 0:00 JST
        end = start + timedelta(days=2)
        evs = cal.parse_ics(ICS, start, end)
        titles = [e["title"] for e in evs]
        self.assertEqual(titles, ["定例会議", "お休み", "長い件名が折り返されている"])
        self.assertEqual(evs[0]["start"], "2026-10-01 10:00")  # UTC 1:00 → 日本時間 10:00
        self.assertTrue(evs[1]["all_day"])
        self.assertEqual(evs[2]["start"], "2026-10-01 15:00")

    def test_only_read_methods_are_allowed(self):
        dav = cal.ReadOnlyCalDAV("https://caldav.example.jp/", "u", "p")
        for m in ["PUT", "DELETE", "POST", "MOVE", "PROPPATCH"]:
            with self.assertRaises(RuntimeError):
                dav.request(m, "https://caldav.example.jp/x", "")


RECUR = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:weekly
SUMMARY:朝礼
DTSTART:20260105T000000Z
DTEND:20260105T001500Z
RRULE:FREQ=WEEKLY;BYDAY=MO,TH
EXDATE:20261005T000000Z
END:VEVENT
BEGIN:VEVENT
UID:weekly
RECURRENCE-ID:20261008T000000Z
SUMMARY:朝礼（時間変更）
DTSTART:20261008T010000Z
DTEND:20261008T011500Z
END:VEVENT
BEGIN:VEVENT
UID:monthly
SUMMARY:役員会
DTSTART;TZID=Asia/Tokyo:20260113T140000
DTEND;TZID=Asia/Tokyo:20260113T160000
RRULE:FREQ=MONTHLY;BYDAY=2TU
END:VEVENT
BEGIN:VEVENT
UID:counted
SUMMARY:研修（3回）
DTSTART;TZID=Asia/Tokyo:20260928T100000
DTEND;TZID=Asia/Tokyo:20260928T120000
RRULE:FREQ=DAILY;INTERVAL=2;COUNT=3
END:VEVENT
BEGIN:VEVENT
UID:bday
SUMMARY:創業記念日
DTSTART;VALUE=DATE:20151009
DTEND;VALUE=DATE:20151010
RRULE:FREQ=YEARLY
END:VEVENT
END:VCALENDAR
"""


class CalendarRecurrenceTest(unittest.TestCase):
    def test_expands_weekly_monthly_daily_yearly_with_exdate_and_override(self):
        start = datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc)  # 10/1 0:00 JST
        end = start + timedelta(days=14)                            # 〜10/14
        evs = cal.parse_ics(RECUR, start, end)
        got = sorted((e["start"], e["title"]) for e in evs)
        self.assertEqual(got, [
            ("2026-10-01 09:00", "朝礼"),            # 木曜
            ("2026-10-02 10:00", "研修（3回）"),      # 9/28, 9/30, 10/2 の3回目
            ("2026-10-08 10:00", "朝礼（時間変更）"),  # 個別に変えた回だけが出る
            ("2026-10-09", "創業記念日"),
            ("2026-10-12 09:00", "朝礼"),            # 10/5 は EXDATE で休み
            ("2026-10-13 14:00", "役員会"),          # 第2火曜
        ])


if __name__ == "__main__":
    unittest.main()
