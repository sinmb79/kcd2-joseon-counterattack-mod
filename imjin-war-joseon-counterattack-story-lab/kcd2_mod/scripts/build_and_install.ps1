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
$TemplateManifest = Join-Path $ProjectRoot "templates\mod.manifest"
$Patch = Get-Content -Raw -Encoding UTF8 -LiteralPath $PatchPath | ConvertFrom-Json
$ModId = [string]$Patch.modId

if ($ModId -notmatch '^[a-z_]+$') {
  throw "modId must contain lowercase letters and underscores only: $ModId"
}

$LocalizationRoot = Join-Path $GameRoot "Localization"
$ModsRoot = Join-Path $GameRoot "Mods"
$BuildRoot = Join-Path $ProjectRoot "build\$ModId"
$BuildLocalization = Join-Path $BuildRoot "Localization"
$InstallRoot = Join-Path $ModsRoot $ModId
$InstallLocalization = Join-Path $InstallRoot "Localization"

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

if (-not (Test-Path -LiteralPath $GameRoot)) {
  throw "KCD2 game root not found: $GameRoot"
}

if (-not (Test-Path -LiteralPath $LocalizationRoot)) {
  throw "KCD2 Localization folder not found: $LocalizationRoot"
}

New-Item -ItemType Directory -Force -Path $BuildLocalization | Out-Null
Copy-Item -LiteralPath $TemplateManifest -Destination (Join-Path $BuildRoot "mod.manifest") -Force

$report = [ordered]@{
  generatedAt = (Get-Date).ToString("s")
  gameRoot = $GameRoot
  modId = $ModId
  files = @()
}

foreach ($language in $Patch.languages) {
  $pakName = [string]$language.pak
  $entryName = [string]$Patch.entry
  $sourcePak = Join-Path $LocalizationRoot $pakName
  if (-not (Test-Path -LiteralPath $sourcePak)) {
    throw "Source localization pak not found: $sourcePak"
  }

  [xml]$doc = Get-ZipEntryText -PakPath $sourcePak -EntryName $entryName

  foreach ($override in $language.rows) {
    $rowId = [string]$override.id
    $row = $doc.Table.Row | Where-Object { $_.Cell[0] -eq $rowId } | Select-Object -First 1
    if ($null -eq $row) {
      throw "Row '$rowId' not found in $pakName/$entryName"
    }

    $cells = $row.SelectNodes("Cell")
    $cells.Item(1).InnerText = [string]$override.english
    $cells.Item(2).InnerText = [string]$override.localized
  }

  $xmlOut = Join-Path $BuildLocalization $entryName
  Save-XmlWithoutDeclaration -Document $doc -Path $xmlOut

  $pakOut = Join-Path $BuildLocalization $pakName
  New-PakFromFile -SourceFile $xmlOut -PakFile $pakOut -EntryName $entryName
  Remove-Item -LiteralPath $xmlOut -Force

  $report.files += [ordered]@{
    pak = $pakName
    entry = $entryName
    rowsChanged = @($language.rows).Count
    output = $pakOut
  }
}

$reportPath = Join-Path $BuildRoot "build-report.json"
$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $reportPath

if (-not $NoInstall) {
  New-Item -ItemType Directory -Force -Path $InstallLocalization | Out-Null
  Copy-Item -LiteralPath (Join-Path $BuildRoot "mod.manifest") -Destination (Join-Path $InstallRoot "mod.manifest") -Force
  Get-ChildItem -File -LiteralPath $BuildLocalization -Filter "*.pak" |
    Copy-Item -Destination $InstallLocalization -Force

  $summary = @(
    "Joseon Counterattack Early Front installed.",
    "Generated: $($report.generatedAt)",
    "Original KCD2 Data and Localization folders were not modified.",
    "Mod root: $InstallRoot"
  )
  $summary | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $InstallRoot "INSTALL_SUMMARY.txt")
}

$report | ConvertTo-Json -Depth 8
