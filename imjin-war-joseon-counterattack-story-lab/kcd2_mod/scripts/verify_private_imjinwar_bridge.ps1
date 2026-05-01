param(
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ModRoot = Join-Path (Join-Path $GameRoot "Mods") "joseon_counterattack_early"
$PakPath = Join-Path (Join-Path $ModRoot "Data") "joseon_counterattack_private_ui.pak"
$RequiredEntries = @(
  "Libs/UI/Textures/Books/Unique/roses_book_01_ui.dds",
  "Libs/UI/Textures/Books/Maps/treasureHunter_map1_1_ui.dds",
  "Libs/UI/Textures/Apse/modal_dialog_simple.dds",
  "Libs/UI/Textures/Books/Products/replaceme_ui.dds",
  "Libs/UI/Textures/Books/Recipes/replaceme_ui.dds",
  "Libs/UI/Textures/Apse/buff_disks.dds"
)

if (!(Test-Path -LiteralPath $PakPath -PathType Leaf)) {
  throw "Private UI bridge pak was not found: $PakPath"
}

$zip = [System.IO.Compression.ZipFile]::OpenRead($PakPath)
try {
  $entries = @($zip.Entries | ForEach-Object { $_.FullName })
  $missing = @($RequiredEntries | Where-Object { $entries -notcontains $_ })
  if ($missing.Count -gt 0) {
    throw "Private UI bridge pak is missing entries: $($missing -join ', ')"
  }

  [pscustomobject]@{
    status = "ok"
    privatePak = $PakPath
    entryCount = $entries.Count
    requiredEntries = $RequiredEntries
    note = "This verifies the local-only private UI bridge pak. It must not be committed or redistributed."
  } | ConvertTo-Json -Depth 5
} finally {
  $zip.Dispose()
}
