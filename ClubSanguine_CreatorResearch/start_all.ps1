# start_all.ps1 - Club Sanguine Outreach Desk launcher + terminal picker
#
#   Right-click > Run with PowerShell, or:  powershell -ExecutionPolicy Bypass -File .\start_all.ps1
#
# Starts the local outreach server (tools/outreach_app.py, 127.0.0.1 only), then lets you pick
# who to message from the terminal: browse creators / journalists / outlets, see their info,
# press M to jump straight to where you can message them, and log what you did.
# Nothing is ever sent automatically - you write and send every message yourself.
# Pure ASCII on purpose so it renders in any Windows console.

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot
$Base = 'http://127.0.0.1:8765'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
try { $Host.UI.RawUI.WindowTitle = 'Club Sanguine - Outreach Desk' } catch { }

# ----------------------------------------------------------------------------- art

$BannerArt = @'
   ____ _     _   _ ____    ____    _    _   _  ____ _   _ ___ _   _ _____
  / ___| |   | | | | __ )  / ___|  / \  | \ | |/ ___| | | |_ _| \ | | ____|
 | |   | |   | | | |  _ \  \___ \ / _ \ |  \| | |  _| | | || ||  \| |  _|
 | |___| |___| |_| | |_) |  ___) / ___ \| |\  | |_| | |_| || || |\  | |___
  \____|_____|\___/|____/  |____/_/   \_\_| \_|\____|\___/|___|_| \_|_____|
'@

$DoorArt = @'
            .-----------------.          "Name's not on the list...
            |  .-----------.  |           ...but it could be."
            |  |  O U T    |  |
            |  |  R E A C H|  |       ==================================
            |  |   D E S K |  |        creators * journalists * outlets
            |  '-----------'  |       ==================================
            |   []  (o)  []   |
      ______|_________________|______
'@

$Art = @{
  creator    = @'
      .--------------------.
      |  [>]  STREAMERS    |    ( o_o )  "is this one human?"
      '--------------------'    /|   |\
'@
  journalist = @'
      .--------------------.
      |  [#]  JOURNALISTS  |    ( -_- )  "got a press kit?"
      '--------------------'    /| == |\
'@
  outlet     = @'
      .--------------------.
      |  [@]  OUTLETS      |    [=====]  "tips@ ... submit ..."
      '--------------------'    |_____|
'@
  any        = @'
      .--------------------.
      |  [*]  THE LIST     |    ( 0_0 )  "who's next at the door?"
      '--------------------'    /|   |\
'@
}

function Write-Banner {
  Clear-Host
  Write-Host $BannerArt -ForegroundColor DarkRed
  Write-Host $DoorArt -ForegroundColor DarkGray
}

function Write-Rule([string]$Char = '-', [ConsoleColor]$Color = 'DarkGray') {
  $w = 100
  try { $w = [Math]::Min($Host.UI.RawUI.WindowSize.Width - 1, 110) } catch { }
  Write-Host ($Char * $w) -ForegroundColor $Color
}

function Cut([string]$s, [int]$n) {
  if ($null -eq $s) { return '' }
  if ($s.Length -le $n) { return $s }
  return $s.Substring(0, $n - 2) + '..'
}

function Fmt-Subs($n) {
  if ($null -eq $n) { return '-' }
  if ($n -ge 1000000) { return ('{0:N1}M' -f ($n / 1000000)) }
  if ($n -ge 1000) { return ('{0:N0}K' -f ($n / 1000)) }
  return "$n"
}

$HowLabel = @{ email = 'EMAIL'; gated = 'GATED@'; discord = 'DISCORD'; form = 'FORM'; dm = 'DM'; web = 'WEB'; none = '-' }
$TierColor = @{ S = 'Magenta'; A = 'Yellow'; B = 'Cyan'; C = 'Gray'; 'Long Tail' = 'DarkGray' }

# ----------------------------------------------------------------------------- server

function Find-Python {
  $cands = @()
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -notlike '*WindowsApps*') { $cands += $cmd.Source }
  $cands += Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending | ForEach-Object { $_.FullName }
  $cmd = Get-Command py -ErrorAction SilentlyContinue
  if ($cmd) { $cands += $cmd.Source }
  foreach ($c in $cands) { if ($c -and (Test-Path $c)) { return $c } }
  return $null
}

function Test-Server {
  try { $null = Invoke-RestMethod "$Base/api/stats" -TimeoutSec 3; return $true } catch { return $false }
}

