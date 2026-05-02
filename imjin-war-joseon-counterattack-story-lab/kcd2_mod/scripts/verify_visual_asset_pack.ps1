param(
  [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ModRoot = Join-Path (Join-Path $GameRoot "Mods") "joseon_counterattack_early"
$PakPath = Join-Path (Join-Path $ModRoot "Data") "joseon_counterattack_private_ui.pak"
$RequiredEntries = @(
  "Libs/UI/Textures/Apse/item_selection.dds",
  "Libs/UI/Textures/Apse/item_info.dds",
  "Libs/UI/Textures/Apse/character_slot.dds",
  "Libs/UI/Textures/Apse/reputation.dds",
  "Libs/UI/Textures/Books/Decorations/t1_s1_first_ui.dds",
  "Libs/UI/Textures/Books/Decorations/t1_s1_p1_left_ui.dds",
  "Libs/UI/Textures/Books/Maps/treasureHunter_map1_1_ui.dds",
  "Libs/UI/Textures/Books/Products/1_ui.dds",
  "Libs/UI/Textures/Books/Ingredients/saltpeter_ui.dds",
  "Libs/UI/Textures/Books/Unique/roses_book_01_ui.dds",
  "Textures/structures/walls/plaster/plaster_a_2x2_diff.dds",
  "Textures/structures/walls/stone_wall/stone_wall_a_4x4_diff.dds",
  "Textures/structures/wood/planks_a_rustic_4x4_diff.dds",
  "Textures/structures/window/glass_diamond_window_1x1_diff.dds"
)

if (!(Test-Path -LiteralPath $PakPath -PathType Leaf)) {
  throw "Joseon visual private pak was not found: $PakPath"
}

$zip = [System.IO.Compression.ZipFile]::OpenRead($PakPath)
try {
  $entries = @($zip.Entries | ForEach-Object { $_.FullName })
  $missing = @($RequiredEntries | Where-Object { $entries -notcontains $_ })
  if ($missing.Count -gt 0) {
    throw "Joseon visual private pak is missing entries: $($missing -join ', ')"
  }
  if ($entries.Count -lt 50) {
    throw "Joseon visual private pak has too few entries: $($entries.Count)"
  }

  [pscustomobject]@{
    status = "ok"
    privatePak = $PakPath
    entryCount = $entries.Count
    requiredEntries = $RequiredEntries
    note = "This verifies the expanded local-only Joseon visual pack."
  } | ConvertTo-Json -Depth 5
} finally {
  $zip.Dispose()
}
