param(
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ScriptRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ScriptRoot
$GameplayPatchPath = Join-Path $ProjectRoot "patches\gameplay_overrides.json"
$GameplayPatch = Get-Content -Raw -Encoding UTF8 -LiteralPath $GameplayPatchPath | ConvertFrom-Json

$ModId = "joseon_counterattack_early"
$ModRoot = Join-Path (Join-Path $GameRoot "Mods") $ModId
$Manifest = Join-Path $ModRoot "mod.manifest"
$Localization = Join-Path $ModRoot "Localization"
$Data = Join-Path $ModRoot "Data"
$RequiredLocalizationPaks = @("Korean_xml.pak", "English_xml.pak")
$RequiredEntries = @("text_ui_menus.xml", "text_ui_tutorials.xml")
$GameplayPak = Join-Path $Data "$ModId.pak"
$GameplayEntry = [string]$GameplayPatch.patchedEntry

function Get-ZipEntryText {
  param(
    [string]$PakPath,
    [string]$EntryName
  )

  $zip = [System.IO.Compression.ZipFile]::OpenRead($PakPath)
  try {
    $entry = $zip.Entries | Where-Object { $_.FullName -eq $EntryName } | Select-Object -First 1
    if ($null -eq $entry) {
      throw "Missing $EntryName in $PakPath"
    }

    $stream = $entry.Open()
    try {
      $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8, $true)
      try {
        return $reader.ReadToEnd()
      } finally {
        $reader.Dispose()
      }
    } finally {
      $stream.Dispose()
    }
  } finally {
    $zip.Dispose()
  }
}

$MenuNeedles = @(
  'Joseon''s Counterattack: Dawn of Dongnae',
  'Start Dawn of Dongnae',
  'Yi Sun-sin lives'
)

$TutorialNeedles = @(
  'Land Battle',
  'opening days of the war',
  'out of stamina'
)

$results = @()

if (-not (Test-Path -LiteralPath $Manifest)) {
  throw "Missing mod.manifest: $Manifest"
}

foreach ($pak in $RequiredLocalizationPaks) {
  $pakPath = Join-Path $Localization $pak
  if (-not (Test-Path -LiteralPath $pakPath)) {
    throw "Missing localization pak: $pakPath"
  }

  foreach ($entry in $RequiredEntries) {
    $text = Get-ZipEntryText -PakPath $pakPath -EntryName $entry
    $needles = if ($entry -eq "text_ui_menus.xml") { $MenuNeedles } else { $TutorialNeedles }
    $matches = $needles | Where-Object { $text.Contains($_) }

    if (@($matches).Count -lt 3) {
      throw "Expected Joseon Counterattack strings were not found in $pakPath/$entry"
    }

    $results += [pscustomobject]@{
      kind = "localization"
      pak = $pak
      entry = $entry
      size = (Get-Item -LiteralPath $pakPath).Length
      matchedNeedles = @($matches).Count
    }
  }
}

if (-not (Test-Path -LiteralPath $GameplayPak)) {
  throw "Missing gameplay pak: $GameplayPak"
}

[xml]$gameplayDoc = Get-ZipEntryText -PakPath $GameplayPak -EntryName $GameplayEntry
$patchedCount = 0
foreach ($param in $GameplayPatch.rpgParams) {
  $key = [string]$param.key
  $expected = [string]$param.value
  $row = $gameplayDoc.database.rpg_params.rpg_param | Where-Object { $_.rpg_param_key -eq $key } | Select-Object -First 1
  if ($null -eq $row) {
    throw "Missing gameplay RPG param: $key"
  }

  if ([string]$row.rpg_param_value -ne $expected) {
    throw "Unexpected value for ${key}: $($row.rpg_param_value), expected $expected"
  }

  $patchedCount += 1
}

$results += [pscustomobject]@{
  kind = "gameplay"
  pak = "$ModId.pak"
  entry = $GameplayEntry
  size = (Get-Item -LiteralPath $GameplayPak).Length
  patchedParams = $patchedCount
}

$result = [pscustomobject]@{
  status = "ok"
  modRoot = $ModRoot
  checks = $results
  note = "KCD2 original Data and Localization files are untouched; this verifies the separate playable Mods package."
}

$result | ConvertTo-Json -Depth 6
