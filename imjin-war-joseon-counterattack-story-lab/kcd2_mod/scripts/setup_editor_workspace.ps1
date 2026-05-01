param(
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2",
  [string]$ModToolsRoot = "C:\Program Files (x86)\Steam\steamapps\common\KCD2Mod",
  [ValidateSet("HardLink", "Copy")]
  [string]$Mode = "HardLink",
  [switch]$Force
)

$ErrorActionPreference = "Stop"

function Get-FullPath {
  param([string]$Path)
  return [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Assert-Directory {
  param([string]$Path, [string]$Name)
  if (!(Test-Path -LiteralPath $Path -PathType Container)) {
    throw "$Name was not found: $Path"
  }
}

function Assert-ChildPath {
  param([string]$Root, [string]$Child)
  $rootFull = Get-FullPath $Root
  $childFull = Get-FullPath $Child
  if (!$childFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to write outside target root. Root=$rootFull Child=$childFull"
  }
}

Assert-Directory -Path $GameRoot -Name "KCD2 game folder"
Assert-Directory -Path $ModToolsRoot -Name "KCD2 modding tools folder"

$sourceRoots = @("Data", "Localization")
$created = 0
$skipped = 0
$replaced = 0
$failed = @()

foreach ($sourceRootName in $sourceRoots) {
  $sourceRoot = Join-Path $GameRoot $sourceRootName
  if (!(Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    continue
  }

  Get-ChildItem -Recurse -File -LiteralPath $sourceRoot -Filter "*.pak" | ForEach-Object {
    $sourceFile = $_.FullName
    $relativePath = $sourceFile.Substring((Get-FullPath $GameRoot).Length).TrimStart('\')
    $destination = Join-Path $ModToolsRoot $relativePath
    Assert-ChildPath -Root $ModToolsRoot -Child $destination

    $destinationDirectory = Split-Path -Parent $destination
    if (!(Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
      New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    }

    if (Test-Path -LiteralPath $destination) {
      if (!$Force) {
        $skipped += 1
        return
      }
      Remove-Item -LiteralPath $destination -Force
      $replaced += 1
    }

    try {
      if ($Mode -eq "HardLink") {
        New-Item -ItemType HardLink -Path $destination -Target $sourceFile | Out-Null
      } else {
        Copy-Item -LiteralPath $sourceFile -Destination $destination -Force
      }
      $created += 1
    } catch {
      $failed += [pscustomobject]@{
        source = $sourceFile
        destination = $destination
        error = $_.Exception.Message
      }
    }
  }
}

$required = @(
  "Data\Tables.pak",
  "Data\Scripts.pak",
  "Localization\Korean_xml.pak"
)

$missingRequired = @()
foreach ($relativePath in $required) {
  $path = Join-Path $ModToolsRoot $relativePath
  if (!(Test-Path -LiteralPath $path -PathType Leaf)) {
    $missingRequired += $relativePath
  }
}

if ($failed.Count -gt 0 -or $missingRequired.Count -gt 0) {
  $result = [pscustomobject]@{
    status = "failed"
    gameRoot = $GameRoot
    modToolsRoot = $ModToolsRoot
    mode = $Mode
    created = $created
    skipped = $skipped
    replaced = $replaced
    failed = $failed
    missingRequired = $missingRequired
  }
  $result | ConvertTo-Json -Depth 6
  throw "Editor workspace setup did not complete."
}

[pscustomobject]@{
  status = "ok"
  gameRoot = $GameRoot
  modToolsRoot = $ModToolsRoot
  mode = $Mode
  created = $created
  skipped = $skipped
  replaced = $replaced
  required = $required
  note = "Original game files were not modified. Missing editor PAKs were linked or copied into the official KCD2Mod tool workspace."
} | ConvertTo-Json -Depth 5
