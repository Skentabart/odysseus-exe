param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dist = Join-Path $RepoRoot "dist"
$AppLayout = Join-Path $Dist "app"

Write-Host "Odysseus Windows Native build scaffold"
Write-Host "Cleaning $Dist"
if (Test-Path $Dist) { Remove-Item -Recurse -Force $Dist }
New-Item -ItemType Directory -Force -Path $Dist | Out-Null
New-Item -ItemType Directory -Force -Path $AppLayout | Out-Null

if (-not $SkipTests) {
    Write-Host "Running Windows-native Python tests"
    python -m pytest tests/windows
}

foreach ($dir in @("runtime", "backend", "frontend", "bin", "resources")) {
    New-Item -ItemType Directory -Force -Path (Join-Path $AppLayout $dir) | Out-Null
}
"@echo off`r`npython -m windows_native --app-dir %~dp0 --portable init`r`npython -m windows_native --app-dir %~dp0 --portable hardware`r`npause" | Set-Content -Encoding ASCII (Join-Path $AppLayout "Odysseus.cmd")
Copy-Item -Recurse -Force (Join-Path $RepoRoot "windows_native") (Join-Path $AppLayout "backend\windows_native")

$PortableRoot = Join-Path $Dist "Odysseus-Portable"
Copy-Item -Recurse -Force $AppLayout $PortableRoot
New-Item -ItemType Directory -Force -Path (Join-Path $PortableRoot "data") | Out-Null
"portable" | Set-Content -Encoding UTF8 (Join-Path $PortableRoot "odysseus.portable")
"Odysseus Portable scaffold. Run Odysseus.cmd for maintenance CLI initialization. Full Odysseus.exe desktop/runtime packaging is implemented in later phases." | Set-Content -Encoding UTF8 (Join-Path $PortableRoot "README.txt")
Compress-Archive -Path (Join-Path $PortableRoot "*") -DestinationPath (Join-Path $Dist "Odysseus-Portable.zip") -Force

$iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
if ($iscc) {
    & $iscc.Source (Join-Path $RepoRoot "packaging\inno\Odysseus.iss")
} else {
    Write-Warning "Inno Setup compiler (iscc.exe) was not found; Odysseus-Setup.exe was not produced."
}
