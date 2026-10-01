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

    def fetch(self, seq, what):
        self._simple_command("FETCH", seq, what)
        lo, hi = (int(x) for x in seq.split(":"))
        return "OK", [f"{i} (UID {i})".encode() for i in range(lo, hi + 1)]

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
        self.box.open_inbox()

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
    def test_send_without_confirm_does_not_send(self):
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
            res = json.loads(buf.getvalue())
            self.assertEqual(res["error"], "not_confirmed")
            self.assertEqual(len(res["confirm_code"]), 8)


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


class ReviewRegressionTest(unittest.TestCase):
    """2026-10-01 の敵対レビューで再現した不具合が戻っていないこと。"""

    R = (datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc), datetime(2026, 10, 14, 15, 0, tzinfo=timezone.utc))

    def ev(self, body):
        return cal.parse_ics("BEGIN:VCALENDAR\nBEGIN:VEVENT\n" + body + "\nEND:VEVENT\nEND:VCALENDAR\n", *self.R)

    def test_value_date_time_is_not_all_day(self):
        evs = self.ev("SUMMARY:打合せ\nDTSTART;VALUE=DATE-TIME:20261002T010000Z\nDTEND;VALUE=DATE-TIME:20261002T020000Z")
        self.assertEqual([(e["start"], e["all_day"]) for e in evs], [("2026-10-02 10:00", False)])

    def test_valarm_does_not_overwrite_uid_or_title(self):
        ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:A\nSUMMARY:朝礼\nDTSTART:20261001T000000Z\nDTEND:20261001T001500Z\n"
               "RRULE:FREQ=DAILY;COUNT=3\nBEGIN:VALARM\nUID:alarm-1\nSUMMARY:通知\nACTION:DISPLAY\nEND:VALARM\nEND:VEVENT\n"
               "BEGIN:VEVENT\nUID:A\nRECURRENCE-ID:20261002T000000Z\nSUMMARY:朝礼（変更）\nDTSTART:20261002T060000Z\n"
               "DTEND:20261002T061500Z\nEND:VEVENT\nEND:VCALENDAR\n")
        got = sorted((e["start"], e["title"]) for e in cal.parse_ics(ics, *self.R))
        self.assertEqual(got, [("2026-10-01 09:00", "朝礼"), ("2026-10-02 15:00", "朝礼（変更）"), ("2026-10-03 09:00", "朝礼")])

    def test_unsupported_rule_is_shown_with_note_not_dropped(self):
        evs = self.ev("SUMMARY:月末の締め\nDTSTART:20250131T000000Z\nDTEND:20250131T010000Z\nRRULE:FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1")
        self.assertEqual(len(evs), 1)
        self.assertIn("note", evs[0])

    def test_biweekly_respects_wkst(self):
        evs = self.ev("SUMMARY:隔週\nDTSTART:20261004T000000Z\nDTEND:20261004T010000Z\nRRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=SU,TU;WKST=SU")
        self.assertEqual([e["start"][:10] for e in evs], ["2026-10-04", "2026-10-06"])

    def test_yearly_nth_weekday_in_month(self):
        evs = self.ev("SUMMARY:体育の日\nDTSTART;VALUE=DATE:20201012\nDTEND;VALUE=DATE:20201013\nRRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=2MO")
        self.assertEqual([e["start"] for e in evs], ["2026-10-12"])

    def test_foreign_timezone_is_converted(self):
        evs = self.ev("SUMMARY:NY会議\nDTSTART;TZID=America/New_York:20261002T090000\nDTEND;TZID=America/New_York:20261002T100000")
        self.assertEqual(evs[0]["start"], "2026-10-02 22:00")

    def test_all_day_without_dtend_on_first_day(self):
        evs = self.ev("SUMMARY:記念日\nDTSTART;VALUE=DATE:20261001")
        self.assertEqual([e["start"] for e in evs], ["2026-10-01"])

    def test_cancelled_is_hidden(self):
        self.assertEqual(self.ev("SUMMARY:中止\nSTATUS:CANCELLED\nDTSTART:20261002T010000Z\nDTEND:20261002T020000Z"), [])

    def test_count_includes_dtstart_even_if_not_matching(self):
        evs = self.ev("SUMMARY:研修\nDTSTART:20261001T010000Z\nDTEND:20261001T020000Z\nRRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=2")
        self.assertEqual([e["start"][:10] for e in evs], ["2026-10-01", "2026-10-05"])  # 木曜の初回＋月曜1回

    def test_unknown_charset_does_not_crash(self):
        self.assertEqual(mail.decode_bytes("見積".encode("cp932"), "x-sjis"), "見積")
        self.assertEqual(mail.decode_bytes("①～".encode("cp932"), "shift_jis"), "①～")
        self.assertEqual(mail.decode_bytes("abc".encode(), "no-such-charset"), "abc")

    def test_recipients_with_comma_in_display_name(self):
        self.assertEqual(mail.parse_recipients('"山田, 太郎" <y@a.jp>, b@b.jp,'), ["y@a.jp", "b@b.jp"])

    def test_confirm_code_changes_when_body_changes(self):
        a = mail.confirm_code("me@x.jp", ["a@b.jp"], [], [], "件名", "本文")
        self.assertNotEqual(a, mail.confirm_code("me@x.jp", ["a@b.jp"], [], [], "件名", "本文。"))

    def test_partly_refused_is_reported_as_failure(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = os.path.join(d, "mail.json")
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump({"address": "u@example.jp", "user": "u", "smtp_host": "smtp.example.jp",
                           "smtp_port": 465, "password_store": "file", "password": "x"}, f)
            body = os.path.join(d, "body.txt")
            Path(body).write_text("こんにちは", encoding="utf-8")
            code = mail.confirm_code("u@example.jp", ["a@example.jp"], [], ["u@example.jp"], "件名", "こんにちは")
            argv = ["mail_readonly.py", "send", "--to", "a@example.jp", "--subject", "件名", "--body-file", body,
                    "--confirm", code]
            fake = mock.MagicMock()
            fake.send_message.return_value = {"a@example.jp": (550, b"no such user")}
            with mock.patch.object(mail, "CONFIG_PATH", cfg_path), mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(mail, "smtp_login", return_value=fake), redirect_stdout(io.StringIO()) as buf:
                with self.assertRaises(SystemExit) as cm:
                    mail.main()
            self.assertEqual(cm.exception.code, 1)
            self.assertEqual(json.loads(buf.getvalue())["error"], "partly_refused")


secret = load("_secret")


class CodexRound1Test(unittest.TestCase):
    """2026-10-01 codex 1巡目の指摘の再発防止。"""

    R = (datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc), datetime(2026, 11, 30, 15, 0, tzinfo=timezone.utc))

    def test_keychain_failure_does_not_leak_password(self):
        failed = mock.Mock(returncode=1, stderr=b"security: SecKeychainItemCreateFromContent: User interaction is not allowed.")
        with mock.patch.object(secret, "SYSTEM", "Darwin"), \
                mock.patch("subprocess.run", side_effect=[mock.Mock(returncode=0), failed]):
            with self.assertRaises(Exception) as cm:
                secret.save("svc", "acct", "SECRET-PW-123", {})
        self.assertNotIn("SECRET-PW-123", str(cm.exception))
        self.assertNotIn("SECRET-PW-123", repr(cm.exception))

    def test_dpapi_failure_does_not_fall_back_to_plaintext(self):
        cfg = {}
        with mock.patch.object(secret, "SYSTEM", "Windows"), \
                mock.patch.object(secret, "_dpapi", side_effect=OSError("boom")):
            with self.assertRaises(Exception):
                secret.save("svc", "acct", "pw", cfg)
        self.assertNotIn("password", cfg)

    def test_credentials_not_sent_to_other_host_or_http(self):
        dav = cal.ReadOnlyCalDAV("https://caldav.icloud.com/", "u", "p")
        for bad in ["http://caldav.icloud.com/x", "https://evil.example.com/x"]:
            with mock.patch("urllib.request.urlopen") as op:
                with self.assertRaises(RuntimeError):
                    dav.request("PROPFIND", bad, "")
                op.assert_not_called()

    def test_server_must_be_https(self):
        dav = cal.ReadOnlyCalDAV("http://caldav.example.jp/", "u", "p")
        with mock.patch("urllib.request.urlopen") as op:
            with self.assertRaises(RuntimeError):
                dav.request("PROPFIND", "http://caldav.example.jp/", "")
            op.assert_not_called()

    def test_cancelled_single_occurrence_is_removed_from_series(self):
        ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:D\nSUMMARY:朝礼\nDTSTART:20261001T000000Z\nDTEND:20261001T001500Z\n"
               "RRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\nBEGIN:VEVENT\nUID:D\nRECURRENCE-ID:20261002T000000Z\nSTATUS:CANCELLED\n"
               "SUMMARY:朝礼\nDTSTART:20261002T000000Z\nDTEND:20261002T001500Z\nEND:VEVENT\nEND:VCALENDAR\n")
        got = [e["start"][:10] for e in cal.parse_ics(ics, *self.R)]
        self.assertEqual(got, ["2026-10-01", "2026-10-03"])

    def test_recurring_foreign_event_follows_its_own_dst(self):
        ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:NY\nSUMMARY:NY定例\nDTSTART;TZID=America/New_York:20261026T090000\n"
               "DTEND;TZID=America/New_York:20261026T100000\nRRULE:FREQ=WEEKLY;COUNT=2\nEND:VEVENT\nEND:VCALENDAR\n")
        got = [e["start"] for e in cal.parse_ics(ics, *self.R)]
        self.assertEqual(got, ["2026-10-26 22:00", "2026-11-02 23:00"])

    def test_preview_shows_whole_body(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = os.path.join(d, "mail.json")
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump({"address": "u@example.jp", "user": "u", "smtp_host": "s", "smtp_port": 465}, f)
            body = os.path.join(d, "body.txt")
            long_body = "あ" * 5000 + "末尾の大事な一文"
            Path(body).write_text(long_body, encoding="utf-8")
            argv = ["mail_readonly.py", "send", "--to", "a@example.jp", "--subject", "件名", "--body-file", body]
            with mock.patch.object(mail, "CONFIG_PATH", cfg_path), mock.patch.object(sys, "argv", argv), \
                    redirect_stdout(io.StringIO()) as buf:
                with self.assertRaises(SystemExit):
                    mail.main()
            self.assertTrue(json.loads(buf.getvalue())["preview"]["body"].endswith("末尾の大事な一文"))



class CodexRound2Test(unittest.TestCase):
    R = (datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc), datetime(2026, 10, 31, 15, 0, tzinfo=timezone.utc))

    def test_confirm_code_covers_sender_and_bcc(self):
        base = dict(to=["a@b.jp"], cc=[], subject="件名", body="本文")
        a = mail.confirm_code(sender="me@x.jp", bcc=["me@x.jp"], **base)
        self.assertNotEqual(a, mail.confirm_code(sender="other@x.jp", bcc=["me@x.jp"], **base))
        self.assertNotEqual(a, mail.confirm_code(sender="me@x.jp", bcc=[], **base))

    def test_utc_weekly_keeps_utc_weekday(self):
        ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:U\nSUMMARY:月曜18時UTC\nDTSTART:20261005T180000Z\nDTEND:20261005T190000Z\n"
               "RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=2\nEND:VEVENT\nEND:VCALENDAR\n")
        self.assertEqual([e["start"] for e in cal.parse_ics(ics, *self.R)], ["2026-10-06 03:00", "2026-10-13 03:00"])

    def test_rdate_adds_occurrences(self):
        ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:R\nSUMMARY:説明会\nDTSTART:20261001T010000Z\nDTEND:20261001T020000Z\n"
               "RDATE:20261003T010000Z\nEND:VEVENT\nEND:VCALENDAR\n")
        self.assertEqual([e["start"][:10] for e in cal.parse_ics(ics, *self.R)], ["2026-10-01", "2026-10-03"])

    def test_this_and_future_is_flagged_not_silently_wrong(self):
        ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:T\nSUMMARY:朝会\nDTSTART:20261001T000000Z\nDTEND:20261001T001500Z\n"
               "RRULE:FREQ=DAILY;COUNT=4\nEND:VEVENT\nBEGIN:VEVENT\nUID:T\nRECURRENCE-ID;RANGE=THISANDFUTURE:20261002T000000Z\n"
               "SUMMARY:朝会\nDTSTART:20261002T020000Z\nDTEND:20261002T021500Z\nEND:VEVENT\nEND:VCALENDAR\n")
        evs = sorted(cal.parse_ics(ics, *self.R), key=lambda e: e["start"])
        later = [e for e in evs if e["start"] >= "2026-10-03"]
        self.assertTrue(later)
        for e in later:
            self.assertIn("note", e)



