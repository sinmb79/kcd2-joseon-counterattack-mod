param(
  [string]$ImjinWarRoot = "C:\Program Files (x86)\Joycity\ImjinWar",
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2",
  [string]$PythonPackageRoot = "C:\Users\sinmb\workspace\tools\python-packages\unitypy",
  [ValidateSet("safe", "full")]
  [string]$VisualProfile = "safe"
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ScriptRoot
$RepoRoot = Split-Path -Parent $ProjectRoot
$BridgeScript = Join-Path $RepoRoot "tools\imjinwar_asset_bridge.py"
$VisualPackScript = Join-Path $ScriptRoot "build_visual_asset_pack.ps1"
$PrivateOutput = Join-Path $RepoRoot "assets\game-captures-private\imjinwar_extract"
$ModRoot = Join-Path (Join-Path $GameRoot "Mods") "joseon_counterattack_early"

if (!(Test-Path -LiteralPath $ImjinWarRoot -PathType Container)) {
  throw "ImjinWar install folder was not found: $ImjinWarRoot"
}

if (!(Test-Path -LiteralPath $ModRoot -PathType Container)) {
  throw "KCD2 Joseon mod folder was not found. Run build_and_install.ps1 first: $ModRoot"
}

if (!(Test-Path -LiteralPath $BridgeScript -PathType Leaf)) {
  throw "Bridge script was not found: $BridgeScript"
}

if (!(Test-Path -LiteralPath (Join-Path $PythonPackageRoot "UnityPy") -PathType Container)) {
  New-Item -ItemType Directory -Path $PythonPackageRoot -Force | Out-Null
  python -m pip install --upgrade --target $PythonPackageRoot UnityPy Pillow
}

$env:PYTHONPATH = $PythonPackageRoot

python $BridgeScript `
  --source $ImjinWarRoot `
  --output $PrivateOutput `
  --kcd2-mod-root $ModRoot `
  --build-ui-pak

if (Test-Path -LiteralPath $VisualPackScript -PathType Leaf) {
  & $VisualPackScript -GameRoot $GameRoot -PythonPackageRoot $PythonPackageRoot -Profile $VisualProfile | Out-Null
}

$pakPath = Join-Path (Join-Path $ModRoot "Data") "joseon_counterattack_private_ui.pak"
if (!(Test-Path -LiteralPath $pakPath -PathType Leaf)) {
  throw "Private KCD2 UI bridge pak was not generated: $pakPath"
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($pakPath)
try {
  $entryCount = @($zip.Entries).Count
} finally {
  $zip.Dispose()
}

[pscustomobject]@{
  status = "ok"
  imjinWarRoot = $ImjinWarRoot
  privateOutput = $PrivateOutput
  privatePak = $pakPath
  privatePakEntries = $entryCount
  visualProfile = $VisualProfile
  note = "Private extracted assets are local-only and ignored by git."
} | ConvertTo-Json -Depth 4