function Start-Desk {
  Write-Host '  [..] checking the door...' -ForegroundColor DarkGray
  $script:Py = Find-Python
  if (-not $script:Py) {
    Write-Host '  [!!] Python 3 not found. Install it:  winget install Python.Python.3.12' -ForegroundColor Red
    Read-Host '  Press Enter to exit'; exit 1
  }
  if (-not (Test-Path 'dashboard\dist\index.html')) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if ($npm) {
      Write-Host '  [..] building the dashboard (first run)...' -ForegroundColor DarkGray
      Push-Location dashboard; & npm install --no-fund --no-audit | Out-Null; & npm run build | Out-Null; Pop-Location
    } else {
      Write-Host '  [!!] dashboard\dist is missing and Node is not installed - the browser view will not load.' -ForegroundColor Yellow
    }
  }
  if (Test-Server) {
    Write-Host '  [ok] server already running at' $Base -ForegroundColor Green
    $script:StartedServer = $null
    return
  }
  $script:StartedServer = Start-Process -FilePath $script:Py -ArgumentList 'tools/outreach_app.py --no-browser' `
    -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 250
    if (Test-Server) { Write-Host '  [ok] server up at' $Base -ForegroundColor Green; return }
  }
  Write-Host '  [!!] server did not start. Try:  python tools/outreach_app.py' -ForegroundColor Red
  Read-Host '  Press Enter to exit'; exit 1
}

function Api-Get([string]$Path) { return Invoke-RestMethod "$Base$Path" -TimeoutSec 30 }

function Api-List([string]$Path) {
  # Windows PowerShell 5.1 returns a JSON array as ONE object; piping unrolls it into rows.
  $rows = @((Invoke-RestMethod "$Base$Path" -TimeoutSec 30) | ForEach-Object { $_ })
  return ,$rows
}

function Api-Log($c, [string]$Action, [string]$Channel = '', [string]$Template = '', [string]$Note = '') {
  $body = @{ entries = @(@{ contact_id = $c.id; kind = $c.kind; name = $c.name; action = $Action;
                            channel = $Channel; template = $Template; note = $Note }) } | ConvertTo-Json -Depth 5
  $bytes = [Text.Encoding]::UTF8.GetBytes($body)
  $null = Invoke-RestMethod "$Base/api/log" -Method Post -ContentType 'application/json; charset=utf-8' -Body $bytes
}

function Q([string]$s) { return [uri]::EscapeDataString($s) }

# ----------------------------------------------------------------------------- stats

function Show-Stats {
  $s = Api-Get '/api/stats'
  Write-Rule '='
  Write-Host ('  TODAY: {0} / {1} messaged      FOLLOW-UPS DUE: {2}' -f $s.messaged_today, $s.daily_target, $s.follow_ups_due) -ForegroundColor White
  $pct = 0
  if ($s.daily_target -gt 0) { $pct = [Math]::Min(1, $s.messaged_today / $s.daily_target) }
  $bar = ('#' * [int](40 * $pct)).PadRight(40, '.')
  Write-Host "  [$bar]" -ForegroundColor DarkRed
  foreach ($k in 'creator', 'journalist', 'outlet') {
    $row = $s.by_kind.$k
    if ($null -eq $row) { continue }
    $parts = $row.PSObject.Properties | Sort-Object Name | ForEach-Object { "$($_.Name) $($_.Value)" }
    Write-Host ('  {0,-11} {1,5} total   {2}' -f ($k + 's'), $s.totals.$k, ($parts -join ' | ')) -ForegroundColor Gray
  }
  Write-Rule '='
}

# ----------------------------------------------------------------------------- list

function Show-List([string]$Kind, [string]$Status = 'new') {
  $filter = @{ q = ''; tier = ''; email = '0'; status = $Status }
  if ($Status -eq 'new') {
    Write-Host ''
    Write-Host '  Filter (Enter = skip)' -ForegroundColor DarkGray
    $filter.q = Read-Host '    search name / game / outlet'
    $t = Read-Host '    tiers e.g. S,A  (blank = all)'
    $filter.tier = ($t.ToUpper() -replace '\s', '')
    $e = Read-Host '    only contacts with an email ready? (y/N)'
    if ($e -match '^[yY]') { $filter.email = '1' }
    $n = Read-Host '    include already-contacted? (y/N)'
    if ($n -match '^[yY]') { $filter.status = 'any' }
  }
  $rows = (Api-List ("/api/find?kind=$Kind&q=$(Q $filter.q)&tier=$(Q $filter.tier)&status=$($filter.status)&email=$($filter.email)&limit=500"))
  $page = 0; $size = 15
  while ($true) {
    Clear-Host
    $artKey = $Kind; if (-not $Art.ContainsKey($artKey)) { $artKey = 'any' }
    Write-Host $Art[$artKey] -ForegroundColor DarkRed
    $title = switch ($Status) { 'today' { "TODAY'S QUEUE" } 'due' { 'FOLLOW-UPS DUE' } default { 'NOT YET CONTACTED' } }
    if ($filter.status -eq 'any') { $title = 'EVERYONE' }
    Write-Host ("  $title  -  {0} match(es)" -f $rows.Count) -ForegroundColor White
    Write-Rule
    Write-Host ('  {0,-4} {1,-5} {2,-4} {3,-26} {4,-22} {5,-8} {6,-12}' -f '#', 'TIER', 'FIT', 'NAME', 'SIZE / OUTLET', 'REACH', 'STATUS') -ForegroundColor DarkGray
    Write-Rule
    if ($rows.Count -eq 0) { Write-Host '  (nobody at the door)' -ForegroundColor DarkGray }
    $from = $page * $size
    $to = [Math]::Min($rows.Count, $from + $size) - 1
    for ($i = $from; $i -le $to; $i++) {
      $r = $rows[$i]
      $size2 = if ($r.kind -eq 'creator') { (Fmt-Subs $r.subs) + ' subs' } elseif ($r.kind -eq 'journalist') { $r.outlet } else { $r.type }
      $star = if ($r.hp) { '*' } else { ' ' }
      $st = if ($r.status) { $r.status } else { 'new' }
      $color = $TierColor[$r.tier]; if (-not $color) { $color = 'Gray' }
      $line = '  {0,-4} {1,-5} {2,-4} {3,-26} {4,-22} {5,-8} {6,-12}' -f ($i + 1), $r.tier, [int]$r.score, (Cut ($star + $r.name) 26), (Cut $size2 22), $HowLabel[$r.how], $st
      Write-Host $line -ForegroundColor $color
    }
    Write-Rule
    $pages = [Math]::Max(1, [Math]::Ceiling($rows.Count / $size))
    Write-Host ("  page {0}/{1}   [number] open   [N]ext  [P]rev   [B]ack" -f ($page + 1), $pages) -ForegroundColor DarkGray
    $cmd = (Read-Host '  >').Trim()
    if ($cmd -match '^\d+$') {
      $idx = [int]$cmd - 1
      if ($idx -ge 0 -and $idx -lt $rows.Count) {
        $res = Show-Card $rows $idx
        if ($Status -ne 'new' -or $filter.status -ne 'any') {
          # refresh so people you just handled drop off the list
          $rows = (Api-List ("/api/find?kind=$Kind&q=$(Q $filter.q)&tier=$(Q $filter.tier)&status=$($filter.status)&email=$($filter.email)&limit=500"))
          if ($page * $size -ge $rows.Count) { $page = [Math]::Max(0, $page - 1) }
        }
        if ($res -eq 'back') { continue }
      }
    }
    elseif ($cmd -match '^[nN]$') { if (($page + 1) * $size -lt $rows.Count) { $page++ } }
    elseif ($cmd -match '^[pP]$') { if ($page -gt 0) { $page-- } }
    elseif ($cmd -match '^[bBqQ]$' -or $cmd -eq '') { return }
  }
}

# ----------------------------------------------------------------------------- card

function Open-Url([string]$Url) {
  if (-not $Url) { return }
  try { Start-Process $Url } catch { Write-Host "  could not open $Url" -ForegroundColor Red }
}

function Default-Channel($c) {
  switch ($c.message.how) {
    'email' { return 'email' } 'gated' { return 'email' } 'discord' { return 'discord' } 'form' { return 'form' }
    'dm' { if ($c.message.label -match 'Bluesky') { return 'bluesky' } elseif ($c.message.label -match ' X$') { return 'x' } else { return 'other' } }
    default { return 'other' }
  }
}

function Show-Card($rows, [int]$idx) {
  $tpl = ''
  while ($true) {
    $r = $rows[$idx]
    $c = Api-Get ("/api/contact?id=$(Q $r.id)&template=$(Q $tpl)")
    $tpl = $c.template
    Clear-Host
    $artKey = $c.kind; if (-not $Art.ContainsKey($artKey)) { $artKey = 'any' }
    Write-Host $Art[$artKey] -ForegroundColor DarkRed
    Write-Rule '='
    $color = $TierColor[$c.tier]; if (-not $color) { $color = 'Gray' }
    $hp = if ($c.hp) { '  * HIGH PRIORITY' } else { '' }
    Write-Host ("  {0}  [{1} | fit {2}]{3}" -f $c.name.ToUpper(), $c.tier, [int]$c.score, $hp) -ForegroundColor $color
    $st = if ($c.state.status) { "$($c.state.status) since $($c.state.since)" } else { 'not contacted yet' }
    if ($c.state.follow_up_on -and ($c.state.status -eq 'contacted' -or $c.state.status -eq 'followed_up')) { $st += "  (follow up $($c.state.follow_up_on))" }
    Write-Host "  $($c.id)  |  $st   ($($idx + 1) of $($rows.Count))" -ForegroundColor Gray
    Write-Rule '='
    if ($c.kind -eq 'creator') {
      Write-Host ('  size      {0} subscribers   twitch: {1}   country: {2}' -f (Fmt-Subs $c.subs), $(if ($c.twitch) { 'yes' } else { 'no' }), $(if ($c.country) { $c.country } else { '?' }))
      Write-Host ('  style     {0}   last active: {1}' -f $c.style, $c.last_active)
    } else {
      Write-Host ('  outlet    {0}' -f $(if ($c.kind -eq 'journalist') { $c.outlet } else { $c.type }))
      Write-Host ('  role      {0}   region: {1}   latest: {2}   Next Fest writer: {3}' -f $c.style, $c.country, $c.last_active, $c.nextfest)
    }
    if ($c.games.Count -gt 0) { Write-Host ('  games     {0}' -f (($c.games) -join ', ')) -ForegroundColor White }
    if ($c.email) { Write-Host ('  email     {0}' -f $c.email) -ForegroundColor Green }
    Write-Rule
    Write-Host '  >> MESSAGE THEM:' $c.message.label -ForegroundColor Green
    Write-Host '     socials & links:' -ForegroundColor DarkGray
    $links = @($c.links)
    for ($i = 0; $i -lt $links.Count; $i++) {
      $u = $links[$i][1]; if ($u -like 'mailto:*') { $u = $u.Substring(7) }
      Write-Host ('     [{0,2}] {1,-24} {2}' -f ($i + 1), (Cut $links[$i][0] 24), (Cut $u 70))
    }
    $ev = @($c.evidence)
    for ($i = 0; $i -lt $ev.Count; $i++) { Write-Host ('     [E{0}] evidence                 {1}' -f ($i + 1), (Cut $ev[$i] 70)) -ForegroundColor DarkGray }
    if ($c.notes) { Write-Host ('  notes     {0}' -f (Cut $c.notes 160)) -ForegroundColor DarkGray }
    if ($c.unfilled.Count -gt 0) { Write-Host ('  ! template placeholders still empty: {0} (set them in outreach\config.json)' -f ($c.unfilled -join ' ')) -ForegroundColor Yellow }
    Write-Rule
    Write-Host '  [M] MESSAGE THEM (opens the best route; message copied / pre-filled)   [1-n] open link   [E1-3] evidence' -ForegroundColor Green
    Write-Host ('  [V] view message  [C] copy message  [A] copy email  [T] switch template ({0})' -f $tpl) -ForegroundColor Gray
    Write-Host '  [L] log CONTACTED  [K] skip  [R] replied  [I] interested  [Y] key sent  [G] covered  [D] declined  [U] undo  [O] note' -ForegroundColor Gray
    Write-Host '  [N] next  [P] prev  [B] back to list' -ForegroundColor DarkGray
    $cmd = (Read-Host '  >').Trim()
    switch -Regex ($cmd) {
      '^[mM]$' {
        if ($c.message.how -eq 'email') {
          $addr = $c.message.url.Substring(7)
          $mailto = 'mailto:' + $addr + '?subject=' + (Q $c.subject) + '&body=' + (Q $c.body)
          Set-Clipboard -Value $c.body
          Open-Url $mailto
          Write-Host '  opened your mail app (message also on the clipboard). Press L once sent.' -ForegroundColor Green
        } else {
          Set-Clipboard -Value $c.body
          Open-Url $c.message.url
          if ($c.message.how -eq 'gated') {
            Write-Host '  opened their YouTube About page: press "View email address", then come back.' -ForegroundColor Green
            $em = Read-Host '  paste the revealed email to save it (Enter to skip)'
            if ($em -match '@') {
              $b = [Text.Encoding]::UTF8.GetBytes((@{ contact_id = $c.id; email = $em.Trim() } | ConvertTo-Json))
              $null = Invoke-RestMethod "$Base/api/reveal" -Method Post -ContentType 'application/json' -Body $b
              Write-Host '  saved. Press M again to open your mail app with the message.' -ForegroundColor Green
            }
          } else {
            Write-Host '  message copied to clipboard - paste it on the page that just opened. Press L once sent.' -ForegroundColor Green
          }
        }
        Read-Host '  (Enter)' | Out-Null
      }
      '^\d+$' { $i = [int]$cmd - 1; if ($i -ge 0 -and $i -lt $links.Count) { Open-Url $links[$i][1] } }
      '^[eE][1-3]$' { $i = [int]$cmd.Substring(1) - 1; if ($i -lt $ev.Count) { Open-Url $ev[$i] } }
      '^[vV]$' {
        Write-Rule; if ($c.subject) { Write-Host "  Subject: $($c.subject)" -ForegroundColor White; Write-Host '' }
        Write-Host $c.body; Write-Rule; Read-Host '  (Enter)' | Out-Null
      }
      '^[cC]$' { Set-Clipboard -Value $c.body; Write-Host '  message copied' -ForegroundColor Green; Start-Sleep -Milliseconds 700 }
      '^[aA]$' {
        $addr = $c.email
        if (-not $addr -and $c.message.how -eq 'email') { $addr = $c.message.url.Substring(7) }
        if ($addr) { Set-Clipboard -Value $addr; Write-Host "  copied $addr" -ForegroundColor Green } else { Write-Host '  no email on file' -ForegroundColor Yellow }
        Start-Sleep -Milliseconds 700
      }
      '^[tT]$' {
        $ts = @($c.templates)
        for ($i = 0; $i -lt $ts.Count; $i++) { Write-Host ('    [{0}] {1}' -f ($i + 1), $ts[$i]) }
        $pick = Read-Host '  template #'
        if ($pick -match '^\d+$' -and [int]$pick -ge 1 -and [int]$pick -le $ts.Count) { $tpl = $ts[[int]$pick - 1] }
      }
      '^[lL]$' {
        $def = Default-Channel $c
        $ch = Read-Host "  sent via? (email/discord/x/bluesky/twitch/youtube/form/other) [$def]"
        if (-not $ch) { $ch = $def }
        $note = Read-Host '  note (optional)'
        Api-Log $c 'contacted' $ch $tpl $note
        Write-Host '  logged as contacted - follow-up date set automatically.' -ForegroundColor Green
        Start-Sleep -Milliseconds 600
        if ($idx -lt $rows.Count - 1) { $idx++ }
      }
      '^[kK]$' { Api-Log $c 'skip'; if ($idx -lt $rows.Count - 1) { $idx++ } }
      '^[rR]$' { Api-Log $c 'replied' }
      '^[iI]$' { Api-Log $c 'interested' }
      '^[yY]$' { Api-Log $c 'key_sent' }
      '^[gG]$' { Api-Log $c 'covered' }
      '^[dD]$' { Api-Log $c 'declined' }
      '^[uU]$' { Api-Log $c 'undo' }
      '^[oO]$' { $note = Read-Host '  note'; if ($note) { Api-Log $c 'note' '' '' $note } }
      '^[nN]$' { if ($idx -lt $rows.Count - 1) { $idx++; $tpl = '' } }
      '^[pP]$' { if ($idx -gt 0) { $idx--; $tpl = '' } }
      '^([bB]|)$' { return 'back' }
    }
  }
}

# ----------------------------------------------------------------------------- main

Write-Banner
Start-Desk
Start-Sleep -Milliseconds 400

while ($true) {
  Write-Banner
  Show-Stats
  Write-Host ''
  Write-Host '   [D]  Open the dashboard in your browser' -ForegroundColor White
  Write-Host '   [C]  Creators / streamers        [J]  Journalists        [O]  Outlets' -ForegroundColor White
  Write-Host "   [T]  Today's queue               [F]  Follow-ups due      [A]  Search everyone" -ForegroundColor White
  Write-Host '   [Q]  Quit' -ForegroundColor DarkGray
  Write-Host ''
  $choice = (Read-Host '  who are we letting in tonight?').Trim().ToUpper()
  switch ($choice) {
    'D' { Open-Url "$Base/" }
    'C' { Show-List 'creator' }
    'J' { Show-List 'journalist' }
    'O' { Show-List 'outlet' }
    'T' { Show-List 'any' 'today' }
    'F' { Show-List 'any' 'due' }
    'A' { Show-List 'any' }
    'Q' {
      if ($script:StartedServer) {
        $stop = Read-Host '  stop the outreach server too? (Y/n)'
        if ($stop -notmatch '^[nN]') { Stop-Process -Id $script:StartedServer.Id -Force -ErrorAction SilentlyContinue }
      }
      Write-Host '  the door is closed. good night.' -ForegroundColor DarkRed
      exit 0
    }
  }
}
