#!/usr/bin/env python3
"""
bootcamp-company: iPhone のカレンダー（iCloud）などを CalDAV で「読むだけ」の道具。
Python 標準ライブラリだけで動く。予定の作成・変更・削除は一切しない（PROPFIND / REPORT だけ）。

使い方:
  python3 caldav_readonly.py setup               # 受講者が自分で実行（Apple ID と「App 用パスワード」を入れる）
  python3 caldav_readonly.py check               # 連携チェック（今日と明日の件数）
  python3 caldav_readonly.py events --days 7     # 今日から7日分の予定
Windows は python3 の代わりに `py -3`。出力はすべて JSON（UTF-8）。
"""
import argparse
import base64
import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _secret  # noqa: E402

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
WINDOWS_TZ = {"Tokyo Standard Time": "Asia/Tokyo", "Korea Standard Time": "Asia/Seoul",
              "China Standard Time": "Asia/Shanghai", "UTC": "UTC", "GMT Standard Time": "Europe/London",
              "Eastern Standard Time": "America/New_York", "Pacific Standard Time": "America/Los_Angeles"}


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
    pw = _secret.load(KEYCHAIN_SERVICE, cfg["user"], cfg)
    if pw is None:
        out({"ok": False, "error": "password_not_found", "hint": "保存したパスワードが見つかりません。setup をやり直してください。"}, 2)
    return pw


# ---------------------------------------------------------------------------
# CalDAV（読むだけ）
# ---------------------------------------------------------------------------

class ReadOnlyCalDAV:
    ALLOWED = {"PROPFIND", "REPORT"}

    def __init__(self, server, user, password):
        self.server = server
        self.host = urlparse(server).hostname or ""
        token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode()
        self.auth = f"Basic {token}"

    def _may_follow(self, url):
        """パスワードを付けて付いていってよい転送先か（https で、同じサーバーか iCloud の中だけ）。"""
        u = urlparse(url)
        if u.scheme != "https":
            return False
        h = u.hostname or ""
        return h == self.host or (self.host.endswith("icloud.com") and h.endswith(".icloud.com"))

    def request(self, method, url, body, depth="0"):
        if method not in self.ALLOWED:
            raise RuntimeError(f"読み取り専用のため {method} は実行しません")
        for _ in range(5):  # urllib は PROPFIND / REPORT の転送を追わないので、自分で追う
            if not self._may_follow(url):
                # パスワードを付けて送るのは https の、設定したサーバー（iCloud なら iCloud の中）だけ
                raise RuntimeError(f"安全でない、または知らない宛先にはパスワードを送りません: {url}")
            req = urllib.request.Request(url, data=body.encode("utf-8"), method=method)
            req.add_header("Authorization", self.auth)
            req.add_header("Content-Type", "application/xml; charset=utf-8")
            req.add_header("Depth", depth)
            try:
                with urllib.request.urlopen(req, timeout=30) as res:
                    return res.geturl(), ET.fromstring(res.read())
            except urllib.error.HTTPError as e:
                loc = e.headers.get("Location") if e.code in (301, 302, 303, 307, 308) else None
                if not loc:
                    raise
                url = urljoin(url, loc)  # 次の周の頭で宛先を確かめる
        raise RuntimeError("転送が多すぎます")

    def principal(self):
        body = '<d:propfind xmlns:d="DAV:"><d:prop><d:current-user-principal/></d:prop></d:propfind>'
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
# iCalendar の読み取り（標準ライブラリだけ）
# ---------------------------------------------------------------------------

def unfold(text):
    lines = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def split_prop(line):
    """'DTSTART;TZID=Asia/Tokyo:20261001T100000' → ('DTSTART', {'TZID': 'Asia/Tokyo'}, '20261001T100000')"""
    head, value = line.split(":", 1)
    parts = head.split(";")
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.upper()] = v.strip('"')
    return parts[0].upper(), params, value


def tz_for(tzid):
    if not tzid:
        return JST
    name = WINDOWS_TZ.get(tzid, tzid)
    if name in ("Asia/Tokyo", "Japan"):
        return JST
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        return JST  # Windows で時差の表が無いとき等。受講者は日本在住が前提なので日本時間として扱う


