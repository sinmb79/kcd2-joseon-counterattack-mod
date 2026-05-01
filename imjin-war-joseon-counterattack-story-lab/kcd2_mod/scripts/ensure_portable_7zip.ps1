param(
  [string]$ToolRoot = "C:\Users\sinmb\workspace\tools\7zip",
  [string]$ArchiveUrl = "https://www.7-zip.org/a/7z2601-extra.7z"
)

$ErrorActionPreference = "Stop"

$archivePath = Join-Path $ToolRoot "7z2601-extra.7z"
$extractRoot = Join-Path $ToolRoot "extra"
$sevenZip = Join-Path $extractRoot "7za.exe"

if (Test-Path -LiteralPath $sevenZip -PathType Leaf) {
  [pscustomobject]@{
    status = "ok"
    sevenZip = $sevenZip
    source = "existing"
  } | ConvertTo-Json -Depth 4
  exit 0
}

New-Item -ItemType Directory -Path $ToolRoot -Force | Out-Null
New-Item -ItemType Directory -Path $extractRoot -Force | Out-Null

if (!(Test-Path -LiteralPath $archivePath -PathType Leaf)) {
  Invoke-WebRequest -Uri $ArchiveUrl -OutFile $archivePath
}

$tar = Join-Path $env:SystemRoot "System32\tar.exe"
if (!(Test-Path -LiteralPath $tar -PathType Leaf)) {
  throw "Windows tar.exe was not found. Cannot extract portable 7-Zip archive without installing system 7-Zip."
}

& $tar -xf $archivePath -C $extractRoot

if (!(Test-Path -LiteralPath $sevenZip -PathType Leaf)) {
  throw "Portable 7-Zip extraction completed, but 7za.exe was not found: $sevenZip"
}

[pscustomobject]@{
  status = "ok"
  sevenZip = $sevenZip
  archive = $archivePath
  source = $ArchiveUrl
  note = "Portable console 7-Zip was prepared without requiring administrator installation."
} | ConvertTo-Json -Depth 4
