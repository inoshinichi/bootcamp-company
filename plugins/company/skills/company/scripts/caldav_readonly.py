#!/usr/bin/env python3
"""
bootcamp-company: iPhone のカレンダー（iCloud）などを CalDAV で「読むだけ」の道具。
Python 標準ライブラリだけで動く。予定の作成・変更・削除は一切しない（GET 系の PROPFIND / REPORT だけ）。

使い方:
  python3 caldav_readonly.py setup               # 受講者が自分で実行（Apple ID と「App 用パスワード」を入れる）
  python3 caldav_readonly.py check               # 連携チェック（今日と明日の件数）
  python3 caldav_readonly.py events --days 7     # 今日から7日分の予定
出力はすべて JSON（UTF-8）。
"""
import argparse
import base64
import getpass
import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "bootcamp-company")
CONFIG_PATH = os.path.join(CONFIG_DIR, "calendar.json")
KEYCHAIN_SERVICE = "bootcamp-company-calendar"
DEFAULT_SERVER = "https://caldav.icloud.com/"
JST = timezone(timedelta(hours=9))
NS = {"d": "DAV:", "c": "urn:ietf:params:xml:ns:caldav"}


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.exit(code)


# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------

def load_config():
    if not os.path.exists(CONFIG_PATH):
        out({"ok": False, "error": "not_configured",
             "hint": "まだ設定されていません。受講者に別のターミナルで `setup` を実行してもらってください。"}, 2)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_password(cfg):
    env = os.environ.get("BOOTCAMP_CAL_PASSWORD")
    if env:
        return env
    if cfg.get("password_store") == "keychain":
        r = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", cfg["user"], "-w"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.rstrip("\n")
        out({"ok": False, "error": "password_not_found", "hint": "キーチェーンにパスワードがありません。setup をやり直してください。"}, 2)
    return cfg.get("password", "")


# ---------------------------------------------------------------------------
# CalDAV（読むだけ）
# ---------------------------------------------------------------------------

class ReadOnlyCalDAV:
    ALLOWED = {"PROPFIND", "REPORT"}

    def __init__(self, server, user, password):
        self.server = server
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.auth = f"Basic {token}"

    def request(self, method, url, body, depth="0"):
        if method not in self.ALLOWED:
            raise RuntimeError(f"読み取り専用のため {method} は実行しません")
        req = urllib.request.Request(url, data=body.encode("utf-8"), method=method)
        req.add_header("Authorization", self.auth)
        req.add_header("Content-Type", "application/xml; charset=utf-8")
        req.add_header("Depth", depth)
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.geturl(), ET.fromstring(res.read())

    def principal(self):
        body = ('<d:propfind xmlns:d="DAV:"><d:prop><d:current-user-principal/></d:prop></d:propfind>')
        base, tree = self.request("PROPFIND", self.server, body)
        href = tree.find(".//d:current-user-principal/d:href", NS)
        return urljoin(base, href.text.strip())

    def calendar_home(self, principal_url):
        body = ('<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
                '<d:prop><c:calendar-home-set/></d:prop></d:propfind>')
        base, tree = self.request("PROPFIND", principal_url, body)
        href = tree.find(".//c:calendar-home-set/d:href", NS)
        return urljoin(base, href.text.strip())

    def calendars(self, home_url):
        body = ('<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
                '<d:prop><d:displayname/><d:resourcetype/><c:supported-calendar-component-set/></d:prop></d:propfind>')
        base, tree = self.request("PROPFIND", home_url, body, depth="1")
        cals = []
        for resp in tree.findall("d:response", NS):
            if resp.find(".//d:resourcetype/c:calendar", NS) is None:
                continue
            comps = [c.get("name") for c in resp.findall(".//c:supported-calendar-component-set/c:comp", NS)]
            if comps and "VEVENT" not in comps:
                continue  # リマインダー等は除く
            name = resp.findtext(".//d:displayname", default="", namespaces=NS)
            cals.append({"name": name, "url": urljoin(base, resp.findtext("d:href", namespaces=NS).strip())})
        return cals

    def events(self, cal_url, start, end):
        s = start.strftime("%Y%m%dT%H%M%SZ")
        e = end.strftime("%Y%m%dT%H%M%SZ")
        body = ('<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
                '<d:prop><c:calendar-data/></d:prop>'
                '<c:filter><c:comp-filter name="VCALENDAR"><c:comp-filter name="VEVENT">'
                f'<c:time-range start="{s}" end="{e}"/>'
                '</c:comp-filter></c:comp-filter></c:filter></c:calendar-query>')
        _, tree = self.request("REPORT", cal_url, body, depth="1")
        items = []
        for data in tree.findall(".//c:calendar-data", NS):
            items.extend(parse_ics(data.text or "", start, end))
        return items


# ---------------------------------------------------------------------------
# iCalendar の最小限の読み取り
# ---------------------------------------------------------------------------