class CodexRound3Test(unittest.TestCase):
    R = (datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc), datetime(2026, 10, 31, 15, 0, tzinfo=timezone.utc))

    def test_attached_eml_does_not_replace_body(self):
        from email.message import EmailMessage
        inner = EmailMessage(); inner["Subject"] = "old"; inner.set_content("ATTACHMENT BODY")
        outer = EmailMessage(); outer["Subject"] = "now"
        outer.set_content("<p>CURRENT BODY</p>", subtype="html")
        outer.add_attachment(inner)
        raw = outer.as_bytes()
        box = mail.ReadOnlyIMAP.__new__(mail.ReadOnlyIMAP)
        box.conn = mock.Mock()
        box.conn.uid.return_value = ("OK", [(b"1 (BODY[] {1}", raw), b")"])
        b = box.body(b"1")
        self.assertIn("CURRENT BODY", b["body"])
        self.assertNotIn("ATTACHMENT BODY", b["body"])

    def test_missing_message_is_an_error(self):
        box = mail.ReadOnlyIMAP.__new__(mail.ReadOnlyIMAP)
        box.conn = mock.Mock()
        box.conn.uid.return_value = ("OK", [None])
        with self.assertRaises(RuntimeError):
            box.body(b"9")
        with self.assertRaises(RuntimeError):
            box.headers(b"9")

    def test_rdate_only_respects_exdate_on_first(self):
        ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:X\nSUMMARY:会\nDTSTART:20261001T010000Z\nDTEND:20261001T020000Z\n"
               "RDATE:20261003T010000Z\nEXDATE:20261001T010000Z\nEND:VEVENT\nEND:VCALENDAR\n")
        self.assertEqual([e["start"][:10] for e in cal.parse_ics(ics, *self.R)], ["2026-10-03"])

    def test_rdate_duplicate_of_rrule_is_shown_once(self):
        ics = ("BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:Y\nSUMMARY:会\nDTSTART:20261001T010000Z\nDTEND:20261001T020000Z\n"
               "RRULE:FREQ=DAILY;COUNT=2\nRDATE:20261002T010000Z\nEND:VEVENT\nEND:VCALENDAR\n")
        self.assertEqual([e["start"][:10] for e in cal.parse_ics(ics, *self.R)], ["2026-10-01", "2026-10-02"])


if __name__ == "__main__":
    unittest.main()
