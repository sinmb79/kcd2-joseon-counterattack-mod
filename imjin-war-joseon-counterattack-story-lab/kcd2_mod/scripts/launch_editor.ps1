param(
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2",
  [string]$ModToolsRoot = "C:\Program Files (x86)\Steam\steamapps\common\KCD2Mod",
  [switch]$SkipWorkspaceSetup,
  [int]$ReadyTimeoutSeconds = 90
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $PSCommandPath
$editor = Join-Path $ModToolsRoot "Bin\Win64ReleaseSteamLTO_DLL\Editor.exe"

if (!(Test-Path -LiteralPath $editor -PathType Leaf)) {
  throw "KCD2 Editor.exe was not found: $editor"
}

if (!$SkipWorkspaceSetup) {
  & (Join-Path $scriptRoot "setup_editor_workspace.ps1") -GameRoot $GameRoot -ModToolsRoot $ModToolsRoot | Out-Host
}

$existing = Get-Process -Name Editor -ErrorAction SilentlyContinue | Where-Object {
  try { $_.Path -ieq $editor } catch { $false }
} | Select-Object -First 1

if ($null -eq $existing) {
  Start-Process -FilePath $editor -WorkingDirectory $ModToolsRoot
} else {
  Write-Host "Editor is already running: PID $($existing.Id)"
}

$deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
$last = $null
do {
  Start-Sleep -Seconds 3
  $last = Get-Process -Name Editor -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -ne $last -and $last.MainWindowTitle -match "WARHORSE Sandbox") {
    break
  }
} while ((Get-Date) -lt $deadline)

[pscustomobject]@{
  status = if ($null -ne $last -and $last.MainWindowTitle -match "WARHORSE Sandbox") { "ready" } else { "started" }
  pid = if ($last) { $last.Id } else { $null }
  title = if ($last) { $last.MainWindowTitle } else { $null }
  responding = if ($last) { $last.Responding } else { $null }
  editor = $editor
  modToolsRoot = $ModToolsRoot
} | ConvertTo-Json -Depth 4
