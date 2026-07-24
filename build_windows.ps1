param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dist = Join-Path $RepoRoot "dist"

Write-Host "Odysseus Windows Native build scaffold"
Write-Host "Cleaning $Dist"
if (Test-Path $Dist) { Remove-Item -Recurse -Force $Dist }
New-Item -ItemType Directory -Force -Path $Dist | Out-Null

if (-not $SkipTests) {
    Write-Host "Running Windows-native Python tests"
    python -m pytest tests/windows
}

$PortableRoot = Join-Path $Dist "Odysseus-Portable"
New-Item -ItemType Directory -Force -Path (Join-Path $PortableRoot "data") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PortableRoot "backend") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PortableRoot "frontend") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PortableRoot "bin") | Out-Null
"portable" | Set-Content -Encoding UTF8 (Join-Path $PortableRoot "odysseus.portable")
"Odysseus Portable scaffold. Full desktop/runtime packaging is implemented in later phases." | Set-Content -Encoding UTF8 (Join-Path $PortableRoot "README.txt")

Compress-Archive -Path $PortableRoot -DestinationPath (Join-Path $Dist "Odysseus-Portable.zip") -Force
Write-Warning "Odysseus-Setup.exe is not produced by this scaffold yet; installer packaging remains a later phase."