def unfold(text):
    lines = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def parse_dt(prop, value):
    """戻り値: (datetime[JST], 終日かどうか)"""
    if "VALUE=DATE" in prop or (len(value) == 8 and value.isdigit()):
        d = datetime.strptime(value[:8], "%Y%m%d")
        return d.replace(tzinfo=JST), True
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(JST), False
    # TZID 付きやタイムゾーン無しは、受講者は日本在住が前提なので日本時間として扱う
    return datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(tzinfo=JST), False


WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
SUPPORTED_RRULE_KEYS = {"FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY", "BYMONTHDAY", "BYMONTH", "WKST"}


def parse_rrule(value):
    return dict(part.split("=", 1) for part in value.split(";") if "=" in part)


def month_diff(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


def matches_rule(rule, first, day):
    """day（date）が繰り返しの規則に当てはまるか。first は初回の date。"""
    freq = rule.get("FREQ")
    interval = int(rule.get("INTERVAL", "1"))
    bymonth = [int(m) for m in rule["BYMONTH"].split(",")] if "BYMONTH" in rule else None
    if bymonth and day.month not in bymonth:
        return False
    byday = rule.get("BYDAY", "").split(",") if rule.get("BYDAY") else []
    if freq == "DAILY":
        return (day - first).days % interval == 0 and (not byday or WEEKDAYS[day.weekday()] in byday)
    if freq == "WEEKLY":
        week0 = first - timedelta(days=first.weekday())
        week = day - timedelta(days=day.weekday())
        if ((week - week0).days // 7) % interval:
            return False
        days = [d[-2:] for d in byday] or [WEEKDAYS[first.weekday()]]
        return WEEKDAYS[day.weekday()] in days
    if freq == "MONTHLY":
        if month_diff(first, day) % interval:
            return False
        if "BYMONTHDAY" in rule:
            nxt = (day.replace(day=28) + timedelta(days=4)).replace(day=1)
            last = (nxt - timedelta(days=1)).day
            wanted = [int(x) if int(x) > 0 else last + 1 + int(x) for x in rule["BYMONTHDAY"].split(",")]
            return day.day in wanted
        if byday:
            for d in byday:
                wd, n = d[-2:], d[:-2]
                if WEEKDAYS[day.weekday()] != wd:
                    continue
                if not n:
                    return True
                n = int(n)
                if n > 0 and (day.day - 1) // 7 + 1 == n:
                    return True
                nxt = (day.replace(day=28) + timedelta(days=4)).replace(day=1)
                last = (nxt - timedelta(days=1)).day
                if n < 0 and (last - day.day) // 7 + 1 == -n:
                    return True
            return False
        return day.day == first.day
    if freq == "YEARLY":
        if (day.year - first.year) % interval:
            return False
        if not bymonth and day.month != first.month:
            return False
        return day.day == first.day
    return False


def expand(ev, start, end):
    """繰り返しの予定を、start〜end の範囲の1回ずつに展開する（手元で計算）。"""
    rule = parse_rrule(ev["rrule"])
    if set(rule) - SUPPORTED_RRULE_KEYS or rule.get("FREQ") not in ("DAILY", "WEEKLY", "MONTHLY", "YEARLY"):
        one = dict(ev)
        one["note"] = "繰り返しの予定（細かい規則のため、1回目の日付だけ表示）"
        return [one]
    first = ev["start"]
    dur = ev.get("end", first) - first
    count = int(rule["COUNT"]) if "COUNT" in rule else None
    until = parse_dt("", rule["UNTIL"])[0] if "UNTIL" in rule else None
    exdates = {x.date() if ev.get("all_day") else x for x in ev.get("exdates", [])}
    s_jst, e_jst = start.astimezone(JST), end.astimezone(JST)
    out_list, n, day = [], 0, first.date()
    last_day = e_jst.date()
    while day <= last_day:
        if matches_rule(rule, first.date(), day):
            occ = datetime.combine(day, first.timetz())
            if until and occ > until:
                break
            n += 1
            if count and n > count:
                break
            key = occ.date() if ev.get("all_day") else occ
            if key not in exdates and occ < e_jst and occ + dur > s_jst:
                one = dict(ev)
                one["start"], one["end"] = occ, occ + dur
                out_list.append(one)
        day += timedelta(days=1)
    return out_list


def parse_ics(text, start, end):
    events, cur = [], None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {"exdates": []}
        elif line == "END:VEVENT" and cur is not None:
            if "start" in cur:
                events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            prop, value = line.split(":", 1)
            name = prop.split(";")[0].upper()
            value = value.replace("\\n", " ").replace("\\,", ",").replace("\\;", ";")
            if name == "SUMMARY":
                cur["title"] = value
            elif name == "LOCATION":
                cur["location"] = value
            elif name == "UID":
                cur["uid"] = value
            elif name == "RRULE":
                cur["rrule"] = value
            elif name == "RECURRENCE-ID":
                cur["recurrence_id"] = parse_dt(prop, value)[0]
            elif name == "EXDATE":
                cur["exdates"].extend(parse_dt(prop, v)[0] for v in value.split(","))
            elif name in ("DTSTART", "DTEND"):
                dt, all_day = parse_dt(prop, value)
                cur["start" if name == "DTSTART" else "end"] = dt
                if name == "DTSTART":
                    cur["all_day"] = all_day
    # 個別に変更された回（RECURRENCE-ID）は、元の繰り返しのその回と差し替える
    overridden = {(e.get("uid"), e["recurrence_id"]) for e in events if "recurrence_id" in e}
    flat = []
    for ev in events:
        if "rrule" in ev and "recurrence_id" not in ev:
            for occ in expand(ev, start, end):
                if (ev.get("uid"), occ["start"]) not in overridden:
                    flat.append(occ)
        else:
            flat.append(ev)
    res = []
    for ev in flat:
        s = ev["start"]
        if s >= end.astimezone(JST) or ev.get("end", s) <= start.astimezone(JST):
            continue
        item = {"title": ev.get("title", "(件名なし)"), "location": ev.get("location", ""),
                "all_day": ev.get("all_day", False),
                "start": s.strftime("%Y-%m-%d") if ev.get("all_day") else s.strftime("%Y-%m-%d %H:%M"),
                "end": ev["end"].strftime("%Y-%m-%d %H:%M") if "end" in ev and not ev.get("all_day") else ""}
        if ev.get("note"):
            item["note"] = ev["note"]
        res.append(item)
    return res


# ---------------------------------------------------------------------------
# コマンド
# ---------------------------------------------------------------------------

def connect(cfg):
    return ReadOnlyCalDAV(cfg.get("server", DEFAULT_SERVER), cfg["user"], get_password(cfg))


def collect(cfg, days):
    dav = connect(cfg)
    today = datetime.now(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    start, end = today.astimezone(timezone.utc), (today + timedelta(days=days)).astimezone(timezone.utc)
    home = cfg.get("home_url") or dav.calendar_home(dav.principal())
    result = []
    for cal in dav.calendars(home):
        for ev in dav.events(cal["url"], start, end):
            ev["calendar"] = cal["name"]
            result.append(ev)
    result.sort(key=lambda e: e["start"])
    return result


def cmd_setup(args):
    print("iPhone のカレンダー（iCloud）の連携設定をします。")
    print("※ パスワードは Apple ID のパスワードではなく、account.apple.com で作る『App 用パスワード』です。")
    user = input("Apple ID（メールアドレス）: ").strip()
    password = getpass.getpass("App 用パスワード（表示されません）: ").strip()
    server = input(f"サーバー [{DEFAULT_SERVER}]: ").strip() or DEFAULT_SERVER
    cfg = {"user": user, "server": server}
    try:
        dav = ReadOnlyCalDAV(server, user, password)
        home = dav.calendar_home(dav.principal())
        cals = dav.calendars(home)
    except urllib.error.HTTPError as e:
        print(f"\n× つながりませんでした（{e.code}）。Apple ID と App 用パスワードを確かめてください。何も保存していません。")
        sys.exit(1)
    except Exception as e:
        print(f"\n× つながりませんでした: {e}")
        sys.exit(1)
    cfg["home_url"] = home
    if platform.system() == "Darwin":
        subprocess.run(["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE, "-a", user], capture_output=True)
        subprocess.run(["security", "add-generic-password", "-s", KEYCHAIN_SERVICE, "-a", user, "-w", password],
                       check=True, capture_output=True)
        cfg["password_store"] = "keychain"
    else:
        cfg["password_store"] = "file"
        cfg["password"] = password
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass
    names = "、".join(c["name"] for c in cals) or "(なし)"
    print(f"\n○ つながりました。見えたカレンダー: {names}")
    print("  秘書の画面に戻って『連携チェック』と言ってください。")


def cmd_check(args):
    cfg = load_config()
    try:
        evs = collect(cfg, 2)
    except urllib.error.HTTPError as e:
        out({"ok": False, "error": f"http_{e.code}",
             "hint": "401 なら App 用パスワードが無効になっています（Apple ID のパスワードを変えると無効になります）。setup をやり直してください。"}, 1)
    out({"ok": True, "today_and_tomorrow": len(evs), "first": evs[0]["title"] if evs else None})


def cmd_events(args):
    cfg = load_config()
    evs = collect(cfg, args.days)
    out({"ok": True, "days": args.days, "count": len(evs), "events": evs})


def main():
    p = argparse.ArgumentParser(description="読み取り専用のカレンダー連携（CalDAV / iCloud）")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    sub.add_parser("check")
    pe = sub.add_parser("events")
    pe.add_argument("--days", type=int, default=7)
    args = p.parse_args()
    try:
        {"setup": cmd_setup, "check": cmd_check, "events": cmd_events}[args.cmd](args)
    except SystemExit:
        raise
    except Exception as e:
        out({"ok": False, "error": type(e).__name__, "detail": str(e)}, 1)


if __name__ == "__main__":
    main()
