param(
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2",
  [string]$PythonPackageRoot = "C:\Users\sinmb\workspace\tools\python-packages\unitypy"
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ScriptRoot
$RepoRoot = Split-Path -Parent $ProjectRoot
$VisualScript = Join-Path $RepoRoot "tools\kcd2_visual_asset_pack.py"
$PrivateRoot = Join-Path $RepoRoot "assets\game-captures-private\imjinwar_extract"
$VisualOutput = Join-Path $RepoRoot "assets\game-captures-private\kcd2_visual_pack"
$ModRoot = Join-Path (Join-Path $GameRoot "Mods") "joseon_counterattack_early"

if (!(Test-Path -LiteralPath $ModRoot -PathType Container)) {
  throw "KCD2 Joseon mod folder was not found. Run build_and_install.ps1 first: $ModRoot"
}

if (!(Test-Path -LiteralPath (Join-Path $PrivateRoot "textures") -PathType Container)) {
  throw "Extracted ImjinWar textures were not found. Run build_private_imjinwar_bridge.ps1 first: $PrivateRoot"
}

if (!(Test-Path -LiteralPath $VisualScript -PathType Leaf)) {
  throw "Visual asset pack script was not found: $VisualScript"
}

if (!(Test-Path -LiteralPath (Join-Path $PythonPackageRoot "PIL") -PathType Container)) {
  New-Item -ItemType Directory -Path $PythonPackageRoot -Force | Out-Null
  python -m pip install --upgrade --target $PythonPackageRoot Pillow
}

$env:PYTHONPATH = $PythonPackageRoot

python $VisualScript `
  --private-root $PrivateRoot `
  --kcd2-mod-root $ModRoot `
  --output $VisualOutput

$pakPath = Join-Path (Join-Path $ModRoot "Data") "joseon_counterattack_private_ui.pak"
if (!(Test-Path -LiteralPath $pakPath -PathType Leaf)) {
  throw "Joseon visual private pak was not generated: $pakPath"
}

[pscustomobject]@{
  status = "ok"
  privateRoot = $PrivateRoot
  visualOutput = $VisualOutput
  privatePak = $pakPath
  note = "Generated visual assets are local-only and ignored by git."
} | ConvertTo-Json -Depth 4
