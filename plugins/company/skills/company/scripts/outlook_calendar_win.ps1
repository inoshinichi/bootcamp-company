# bootcamp-company: Windows の「パソコンの Outlook（従来版）」の予定表を「読むだけ」の道具。
# 予定の作成・変更・削除はしない（Items を読むだけ）。
#
# 使い方（秘書が実行する）:
#   powershell -NoProfile -ExecutionPolicy Bypass -File outlook_calendar_win.ps1 -Days 2
#
# ⚠️ 「新しい Outlook」では動かない（外部から読む仕組み＝COM が無い）。
#    その場合は ok=false / error=new_outlook_or_not_installed を返すので、秘書は
#    「従来の Outlook に切り替える」か「Google カレンダーをおすすめ」を案内する。
param(
  [int]$Days = 2
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Out-Json($obj) {
  $obj | ConvertTo-Json -Depth 5 -Compress:$false
}

try {
  $outlook = New-Object -ComObject Outlook.Application -ErrorAction Stop
} catch {
  Out-Json @{
    ok = $false
    error = "new_outlook_or_not_installed"
    hint = "従来版の Outlook が見つかりません。『新しい Outlook』を使っている場合、この方法では読めません。"
  }
  exit 1
}

try {
  $ns = $outlook.GetNamespace("MAPI")
  $calendar = $ns.GetDefaultFolder(9)   # 9 = olFolderCalendar
  $items = $calendar.Items
  $items.IncludeRecurrences = $true     # 繰り返しの予定も1件ずつ展開する
  $items.Sort("[Start]")

  $start = (Get-Date).Date
  $end = $start.AddDays($Days)
  # Restrict の日付はその PC の地域設定の書式で渡す必要がある
  $fmt = (Get-Culture).DateTimeFormat.ShortDatePattern + " " + (Get-Culture).DateTimeFormat.ShortTimePattern
  $filter = "[Start] < '" + $end.ToString($fmt) + "' AND [End] > '" + $start.ToString($fmt) + "'"
  $found = $items.Restrict($filter)

  $events = @()
  foreach ($it in $found) {
    $events += [ordered]@{
      title    = $it.Subject
      start    = $it.Start.ToString("yyyy-MM-dd HH:mm")
      end      = $it.End.ToString("yyyy-MM-dd HH:mm")
      all_day  = [bool]$it.AllDayEvent
      location = $it.Location
    }
    if ($events.Count -ge 200) { break }
  }

  Out-Json ([ordered]@{ ok = $true; days = $Days; count = $events.Count; events = $events })
} catch {
  Out-Json @{ ok = $false; error = "read_failed"; detail = $_.Exception.Message }
  exit 1
}
