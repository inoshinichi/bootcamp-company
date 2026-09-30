-- bootcamp-company: Mac の「カレンダー」アプリに入っている予定を「読むだけ」の道具。
-- iCloud・Google・会社のカレンダーなど、カレンダーアプリに入れてあるものが全部見える。
-- 予定の作成・変更・削除はしない。
--
-- 使い方（秘書が実行する）:
--   osascript mac_calendar.applescript 2      -- 今日から2日分
--
-- ⚠️ 初回だけ「ターミナル（または Cursor）がカレンダーにアクセスしようとしています」と
--    Mac が確認を出す。受講者に「許可」を押してもらう（押す前に秘書が一声かける）。
-- ⚠️ 繰り返しの予定は、最初の回の日付でしか拾えないことがある（カレンダーアプリの仕様）。
--    抜けが気になる受講者には iCloud の道（caldav_readonly.py）を案内する。

on run argv
	set dayCount to 2
	if (count of argv) > 0 then set dayCount to (item 1 of argv) as integer
	set startDate to current date
	set time of startDate to 0
	set endDate to startDate + dayCount * days
	set outLines to {}
	tell application "Calendar"
		repeat with cal in calendars
			set calName to name of cal
			try
				set evs to (every event of cal whose start date < endDate and end date > startDate)
				repeat with ev in evs
					set t to summary of ev
					set s to start date of ev
					set end of outLines to (my fmt(s)) & tab & calName & tab & t
				end repeat
			end try
		end repeat
	end tell
	set AppleScript's text item delimiters to linefeed
	return outLines as text
end run

on fmt(d)
	set y to year of d as integer
	set m to month of d as integer
	set dd to day of d as integer
	set hh to hours of d
	set mi to minutes of d
	return (y as text) & "-" & my pad(m) & "-" & my pad(dd) & " " & my pad(hh) & ":" & my pad(mi)
end fmt

on pad(n)
	if n < 10 then return "0" & (n as text)
	return n as text
end pad
