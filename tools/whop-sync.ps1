<#
  Whop-Clips holen: kopiert die fertigen Clips aus dem Branch `videos` nach Videos\Whop-Campaign
  und lädt neues Rohmaterial aus Videos\Whop-Campaign\Material in das private Repo `Whop-Material` hoch.

  Einmal einrichten (legt den Aufgabenplaner-Task "Whop-Clips holen" an: bei Anmeldung + alle 30 Minuten):
      powershell -ExecutionPolicy Bypass -File whop-sync.ps1 -Install

  Danach läuft alles von selbst. Es wird nur dazukopiert, nie etwas gelöscht. Tage, die du im Ordner selbst
  gelöscht hast, kommen nicht zurück. Protokoll: %LOCALAPPDATA%\whop-sync\sync.log

  Material: Alles in Whop-Campaign\Material (bis 95 MB pro Datei, GitHub-Grenze) wird gespiegelt hochgeladen.
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
$MaterialClone = Join-Path $Base 'material'
$MaxBytes = 95MB
# im Hintergrund nie auf eine Anmeldung warten; beim Einrichten (-Install) darf sich das Login-Fenster öffnen
if (-not $Install) { $env:GIT_TERMINAL_PROMPT = '0' }

New-Item -ItemType Directory -Force -Path $Base, $Target, $MaterialDir | Out-Null

function Write-Log($msg) {
    Add-Content -Path $Log -Value ("{0:yyyy-MM-dd HH:mm:ss}  {1}" -f (Get-Date), $msg) -Encoding UTF8
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
    # Spiegelt Material\ in ein lokales Git-Repo und pusht nur, wenn sich etwas geändert hat
    if (-not (Test-Path (Join-Path $MaterialClone '.git'))) {
        New-Item -ItemType Directory -Force -Path $MaterialClone | Out-Null
        Invoke-Git -C $MaterialClone init --quiet
        Invoke-Git -C $MaterialClone config core.autocrlf false
        Invoke-Git -C $MaterialClone config core.quotepath false
        Invoke-Git -C $MaterialClone config user.name whop-sync
        Invoke-Git -C $MaterialClone config user.email whop-sync@users.noreply.github.com
        Invoke-Git -C $MaterialClone remote add origin $MaterialRepo
        Invoke-Git -C $MaterialClone checkout --quiet -b main
        try {  # gibt es schon Material im Repo (z. B. nach Neuinstallation), darauf aufbauen
            Invoke-Git -C $MaterialClone fetch --quiet origin main
            Invoke-Git -C $MaterialClone reset --quiet --soft FETCH_HEAD
        } catch { }
    }
    foreach ($big in Get-ChildItem $MaterialDir -Recurse -File | Where-Object { $_.Length -gt $MaxBytes }) {
        Write-Log "Material zu groß (über 95 MB), nicht hochgeladen: $($big.Name)"
    }
    & robocopy $MaterialDir $MaterialClone /MIR /MAX:$MaxBytes /XD .git /XF desktop.ini Thumbs.db '*.tmp' /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy Fehler $LASTEXITCODE" }
    $changes = @(& git -C $MaterialClone status --porcelain)
    if ($changes.Count -eq 0) { return 0 }
    Invoke-Git -C $MaterialClone add -A
    Invoke-Git -C $MaterialClone commit --quiet -m ("Material {0:yyyy-MM-dd HH:mm}" -f (Get-Date))
    Invoke-Git -C $MaterialClone push --quiet -u origin main
    return $changes.Count
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
    Write-Log "fertig, $new neue Clips"
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
if ($failed) { exit 1 }
