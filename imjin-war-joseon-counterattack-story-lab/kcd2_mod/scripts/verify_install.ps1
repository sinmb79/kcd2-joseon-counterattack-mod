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
$RequiredEntries = @("text_ui_menus.xml", "text_ui_tutorials.xml", "text_ui_quest.xml", "text_ui_items.xml", "text_ui_soul.xml")
$GameplayPak = Join-Path $Data "$ModId.pak"
$GameplayEntry = [string]$GameplayPatch.patchedEntry
$DeepDataEntries = @(
  "Libs/Tables/item/InventoryPreset__player.xml",
  "Libs/Tables/item/clothing_preset__joseon_counterattack_early.xml",
  "Libs/Tables/item/weapon_preset__joseon_counterattack_early.xml",
  "Libs/Storm/equipment/player.xml"
)

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
  'Dawn of Dongnae is not a story'
)

$TutorialNeedles = @(
  'Land Battle',
  'opening days of the war',
  'out of stamina'
)

$QuestNeedles = @(
  'The Red Beacon of Busanjin',
  'Yi Sun-sin lives',
  'Map of the Counterattack'
)

$ItemNeedles = @(
  'Dongnae Dispatch',
  'Gate Guard Spear',
  'Powderproofing Formula'
)

$SoulNeedles = @(
  'Courier''s Breath',
  'Promise of the Southern Sea',
  'Courier Han-gyeol'
)

$StarterNeedles = @(
  'joseon_counterattack_courier',
  'joseon_counterattack_land_front_weapons',
  'bandage_classic'
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
    $needles = switch ($entry) {
      "text_ui_menus.xml" { $MenuNeedles }
      "text_ui_tutorials.xml" { $TutorialNeedles }
      "text_ui_quest.xml" { $QuestNeedles }
      "text_ui_items.xml" { $ItemNeedles }
      "text_ui_soul.xml" { $SoulNeedles }
      default { @() }
    }
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

foreach ($deepEntry in $DeepDataEntries) {
  $deepText = Get-ZipEntryText -PakPath $GameplayPak -EntryName $deepEntry
  if ($deepEntry -eq "Libs/Tables/item/InventoryPreset__player.xml") {
    $matches = $StarterNeedles | Where-Object { $deepText.Contains($_) }
    if (@($matches).Count -lt 3) {
      throw "Expected Joseon starter inventory items were not found in $GameplayPak/$deepEntry"
    }
  } elseif ($deepEntry -eq "Libs/Tables/item/clothing_preset__joseon_counterattack_early.xml") {
    $matches = @('01894921-14e0-4012-a3a6-5f1fcf01d2d2', '3694c855-086f-4ce4-b402-a97ecce944f9', '018c1614-ddbf-4d9b-a797-40330be86c1c') | Where-Object { $deepText.Contains($_) }
    if (@($matches).Count -lt 3) {
      throw "Expected Joseon clothing preset items were not found in $GameplayPak/$deepEntry"
    }
  } elseif ($deepEntry -eq "Libs/Tables/item/weapon_preset__joseon_counterattack_early.xml") {
    $matches = @('059893ea-3aef-48b3-b1ce-7eb3391fa028', '0077dfa2-b9be-4ae3-ae59-2803ba49dfcb', '710e3706-8974-404b-b23a-6f51670ef1ed') | Where-Object { $deepText.Contains($_) }
    if (@($matches).Count -lt 3) {
      throw "Expected Joseon weapon preset items were not found in $GameplayPak/$deepEntry"
    }
  } else {
    $matches = @()
  }

  $results += [pscustomobject]@{
    kind = "deep_data"
    pak = "$ModId.pak"
    entry = $deepEntry
    size = $deepText.Length
    matchedNeedles = @($matches).Count
  }
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