def parse_dt(params, value):
    """戻り値: (datetime[JST], 終日かどうか)"""
    value = value.strip()
    if params.get("VALUE") == "DATE" or (len(value) == 8 and value.isdigit()):
        return datetime.strptime(value[:8], "%Y%m%d").replace(tzinfo=JST), True
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(JST), False
    local = datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(tzinfo=tz_for(params.get("TZID")))
    return local.astimezone(JST), False


def parse_duration(value):
    m = re.fullmatch(r"([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", value.strip())
    if not m:
        return None
    sign, w, d, h, mi, s = m.groups()
    td = timedelta(weeks=int(w or 0), days=int(d or 0), hours=int(h or 0), minutes=int(mi or 0), seconds=int(s or 0))
    return -td if sign == "-" else td


def read_vevents(text):
    """VEVENT の直下の項目だけを読む（中の VALARM などの UID・SUMMARY に上書きされないように）。"""
    events, stack, cur = [], [], None
    for line in unfold(text):
        if line.startswith("BEGIN:"):
            stack.append(line[6:].strip().upper())
            if stack[-1] == "VEVENT":
                cur = {"exdates": []}
            continue
        if line.startswith("END:"):
            name = stack.pop() if stack else ""
            if name == "VEVENT" and cur is not None:
                if "start" in cur:
                    events.append(cur)
                cur = None
            continue
        if cur is None or not stack or stack[-1] != "VEVENT" or ":" not in line:
            continue
        name, params, value = split_prop(line)
        value = value.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",").replace("\\;", ";")
        if name == "SUMMARY":
            cur["title"] = value
        elif name == "LOCATION":
            cur["location"] = value
        elif name == "UID":
            cur["uid"] = value
        elif name == "STATUS":
            cur["status"] = value.upper()
        elif name == "RRULE":
            cur["rrule"] = value
        elif name == "RECURRENCE-ID":
            cur["recurrence_id"] = parse_dt(params, value)[0]
            if params.get("RANGE", "").upper() == "THISANDFUTURE":
                cur["this_and_future"] = True
        elif name == "RDATE" and params.get("VALUE", "").upper() != "PERIOD":
            cur.setdefault("rdates", []).extend(parse_dt(params, v)[0] for v in value.split(",") if v)
        elif name == "EXDATE":
            cur["exdates"].extend(parse_dt(params, v)[0] for v in value.split(",") if v)
        elif name == "DURATION":
            cur["duration"] = parse_duration(value)
        elif name in ("DTSTART", "DTEND"):
            dt, all_day = parse_dt(params, value)
            cur["start" if name == "DTSTART" else "end"] = dt
            if name == "DTSTART":
                cur["all_day"] = all_day
                if not all_day and value.strip().endswith("Z"):
                    # 繰り返しは「登録された時刻の基準」で数える（UTC で登録された予定は UTC の曜日で）
                    cur["start_local"] = dt.astimezone(timezone.utc)
                elif not all_day and params.get("TZID"):
                    # 予定が作られた地域の時刻で数える（夏時間の切り替えをまたいでもずれないように）
                    cur["start_local"] = dt.astimezone(tz_for(params.get("TZID")))
    for ev in events:
        if "end" not in ev:
            if ev.get("duration") is not None:
                ev["end"] = ev["start"] + ev["duration"]
            else:
                ev["end"] = ev["start"] + (timedelta(days=1) if ev.get("all_day") else timedelta(0))
    return events


# ---------------------------------------------------------------------------
# 繰り返しの予定の展開（iCloud はサーバー側で展開してくれないため、手元で計算する）
# ---------------------------------------------------------------------------

WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
SUPPORTED_RRULE_KEYS = {"FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY", "BYMONTHDAY", "BYMONTH", "WKST"}


def parse_rrule(value):
    return {k.upper(): v for k, v in (part.split("=", 1) for part in value.split(";") if "=" in part)}


def last_day_of_month(d):
    nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return (nxt - timedelta(days=1)).day


