<#
  Whop-Clips holen: kopiert die fertigen Clips aus dem Branch `videos` nach Videos\Whop-Campaign
  und lädt neues Rohmaterial aus Videos\Whop-Campaign\Material in das private Repo `Whop-Material` hoch.

  Einmal einrichten (legt den Aufgabenplaner-Task "Whop-Clips holen" an: bei Anmeldung + alle 30 Minuten):
      powershell -ExecutionPolicy Bypass -File whop-sync.ps1 -Install

  Danach läuft alles von selbst. Es wird nur dazukopiert, nie etwas gelöscht. Tage, die du im Ordner selbst
  gelöscht hast, kommen nicht zurück. Protokoll: %LOCALAPPDATA%\whop-sync\sync.log

  Material: Alles in Whop-Campaign\Material (bis 95 MB pro Datei, GitHub-Grenze) wird hochgeladen, in Paketen
  bis 400 MB. Was dort gelöscht wird, verschwindet auch im Repo. Git liest den Ordner nur, es ändert dort nie etwas.
  Größere Dateien werden übersprungen und im Protokoll vermerkt. Das Skript aktualisiert sich selbst aus dem Branch.
#>
param([switch]$Install)

$ErrorActionPreference = 'Stop'
$Repo   = 'https://github.com/moritzstiebellehner3-stack/Whopclips.git'
$Base   = Join-Path $env:LOCALAPPDATA 'whop-sync'
$Clone  = Join-Path $Base 'repo'
$SeenFile = Join-Path $Base 'seen.txt'
$Log    = Join-Path $Base 'sync.log'
$Target = Join-Path ([Environment]::GetFolderPath('MyVideos')) 'Whop-Campaign'
$Self   = Join-Path $Base 'whop-sync.ps1'
$TaskName = 'Whop-Clips holen'
$MaterialDir  = Join-Path $Target 'Material'
$MaterialRepo = 'https://github.com/moritzstiebellehner3-stack/Whop-Material.git'
$MaterialGit  = Join-Path $Base 'material.git'   # nur die Git-Daten; die Dateien bleiben in Material\
$OldCopy      = Join-Path $Base 'material'       # Kopie der Vorversion, wird entfernt
$Lock         = Join-Path $Base 'material.lock'
$MaxBytes  = 95MB
$PackBytes = 400MB
# im Hintergrund nie auf eine Anmeldung warten; beim Einrichten (-Install) darf sich das Login-Fenster öffnen
if (-not $Install) { $env:GIT_TERMINAL_PROMPT = '0'; $env:GCM_INTERACTIVE = 'never' }
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }  # Dateinamen mit Umlauten aus git richtig lesen

New-Item -ItemType Directory -Force -Path $Base, $Target, $MaterialDir | Out-Null

function Write-Log($msg) {
    Add-Content -Path $Log -Value ("{0:yyyy-MM-dd HH:mm:ss}  {1}" -f (Get-Date), $msg) -Encoding UTF8
}

function Write-Step($msg) {
    Write-Host $msg
    Write-Log $msg
}

function Invoke-Git {
    # Windows PowerShell 5.1 wertet git-Meldungen auf stderr sonst als Fehler und bricht ab
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $out = & git @args 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $old
    if ($code -ne 0) { throw "git $($args -join ' ') fehlgeschlagen ($code): $out" }
}

function Invoke-GitLive {
    # git mit sichtbarer Ausgabe (Anmeldung, Upload-Fortschritt); nur der Exit-Code zählt
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & git @args | Out-Host
    $code = $LASTEXITCODE
    $ErrorActionPreference = $old
    if ($code -ne 0) { throw "git $($args -join ' ') fehlgeschlagen ($code)" }
}

function Get-Git {
    # stdout von git als Text, ohne bei Exit-Code != 0 abzubrechen
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $out = & git @args 2>$null
    $ErrorActionPreference = $old
    return $out
}

function Show-Toast($text) {
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
            [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $nodes = $xml.GetElementsByTagName('text')
        $nodes.Item(0).AppendChild($xml.CreateTextNode('Whop-Clips')) | Out-Null
        $nodes.Item(1).AppendChild($xml.CreateTextNode($text)) | Out-Null
        $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show(
            [Windows.UI.Notifications.ToastNotification]::new($xml))
    } catch { Write-Log "Benachrichtigung ging nicht: $_" }
}

