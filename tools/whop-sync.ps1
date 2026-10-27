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
$ChunkBytes = 90MB                                 # große Videos gehen in Teilen zu 90 MB hoch
$BigDone = Join-Path $Base 'big-done.txt'
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

function Push-BigFiles($g, $bigs, $push) {
    # Videos über 95 MB (GitHub-Grenze 100 MB pro Datei) als Teile zu 90 MB: jeder Teil wird direkt in die
    # Git-Datenbank geschrieben (_teile/<Name>.part001 ...), im Material-Ordner selbst entsteht nichts.
    $done = @()
    if (Test-Path $BigDone) { $done = @(Get-Content $BigDone -Encoding UTF8) }
    $current = @{}
    foreach ($f in $bigs) { $current[($f.FullName.Substring($MaterialDir.Length).TrimStart('\') -replace '\\', '/')] = $f }

    # Teile von Videos, die Moritz gelöscht hat, wieder entfernen
    $gone = 0
    foreach ($part in @((Get-Git $g ls-files -z -- _teile) -join "`n" -split "`0" | Where-Object { $_ })) {
        $rel = $part.Substring(7) -replace '\.part\d{3}$', ''
        if (-not $current.ContainsKey($rel)) { Invoke-Git $g update-index --force-remove -- $part; $gone++ }
    }
    if ($gone -gt 0) {
        Invoke-Git $g commit --quiet -m 'Material: Teile gelöschter Videos entfernt'
        Invoke-GitLive $g @push
        $done = @($done | Where-Object { $current.ContainsKey(($_ -split '\|')[0]) })
        Set-Content -Path $BigDone -Value $done -Encoding UTF8
    }

    $tmp = Join-Path $Base 'teil.tmp'
    $count = 0
    foreach ($rel in $current.Keys) {
        $f = $current[$rel]
        $key = "$rel|$($f.Length)|$($f.LastWriteTimeUtc.Ticks)"
        if ($done -contains $key) { continue }
        $n = [int][Math]::Ceiling($f.Length / $ChunkBytes)
        Write-Step "Großes Video in $n Teilen: $rel"
        foreach ($old in @((Get-Git $g ls-files -z -- _teile) -join "`n" -split "`0" | Where-Object { $_ -and $_.StartsWith("_teile/$rel.part") })) {
            Invoke-Git $g update-index --force-remove -- $old   # ältere Version derselben Datei
        }
        $in = [IO.File]::OpenRead($f.FullName)
        try {
            $buf = New-Object byte[] $ChunkBytes
            for ($i = 1; $i -le $n; $i++) {
                $read = 0
                while ($read -lt $ChunkBytes) {
                    $r = $in.Read($buf, $read, $ChunkBytes - $read)
                    if ($r -le 0) { break }
                    $read += $r
                }
                $out = [IO.File]::Create($tmp)
                $out.Write($buf, 0, $read)
                $out.Close()
                $sha = @(Get-Git $g hash-object -w --no-filters -- $tmp)[0]
                if (-not $sha) { throw "Teil $i von $rel konnte nicht gespeichert werden" }
                Invoke-Git $g update-index --add --cacheinfo 100644 $sha ('_teile/{0}.part{1:D3}' -f $rel, $i)
                if (($i % 4 -eq 0) -or ($i -eq $n)) {
                    Invoke-Git $g commit --quiet -m "Material: $rel, Teil $i/$n"
                    Write-Step "Lade Teil $i/$n hoch..."
                    Invoke-GitLive $g @push
                }
            }
        } finally {
            $in.Close()
            Remove-Item $tmp -Force -ErrorAction SilentlyContinue
        }
        Add-Content -Path $BigDone -Value $key -Encoding UTF8
        Write-Step "Fertig hochgeladen: $rel"
        $count++
    }
    return $count
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
        $bigs = @(Get-ChildItem $MaterialDir -Recurse -File | Where-Object { $_.Length -gt $MaxBytes })
        foreach ($big in $bigs) {
            $rel = $big.FullName.Substring($MaterialDir.Length).TrimStart('\') -replace '\\', '/'
            $exclude += '/' + ($rel -replace '([\[\]\*\?])', '\$1')
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
            if ($path.StartsWith('_teile/')) { continue }  # Teile großer Videos laufen über Push-BigFiles
            $full = Join-Path $MaterialDir ($path -replace '/', '\')
            $size = 0
            if (Test-Path -LiteralPath $full) { $size = (Get-Item -LiteralPath $full -Force).Length }
            $items += [pscustomobject]@{ Path = $path; Size = $size }
        }
        $push = @('push', '-u', 'origin', 'main')
        if ($Install) { $push += '--progress' } else { $push += '--quiet' }
        if ($items.Count -eq 0) {
            Write-Step 'Material: keine neuen kleinen Dateien'
            return (Push-BigFiles $g $bigs $push)
        }

        $packs = @(); $cur = @(); $sum = 0
        foreach ($it in $items) {
            if ($cur.Count -gt 0 -and ($sum + $it.Size) -gt $PackBytes) { $packs += , $cur; $cur = @(); $sum = 0 }
            $cur += $it.Path; $sum += $it.Size
        }
        if ($cur.Count -gt 0) { $packs += , $cur }
        $mb = [Math]::Round((($items | Measure-Object Size -Sum).Sum) / 1MB)
        Write-Step "Material: $($items.Count) Dateien, $mb MB, in $($packs.Count) Paket(en)"

        $list = Join-Path $Base 'material-pack.txt'
        for ($i = 0; $i -lt $packs.Count; $i++) {
            $n = "$($i + 1)/$($packs.Count)"
            [IO.File]::WriteAllText($list, (($packs[$i] -join "`0") + "`0"), (New-Object Text.UTF8Encoding $false))
            Invoke-Git --literal-pathspecs $g add "--pathspec-from-file=$list" --pathspec-file-nul
            Invoke-Git $g commit --quiet -m ("Material {0:yyyy-MM-dd HH:mm}, Paket $n" -f (Get-Date))
            Write-Step "Lade Paket $n hoch..."
            Invoke-GitLive $g @push
            Write-Step "Paket $n hochgeladen"
        }
        return $items.Count + (Push-BigFiles $g $bigs $push)
    } finally {
        Remove-Item $Lock -Force -ErrorAction SilentlyContinue
    }
}

function Register-SyncTask {
    # conhost --headless: kein Konsolenfenster (powershell -WindowStyle Hidden blitzt trotzdem kurz auf)
    $action = New-ScheduledTaskAction -Execute 'conhost.exe' `
        -Argument "--headless powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$Self`""
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
}

if ($Install) {
    if ($PSCommandPath -and ($PSCommandPath -ne $Self)) { Copy-Item $PSCommandPath $Self -Force }
    Register-SyncTask
    Write-Host "Eingerichtet: Aufgabe '$TaskName'. Clips landen in $Target"
    Write-Log 'Aufgabe eingerichtet'
} else {
    # Alte Einrichtung (powershell.exe direkt, Fenster blitzt auf) einmalig auf die fensterlose Variante umstellen
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        if ($task.Actions[0].Execute -ne 'conhost.exe') { Register-SyncTask; Write-Log 'Aufgabe auf fensterlosen Start umgestellt' }
    } catch { Write-Log "Aufgabe konnte nicht umgestellt werden: $_" }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Log 'git nicht gefunden - bitte Git for Windows installieren'
    throw 'git nicht gefunden'
}

try {
    Write-Step 'Hole fertige Clips (beim ersten Mal kann das ein paar Minuten dauern)...'
    try {
        if (-not (Test-Path (Join-Path $Clone '.git'))) {
            Invoke-Git clone --quiet --depth 1 --branch videos --single-branch $Repo $Clone
        } else {
            Invoke-Git -C $Clone fetch --quiet --depth 1 origin videos
            Invoke-Git -C $Clone reset --quiet --hard FETCH_HEAD
        }
    } catch {
        # repo\ ist nur ein Zwischenspeicher: bei Problemen löschen und frisch holen
        Write-Step "Zwischenspeicher wird neu angelegt ($_)"
        if (Test-Path $Clone) { Remove-Item $Clone -Recurse -Force }
        Invoke-Git clone --quiet --depth 1 --branch videos --single-branch $Repo $Clone
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
        & robocopy $day.FullName $dest /E /R:2 /W:5 /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) {
            Write-Step "Konnte $($day.Name) nicht ganz kopieren (robocopy $LASTEXITCODE, ist ein Video gerade offen?)"
            continue
        }
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
    Write-Step "Fehler beim Clips holen: $_"
    $failed = $true
}

try {
    $up = Push-Material
    if ($up -gt 0) {
        Write-Log "Material hochgeladen ($up neue oder geaenderte Dateien)"
        Show-Toast "Material hochgeladen ($up neue oder geaenderte Dateien)"
    }
} catch {
    Write-Step "Material-Upload fehlgeschlagen: $_"
}
if ($Install) { Write-Host 'Fertig. Du kannst das Fenster schliessen.' }
if ($failed) { exit 1 }
