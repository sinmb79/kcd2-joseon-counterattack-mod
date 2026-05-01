param(
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2",
  [switch]$NoInstall
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ScriptRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ScriptRoot
$RepoRoot = Split-Path -Parent $ProjectRoot
$PatchPath = Join-Path $ProjectRoot "patches\localization_overrides.json"
$GameplayPatchPath = Join-Path $ProjectRoot "patches\gameplay_overrides.json"
$LongPatchPath = Join-Path $ProjectRoot "patches\long_campaign_overrides.json"
$TemplateManifest = Join-Path $ProjectRoot "templates\mod.manifest"
$Patch = Get-Content -Raw -Encoding UTF8 -LiteralPath $PatchPath | ConvertFrom-Json
$GameplayPatch = Get-Content -Raw -Encoding UTF8 -LiteralPath $GameplayPatchPath | ConvertFrom-Json
$LongPatch = Get-Content -Raw -Encoding UTF8 -LiteralPath $LongPatchPath | ConvertFrom-Json
$ModId = [string]$Patch.modId

if ($ModId -notmatch '^[a-z_]+$') {
  throw "modId must contain lowercase letters and underscores only: $ModId"
}

if ([string]$GameplayPatch.modId -ne $ModId) {
  throw "Gameplay patch modId does not match localization modId."
}

$LocalizationRoot = Join-Path $GameRoot "Localization"
$DataRoot = Join-Path $GameRoot "Data"
$ModsRoot = Join-Path $GameRoot "Mods"
$BuildRoot = Join-Path $ProjectRoot "build\$ModId"
$BuildLocalization = Join-Path $BuildRoot "Localization"
$BuildData = Join-Path $BuildRoot "Data"
$InstallRoot = Join-Path $ModsRoot $ModId
$InstallLocalization = Join-Path $InstallRoot "Localization"
$InstallData = Join-Path $InstallRoot "Data"

function Get-ZipEntryText {
  param(
    [string]$PakPath,
    [string]$EntryName
  )

  $zip = [System.IO.Compression.ZipFile]::OpenRead($PakPath)
  try {
    $entry = $zip.Entries | Where-Object { $_.FullName -ieq $EntryName } | Select-Object -First 1
    if ($null -eq $entry) {
      throw "Entry '$EntryName' not found in '$PakPath'."
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

function Save-XmlWithoutDeclaration {
  param(
    [xml]$Document,
    [string]$Path
  )

  $settings = [System.Xml.XmlWriterSettings]::new()
  $settings.Encoding = [System.Text.UTF8Encoding]::new($false)
  $settings.OmitXmlDeclaration = $true
  $settings.Indent = $false

  $writer = [System.Xml.XmlWriter]::Create($Path, $settings)
  try {
    $Document.Save($writer)
  } finally {
    $writer.Dispose()
  }
}

function New-PakFromFile {
  param(
    [string]$SourceFile,
    [string]$PakFile,
    [string]$EntryName
  )

  if (Test-Path -LiteralPath $PakFile) {
    Remove-Item -LiteralPath $PakFile -Force
  }

  $archive = [System.IO.Compression.ZipFile]::Open($PakFile, [System.IO.Compression.ZipArchiveMode]::Create)
  try {
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
      $archive,
      $SourceFile,
      $EntryName,
      [System.IO.Compression.CompressionLevel]::NoCompression
    ) | Out-Null
  } finally {
    $archive.Dispose()
  }
}

function New-PakFromDirectory {
  param(
    [string]$SourceDirectory,
    [string]$PakFile
  )

  if (Test-Path -LiteralPath $PakFile) {
    Remove-Item -LiteralPath $PakFile -Force
  }

  $sourceRoot = (Resolve-Path -LiteralPath $SourceDirectory).Path.TrimEnd('\')
  $targetPak = [System.IO.Path]::GetFullPath($PakFile)
  $archive = [System.IO.Compression.ZipFile]::Open($PakFile, [System.IO.Compression.ZipArchiveMode]::Create)
  try {
    Get-ChildItem -File -Recurse -LiteralPath $sourceRoot | ForEach-Object {
      if ([System.IO.Path]::GetFullPath($_.FullName) -eq $targetPak) {
        return
      }
      $relative = $_.FullName.Substring($sourceRoot.Length).TrimStart('\') -replace '\\', '/'
      [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $archive,
        $_.FullName,
        $relative,
        [System.IO.Compression.CompressionLevel]::NoCompression
      ) | Out-Null
    }
  } finally {
    $archive.Dispose()
  }
}

function Get-LanguageBank {
  param(
    [object]$PatchData,
    [string]$LanguageCode
  )

  $property = $PatchData.PSObject.Properties[$LanguageCode]
  if ($null -eq $property) {
    throw "Missing language bank '$LanguageCode' in long campaign patch."
  }
  return $property.Value
}

function Get-LongCampaignText {
  param(
    [object]$Bank,
    [string]$Mode,
    [int]$Index,
    [string]$RowId
  )

  if ($Mode -eq "quest") {
    $chapters = @($Bank.questChapters)
    $chapterIndex = [int]([Math]::Floor($Index / 4) % $chapters.Count)
    $chapter = $chapters[$chapterIndex]
    switch ($Index % 4) {
      0 { return "$($chapter.code) $($chapter.title)" }
      1 { return [string]$chapter.objective }
      2 { return [string]$chapter.journal }
      default { return [string]$chapter.complication }
    }
  }

  if ($Mode -eq "item") {
    if ($RowId -like "alch_*step*") {
      $recipes = @($Bank.recipeSteps)
      return [string]$recipes[$Index % $recipes.Count]
    }

    $items = @($Bank.items)
    $item = $items[$Index % $items.Count]
    if ($RowId -match "(desc|description|lore|text)") {
      return [string]$item.description
    }
    return [string]$item.name
  }

  if ($Mode -eq "soul") {
    $traits = @($Bank.traits)
    $trait = $traits[$Index % $traits.Count]
    if ($RowId -match "(desc|description|lore|text)") {
      return [string]$trait.description
    }
    return [string]$trait.name
  }

  throw "Unknown long campaign mode: $Mode"
}

function Apply-LongCampaignRewrite {
  param(
    [xml]$Document,
    [object]$Rule,
    [object]$EnglishBank,
    [object]$LocalizedBank
  )

  $changed = 0
  $index = 0
  foreach ($row in $Document.Table.Row) {
    $cells = $row.SelectNodes("Cell")
    if ($cells.Count -lt 3) {
      continue
    }

    $rowId = [string]$cells.Item(0).InnerText
    $cells.Item(1).InnerText = Get-LongCampaignText -Bank $EnglishBank -Mode ([string]$Rule.mode) -Index $index -RowId $rowId
    $cells.Item(2).InnerText = Get-LongCampaignText -Bank $LocalizedBank -Mode ([string]$Rule.mode) -Index $index -RowId $rowId
    $changed += 1
    $index += 1
  }

  return $changed
}

if (-not (Test-Path -LiteralPath $GameRoot)) {
  throw "KCD2 game root not found: $GameRoot"
}

if (-not (Test-Path -LiteralPath $LocalizationRoot)) {
  throw "KCD2 Localization folder not found: $LocalizationRoot"
}

if (-not (Test-Path -LiteralPath $DataRoot)) {
  throw "KCD2 Data folder not found: $DataRoot"
}

if (Test-Path -LiteralPath $BuildRoot) {
  Remove-Item -LiteralPath $BuildRoot -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $BuildLocalization | Out-Null
New-Item -ItemType Directory -Force -Path $BuildData | Out-Null
Copy-Item -LiteralPath $TemplateManifest -Destination (Join-Path $BuildRoot "mod.manifest") -Force

$report = [ordered]@{
  generatedAt = (Get-Date).ToString("s")
  gameRoot = $GameRoot
  modId = $ModId
  files = @()
}

foreach ($language in $Patch.languages) {
  $pakName = [string]$language.pak
  $sourcePak = Join-Path $LocalizationRoot $pakName
  if (-not (Test-Path -LiteralPath $sourcePak)) {
    throw "Source localization pak not found: $sourcePak"
  }

  $languageTemp = Join-Path $BuildRoot ("_localization_temp\" + [System.IO.Path]::GetFileNameWithoutExtension($pakName))
  New-Item -ItemType Directory -Force -Path $languageTemp | Out-Null

  $languageCode = if ($pakName -like "Korean*") { "ko" } else { "en" }
  $englishBank = Get-LanguageBank -PatchData $LongPatch -LanguageCode "en"
  $localizedBank = Get-LanguageBank -PatchData $LongPatch -LanguageCode $languageCode

  $entrySets = @()
  if ($null -ne $language.entries) {
    $entrySets = @($language.entries)
  } else {
    $entrySets = @([pscustomobject]@{
      entry = [string]$Patch.entry
      rows = $language.rows
    })
  }

  $entryNames = [System.Collections.Generic.List[string]]::new()
  foreach ($entrySet in $entrySets) {
    $entryNameForSet = [string]$entrySet.entry
    if (-not $entryNames.Contains($entryNameForSet)) {
      $entryNames.Add($entryNameForSet)
    }
  }
  if ($LongPatch.enabled) {
    foreach ($longRule in @($LongPatch.entries)) {
      $longEntryName = [string]$longRule.entry
      if (-not $entryNames.Contains($longEntryName)) {
        $entryNames.Add($longEntryName)
      }
    }
  }

  foreach ($entryName in $entryNames) {
    [xml]$doc = Get-ZipEntryText -PakPath $sourcePak -EntryName $entryName

    $longRule = @($LongPatch.entries) | Where-Object { [string]$_.entry -eq $entryName } | Select-Object -First 1
    if ($LongPatch.enabled -and $null -ne $longRule) {
      $longChanged = Apply-LongCampaignRewrite -Document $doc -Rule $longRule -EnglishBank $englishBank -LocalizedBank $localizedBank
      $report.files += [ordered]@{
        kind = "long_campaign"
        pak = $pakName
        entry = $entryName
        rowsChanged = $longChanged
      }
    }

    $explicitSet = $entrySets | Where-Object { [string]$_.entry -eq $entryName } | Select-Object -First 1
    if ($null -ne $explicitSet) {
      foreach ($override in @($explicitSet.rows)) {
        $rowId = [string]$override.id
        $row = $doc.Table.Row | Where-Object { $_.Cell[0] -eq $rowId } | Select-Object -First 1
        if ($null -eq $row) {
          throw "Row '$rowId' not found in $pakName/$entryName"
        }

        $cells = $row.SelectNodes("Cell")
        $cells.Item(1).InnerText = [string]$override.english
        $cells.Item(2).InnerText = [string]$override.localized
      }
    }

    $xmlOut = Join-Path $languageTemp $entryName
    Save-XmlWithoutDeclaration -Document $doc -Path $xmlOut

    if ($null -ne $explicitSet) {
      $report.files += [ordered]@{
        kind = "localization"
        pak = $pakName
        entry = $entryName
        rowsChanged = @($explicitSet.rows).Count
      }
    }
  }

  $pakOut = Join-Path $BuildLocalization $pakName
  New-PakFromDirectory -SourceDirectory $languageTemp -PakFile $pakOut

  Remove-Item -LiteralPath $languageTemp -Recurse -Force
}

$tablesPak = Join-Path $DataRoot ([string]$GameplayPatch.sourcePak)
if (-not (Test-Path -LiteralPath $tablesPak)) {
  throw "Source table pak not found: $tablesPak"
}

[xml]$sourceRpg = Get-ZipEntryText -PakPath $tablesPak -EntryName ([string]$GameplayPatch.tableEntry)
[xml]$patchedRpg = '<?xml version="1.0" encoding="us-ascii"?><database xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="barbora" xsi:noNamespaceSchemaLocation="../database.xsd"><rpg_params version="1"></rpg_params></database>'

foreach ($param in $GameplayPatch.rpgParams) {
  $key = [string]$param.key
  $sourceRow = $sourceRpg.database.rpg_params.rpg_param | Where-Object { $_.rpg_param_key -eq $key } | Select-Object -First 1
  if ($null -eq $sourceRow) {
    throw "RPG param '$key' not found in $($GameplayPatch.tableEntry)."
  }

  $patchedRow = $patchedRpg.ImportNode($sourceRow, $true)
  $patchedRow.SetAttribute("rpg_param_value", [string]$param.value)
  $patchedRpg.database.rpg_params.AppendChild($patchedRow) | Out-Null
}

$patchedEntry = [string]$GameplayPatch.patchedEntry
$patchedFile = Join-Path $BuildData ($patchedEntry -replace '/', '\')
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $patchedFile) | Out-Null
$settings = [System.Xml.XmlWriterSettings]::new()
$settings.Encoding = [System.Text.ASCIIEncoding]::new()
$settings.OmitXmlDeclaration = $false
$settings.Indent = $true
$writer = [System.Xml.XmlWriter]::Create($patchedFile, $settings)
try {
  $patchedRpg.Save($writer)
} finally {
  $writer.Dispose()
}

$dataPakOut = Join-Path $BuildData "$ModId.pak"
New-PakFromDirectory -SourceDirectory $BuildData -PakFile $dataPakOut
Remove-Item -LiteralPath (Join-Path $BuildData "Libs") -Recurse -Force

$report.files += [ordered]@{
  kind = "gameplay"
  pak = "$ModId.pak"
  entry = $patchedEntry
  rowsChanged = @($GameplayPatch.rpgParams).Count
  output = $dataPakOut
}

$reportPath = Join-Path $BuildRoot "build-report.json"
$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $reportPath

if (-not $NoInstall) {
  New-Item -ItemType Directory -Force -Path $InstallLocalization | Out-Null
  New-Item -ItemType Directory -Force -Path $InstallData | Out-Null
  Copy-Item -LiteralPath (Join-Path $BuildRoot "mod.manifest") -Destination (Join-Path $InstallRoot "mod.manifest") -Force
  Get-ChildItem -File -LiteralPath $BuildLocalization -Filter "*.pak" |
    Copy-Item -Destination $InstallLocalization -Force
  Get-ChildItem -File -LiteralPath $BuildData -Filter "*.pak" |
    Copy-Item -Destination $InstallData -Force

  $summary = @(
    "Joseon Counterattack Early Front installed.",
    "Generated: $($report.generatedAt)",
    "Localization and gameplay table patches are installed.",
    "Original KCD2 Data and Localization folders were not modified.",
    "Mod root: $InstallRoot"
  )
  $summary | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $InstallRoot "INSTALL_SUMMARY.txt")
}

$report | ConvertTo-Json -Depth 8