def byday_in_month(byday, day):
    """BYDAY（例: MO, 2TU, -1FR）に day が当てはまるか（「第n◯曜」は月の中で数える）。"""
    for d in byday:
        wd, n = d[-2:], d[:-2]
        if WEEKDAYS[day.weekday()] != wd:
            continue
        if not n or n == "+":
            return True
        n = int(n)
        if n > 0 and (day.day - 1) // 7 + 1 == n:
            return True
        if n < 0 and (last_day_of_month(day) - day.day) // 7 + 1 == -n:
            return True
    return False


def bymonthday_ok(rule, day):
    last = last_day_of_month(day)
    wanted = [int(x) if int(x) > 0 else last + 1 + int(x) for x in rule["BYMONTHDAY"].split(",")]
    return day.day in wanted


def matches_rule(rule, first, day):
    """day（date）が繰り返しの規則に当てはまるか。first は初回の date。"""
    freq = rule.get("FREQ")
    interval = int(rule.get("INTERVAL", "1"))
    byday = [x for x in rule.get("BYDAY", "").split(",") if x]
    bymonth = [int(m) for m in rule["BYMONTH"].split(",")] if "BYMONTH" in rule else None
    if bymonth and day.month not in bymonth:
        return False
    if freq == "DAILY":
        if (day - first).days % interval:
            return False
        if byday and WEEKDAYS[day.weekday()] not in [d[-2:] for d in byday]:
            return False
        return "BYMONTHDAY" not in rule or bymonthday_ok(rule, day)
    if freq == "WEEKLY":
        wkst = WEEKDAYS.index(rule.get("WKST", "MO"))
        week0 = first - timedelta(days=(first.weekday() - wkst) % 7)
        week = day - timedelta(days=(day.weekday() - wkst) % 7)
        if ((week - week0).days // 7) % interval:
            return False
        days = [d[-2:] for d in byday] or [WEEKDAYS[first.weekday()]]
        return WEEKDAYS[day.weekday()] in days
    if freq == "MONTHLY":
        if ((day.year - first.year) * 12 + day.month - first.month) % interval:
            return False
        if "BYMONTHDAY" in rule or byday:
            return ("BYMONTHDAY" not in rule or bymonthday_ok(rule, day)) and (not byday or byday_in_month(byday, day))
        return day.day == first.day
    if freq == "YEARLY":
        if (day.year - first.year) % interval:
            return False
        if not bymonth and day.month != first.month:
            return False
        if "BYMONTHDAY" in rule or byday:
            return ("BYMONTHDAY" not in rule or bymonthday_ok(rule, day)) and (not byday or byday_in_month(byday, day))
        return day.day == first.day
    return False


def expand(ev, start, end):
    """繰り返しの予定を、start〜end の範囲の1回ずつに展開する。"""
    rule = parse_rrule(ev["rrule"])
    first = ev.get("start_local", ev["start"])  # 予定が作られた地域の時刻
    unsupported = set(rule) - SUPPORTED_RRULE_KEYS or rule.get("FREQ") not in ("DAILY", "WEEKLY", "MONTHLY", "YEARLY")
    if not unsupported and rule.get("FREQ") == "YEARLY" and rule.get("BYDAY") and "BYMONTH" not in rule \
            and any(re.match(r"^[+-]?\d", d) for d in rule["BYDAY"].split(",")):
        unsupported = True  # 「毎年 第20月曜」のような年単位の数え方は対応しない
    if unsupported:
        one = dict(ev)
        one["note"] = "繰り返しの予定（細かい規則のため、この期間の日付は計算できません。初回の日付を表示）"
        one["force_show"] = True
        return [one]
    dur = ev["end"] - first
    count = int(rule["COUNT"]) if "COUNT" in rule else None
    until = None
    if "UNTIL" in rule:
        u, u_all_day = parse_dt({}, rule["UNTIL"])
        until = datetime.combine(u.date(), time(23, 59, 59), tzinfo=JST) if u_all_day else u
    exdates = {x.date() if ev.get("all_day") else x.timestamp() for x in ev.get("exdates", [])}
    s_jst, e_jst = start.astimezone(JST), end.astimezone(JST)
    result = []

    def consider(occ):
        occ = occ.astimezone(JST)
        key = occ.date() if ev.get("all_day") else occ.timestamp()
        if key not in exdates and occ < e_jst and occ + dur > s_jst:
            one = dict(ev)
            one["start"], one["end"] = occ, occ + dur
            result.append(one)

    consider(first)  # 初回（DTSTART）は規則に合わなくても必ず1回目に数える（RFC 5545）
    n = 1
    day = first.date() + timedelta(days=1)
    last_day = e_jst.astimezone(first.tzinfo).date() + timedelta(days=1)
    while day <= last_day and (count is None or n < count):
        if matches_rule(rule, first.date(), day):
            occ = datetime.combine(day, first.timetz()).astimezone(JST)
            if until and occ > until:
                break
            n += 1
            consider(occ)
        day += timedelta(days=1)
    return result


def parse_ics(text, start, end):
    all_events = read_vevents(text)
    # 個別に変更・取り消された回（RECURRENCE-ID）は、元の繰り返しのその回と差し替える（取り消しは消すだけ）
    overridden = {(e.get("uid"), e["recurrence_id"].timestamp()) for e in all_events if "recurrence_id" in e}
    # 「この回以降を変更」（RANGE=THISANDFUTURE）は、その回より後を正しく計算できないので注記を付ける
    future_changed = {}
    for e in all_events:
        if e.get("this_and_future"):
            t = e["recurrence_id"].timestamp()
            future_changed[e.get("uid")] = min(t, future_changed.get(e.get("uid"), t))
    events = [e for e in all_events if e.get("status") != "CANCELLED"]
    flat = []
    for ev in events:
        if ("rrule" in ev or ev.get("rdates")) and "recurrence_id" not in ev:
            occs = expand(ev, start, end) if "rrule" in ev else [ev] if ev["end"] > start.astimezone(JST) else []
            for extra in ev.get("rdates", []):  # 追加の開催日（RDATE）
                one = dict(ev)
                one["start"], one["end"] = extra, extra + (ev["end"] - ev["start"])
                exd = {x.timestamp() for x in ev.get("exdates", [])}
                if extra.timestamp() not in exd:
                    occs.append(one)
            for occ in occs:
                if (ev.get("uid"), occ["start"].timestamp()) in overridden:
                    continue
                cut = future_changed.get(ev.get("uid"))
                if cut is not None and occ["start"].timestamp() > cut:
                    occ = dict(occ)
                    occ["note"] = "「この回以降を変更」された予定です。変更前の時刻で表示しているので、カレンダーで確かめてください"
                flat.append(occ)
        else:
            flat.append(ev)
    s_jst, e_jst = start.astimezone(JST), end.astimezone(JST)
    res = []
    for ev in flat:
        s, e = ev["start"], ev["end"]
        if not ev.get("force_show") and (s >= e_jst or (e <= s_jst if e > s else s < s_jst)):
            continue
        item = {"title": ev.get("title", "(件名なし)"), "location": ev.get("location", ""),
                "all_day": ev.get("all_day", False),
                "start": s.strftime("%Y-%m-%d") if ev.get("all_day") else s.strftime("%Y-%m-%d %H:%M"),
                "end": "" if ev.get("all_day") else e.strftime("%Y-%m-%d %H:%M")}
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
    password = getpass.getpass("App 用パスワード（入力しても画面には出ません。貼り付けたら Enter）: ").strip()
    server = input(f"サーバー（そのまま Enter でよい） [{DEFAULT_SERVER}]: ").strip() or DEFAULT_SERVER
    cfg = {"user": user, "server": server}
    try:
        dav = ReadOnlyCalDAV(server, user, password)
        home = dav.calendar_home(dav.principal())
        cals = dav.calendars(home)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("\n× Apple ID か App 用パスワードが違うようです。もう一度確かめてください。何も保存していません。")
        else:
            print(f"\n× サーバーから思わぬ返事がありました（{e.code}）。秘書にこの番号を伝えてください。何も保存していません。")
        sys.exit(1)
    except Exception as e:
        print(f"\n× つながりませんでした: {e}\n  秘書にこの文を伝えてください。何も保存していません。")
        sys.exit(1)
    cfg["home_url"] = home
    _secret.save(KEYCHAIN_SERVICE, user, password, cfg)
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
