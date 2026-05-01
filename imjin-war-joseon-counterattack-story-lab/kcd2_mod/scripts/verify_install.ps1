param(
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ModId = "joseon_counterattack_early"
$ModRoot = Join-Path (Join-Path $GameRoot "Mods") $ModId
$Manifest = Join-Path $ModRoot "mod.manifest"
$Localization = Join-Path $ModRoot "Localization"
$RequiredPaks = @("Korean_xml.pak", "English_xml.pak")
$Needles = @(
  "조선의 반격: 동래성의 새벽",
  "동래성의 새벽 시작",
  "이순신은 살아 있다",
  "Joseon's Counterattack: Dawn of Dongnae",
  "Start Dawn of Dongnae",
  "Yi Sun-sin lives"
)

$results = @()

if (-not (Test-Path -LiteralPath $Manifest)) {
  throw "Missing mod.manifest: $Manifest"
}

foreach ($pak in $RequiredPaks) {
  $pakPath = Join-Path $Localization $pak
  if (-not (Test-Path -LiteralPath $pakPath)) {
    throw "Missing pak: $pakPath"
  }

  $zip = [System.IO.Compression.ZipFile]::OpenRead($pakPath)
  try {
    $entry = $zip.Entries | Where-Object { $_.FullName -eq "text_ui_menus.xml" } | Select-Object -First 1
    if ($null -eq $entry) {
      throw "Missing text_ui_menus.xml in $pakPath"
    }

    $stream = $entry.Open()
    try {
      $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8, $true)
      try {
        $text = $reader.ReadToEnd()
      } finally {
        $reader.Dispose()
      }
    } finally {
      $stream.Dispose()
    }
  } finally {
    $zip.Dispose()
  }

  $matches = $Needles | Where-Object { $text.Contains($_) }
  if (@($matches).Count -lt 3) {
    throw "Expected Joseon Counterattack strings were not found in $pakPath"
  }

  $results += [pscustomobject]@{
    pak = $pak
    entry = "text_ui_menus.xml"
    size = (Get-Item -LiteralPath $pakPath).Length
    matchedNeedles = @($matches).Count
  }
}

$result = [pscustomobject]@{
  status = "ok"
  modRoot = $ModRoot
  paks = $results
  note = "KCD2 original Data and Localization files are untouched; this verifies the separate Mods package."
}

$result | ConvertTo-Json -Depth 5