function Push-Material {
    # Git arbeitet direkt auf Material\ (core.worktree), liest dort aber nur: kein checkout, kein reset --hard, kein clean.
    if ((Test-Path $Lock) -and (((Get-Date) - (Get-Item $Lock).LastWriteTime).TotalHours -lt 3)) {
        Write-Log 'Material: Upload läuft schon in einem anderen Fenster, übersprungen'
        return 0
    }
    Set-Content -Path $Lock -Value (Get-Date)
    try {
        if (Test-Path $OldCopy) { Remove-Item $OldCopy -Recurse -Force; Write-Log 'alte Material-Kopie entfernt' }
        $g = "--git-dir=$MaterialGit"
        if (-not (Test-Path (Join-Path $MaterialGit 'HEAD'))) {
            Invoke-Git init --quiet --bare $MaterialGit
            Invoke-Git $g config core.bare false
            Invoke-Git $g config core.worktree ($MaterialDir -replace '\\', '/')
            Invoke-Git $g config core.autocrlf false
            Invoke-Git $g config core.quotepath false
            Invoke-Git $g config user.name whop-sync
            Invoke-Git $g config user.email whop-sync@users.noreply.github.com
            Invoke-Git $g symbolic-ref HEAD refs/heads/main
            Invoke-Git $g remote add origin $MaterialRepo
            Write-Step 'Verbinde mit GitHub (Whop-Material)...'
            try {  # gibt es schon Material im Repo (z. B. nach Neuinstallation), darauf aufbauen
                Invoke-GitLive $g fetch origin main
                Invoke-Git $g reset --quiet --soft FETCH_HEAD
            } catch { Write-Log 'Repo noch leer oder Abruf ging nicht' }
        }

        # Nicht hochladen: zu große Dateien, Systemdateien, halbfertige Downloads
        $exclude = @('desktop.ini', 'Thumbs.db', '*.tmp', '*.crdownload', '*.part', '~$*')
        foreach ($big in Get-ChildItem $MaterialDir -Recurse -File | Where-Object { $_.Length -gt $MaxBytes }) {
            $rel = $big.FullName.Substring($MaterialDir.Length).TrimStart('\') -replace '\\', '/'
            $exclude += '/' + ($rel -replace '([\[\]\*\?])', '\$1')
            Write-Step "Zu groß (über 95 MB), wird nicht hochgeladen: $rel"
        }
        New-Item -ItemType Directory -Force -Path (Join-Path $MaterialGit 'info') | Out-Null
        [IO.File]::WriteAllText((Join-Path $MaterialGit 'info\exclude'), (($exclude -join "`n") + "`n"),
            (New-Object Text.UTF8Encoding $false))

        # Lokale Commits, die nie oben angekommen sind (z. B. abgebrochener Upload): zurücknehmen, Dateien bleiben
        $local = Get-Git $g rev-parse --verify -q HEAD
        $remote = Get-Git $g rev-parse --verify -q refs/remotes/origin/main
        if ($local -and ($local -ne $remote)) {
            if ($remote) { Invoke-Git $g reset --quiet --mixed $remote }
            else {
                Invoke-Git $g update-ref -d refs/heads/main
                Invoke-Git $g rm -r -q --cached --ignore-unmatch .
            }
            Write-Log 'nicht hochgeladene Commits zurückgenommen, werden in Paketen neu hochgeladen'
        }
        # Reste eines abgebrochenen Laufs aus dem Index nehmen, damit jeder Commit genau ein Paket enthält
        if (Get-Git $g rev-parse --verify -q HEAD) { Invoke-Git $g reset --quiet --mixed }
        else { Invoke-Git $g rm -r -q --cached --ignore-unmatch . }

        Write-Step 'Prüfe Material-Ordner...'
        $raw = (Get-Git $g status --porcelain -z -uall) -join "`n"
        $items = @()
        foreach ($entry in ($raw -split "`0" | Where-Object { $_.Length -gt 3 })) {
            $path = $entry.Substring(3)
            $full = Join-Path $MaterialDir ($path -replace '/', '\')
            $size = 0
            if (Test-Path -LiteralPath $full) { $size = (Get-Item -LiteralPath $full -Force).Length }
            $items += [pscustomobject]@{ Path = $path; Size = $size }
        }
        if ($items.Count -eq 0) { Write-Step 'Material: nichts Neues'; return 0 }

        $packs = @(); $cur = @(); $sum = 0
        foreach ($it in $items) {
            if ($cur.Count -gt 0 -and ($sum + $it.Size) -gt $PackBytes) { $packs += , $cur; $cur = @(); $sum = 0 }
            $cur += $it.Path; $sum += $it.Size
        }
        if ($cur.Count -gt 0) { $packs += , $cur }
        $mb = [Math]::Round((($items | Measure-Object Size -Sum).Sum) / 1MB)
        Write-Step "Material: $($items.Count) Dateien, $mb MB, in $($packs.Count) Paket(en)"

        $list = Join-Path $Base 'material-pack.txt'
        $push = @('push', '-u', 'origin', 'main')
        if ($Install) { $push += '--progress' } else { $push += '--quiet' }
        for ($i = 0; $i -lt $packs.Count; $i++) {
            $n = "$($i + 1)/$($packs.Count)"
            [IO.File]::WriteAllText($list, (($packs[$i] -join "`0") + "`0"), (New-Object Text.UTF8Encoding $false))
            Invoke-Git --literal-pathspecs $g add "--pathspec-from-file=$list" --pathspec-file-nul
            Invoke-Git $g commit --quiet -m ("Material {0:yyyy-MM-dd HH:mm}, Paket $n" -f (Get-Date))
            Write-Step "Lade Paket $n hoch..."
            Invoke-GitLive $g @push
            Write-Step "Paket $n hochgeladen"
        }
        return $items.Count
    } finally {
        Remove-Item $Lock -Force -ErrorAction SilentlyContinue
    }
}

if ($Install) {
    if ($PSCommandPath -and ($PSCommandPath -ne $Self)) { Copy-Item $PSCommandPath $Self -Force }
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' `
        -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Self`""
    $every = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 30)
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Hours 3)
    $desc = 'Holt fertige Whop-Clips aus GitHub (Branch videos) nach Videos\Whop-Campaign und lädt Material hoch.'
    try {
        $logon = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($logon, $every) -Settings $settings `
            -Description $desc -Force | Out-Null
    } catch {
        # Ohne Adminrechte kann der Anmelde-Auslöser scheitern; dann reicht "alle 30 Minuten"
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $every -Settings $settings `
            -Description $desc -Force | Out-Null
    }
    Write-Host "Eingerichtet: Aufgabe '$TaskName'. Clips landen in $Target"
    Write-Log 'Aufgabe eingerichtet'
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Log 'git nicht gefunden - bitte Git for Windows installieren'
    throw 'git nicht gefunden'
}

try {
    Write-Step 'Hole fertige Clips (beim ersten Mal kann das ein paar Minuten dauern)...'
    if (-not (Test-Path (Join-Path $Clone '.git'))) {
        Invoke-Git clone --quiet --depth 1 --branch videos --single-branch $Repo $Clone
    } else {
        Invoke-Git -C $Clone fetch --quiet --depth 1 origin videos
        Invoke-Git -C $Clone reset --quiet --hard FETCH_HEAD
    }

    $seen = @()
    if (Test-Path $SeenFile) { $seen = @(Get-Content $SeenFile) }
    $today = Get-Date
    $new = 0
    foreach ($day in Get-ChildItem $Clone -Directory | Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' }) {
        # Neue Tage komplett holen; heute und gestern zusätzlich nachziehen (falls ein Clip neu gerendert wurde)
        $recent = ($today - [datetime]::ParseExact($day.Name, 'yyyy-MM-dd', $null)).TotalDays -lt 2
        if (($seen -contains $day.Name) -and -not $recent) { continue }
        if (($seen -contains $day.Name) -and -not (Test-Path (Join-Path $Target $day.Name))) { continue }
        $dest = Join-Path $Target $day.Name
        $before = @(Get-ChildItem $dest -Recurse -File -Filter *.mp4 -ErrorAction SilentlyContinue).Count
        & robocopy $day.FullName $dest /E /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy Fehler $LASTEXITCODE" }
        $after = @(Get-ChildItem $dest -Recurse -File -Filter *.mp4).Count
        $new += [Math]::Max(0, $after - $before)
        if ($seen -notcontains $day.Name) { Add-Content -Path $SeenFile -Value $day.Name }
    }
    Write-Step "Clips: $new neue"
    if ($new -gt 0) { Show-Toast "$new neue Clips in Videos\Whop-Campaign" }

    # Selbst-Update: neue Version des Skripts liegt im Branch videos, gilt ab dem nächsten Lauf
    $fresh = Join-Path $Clone 'whop-sync.ps1'
    if ((Test-Path $fresh) -and (Test-Path $Self) -and ((Get-FileHash $fresh).Hash -ne (Get-FileHash $Self).Hash)) {
        Copy-Item $fresh $Self -Force
        Write-Log 'Skript aktualisiert'
    }
} catch {
    Write-Log "Fehler: $_"
    $failed = $true
}

try {
    $up = Push-Material
    if ($up -gt 0) {
        Write-Log "Material hochgeladen ($up neue oder geaenderte Dateien)"
        Show-Toast "Material hochgeladen ($up neue oder geaenderte Dateien)"
    }
} catch {
    Write-Log "Material-Upload fehlgeschlagen: $_"
}
if ($Install) { Write-Host 'Fertig. Du kannst das Fenster schliessen.' }
if ($failed) { exit 1 }
