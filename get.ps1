#Requires -Version 5.1
<#
.SYNOPSIS
    Phantom - Ethical RedTeam -- One-line installer
.DESCRIPTION
    Bootstrap script. Clones the repo and launches the interactive installer.
    Usage: irm https://raw.githubusercontent.com/kmdn-ch/phantom-ethical-redteam/main/get.ps1 | iex
#>

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$REPO     = "https://github.com/kmdn-ch/phantom-ethical-redteam.git"
$DEST     = "$env:USERPROFILE\phantom"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Phantom - Ethical RedTeam" -ForegroundColor Cyan
Write-Host "  One-line installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- Check git ---
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] git is required. Install it from https://git-scm.com" -ForegroundColor Red
    exit 1
}

# --- Check Python ---
$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(\d+)" -and [int]$Matches[1] -ge 11) {
            $python = $cmd
            break
        }
    }
}
if (-not $python) {
    Write-Host "[ERROR] Python 3.11+ is required. Install it from https://python.org" -ForegroundColor Red
    exit 1
}

# --- Clone or update ---
if (Test-Path "$DEST\.git") {
    Write-Host "  [i] Existing installation found at $DEST" -ForegroundColor Cyan
    Write-Host "  --> Updating to latest version..." -ForegroundColor Yellow
    Push-Location $DEST
    git pull --quiet origin main
    Pop-Location
} else {
    if (Test-Path $DEST) {
        Write-Host "  [i] Directory $DEST exists but is not a git repo — removing it." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $DEST
    }
    Write-Host "  --> Cloning Phantom to $DEST ..." -ForegroundColor Yellow
    git clone --quiet $REPO $DEST
    Write-Host "  [OK] Cloned successfully" -ForegroundColor Green
}

# --- Launch installer ---
Write-Host ""
Write-Host "  --> Launching installer..." -ForegroundColor Yellow
Write-Host ""
Set-Location $DEST
& powershell.exe -ExecutionPolicy Bypass -File ".\install.ps1"
