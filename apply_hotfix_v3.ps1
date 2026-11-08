$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Write-Host "AVAN Stage 20 Visual + Studio Hotfix V3" -ForegroundColor Cyan

if (-not (Test-Path ".\manage.py")) {
  Write-Host "Run this script from C:\Users\Tara\Desktop\avan-starter" -ForegroundColor Red
  exit 1
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "Git was not found." -ForegroundColor Red
  exit 1
}

$inside = (git rev-parse --is-inside-work-tree 2>$null | Select-Object -First 1)
if ($inside -ne "true") {
  Write-Host "This folder is not a Git work tree." -ForegroundColor Red
  exit 1
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = ".stage20-v3-backup-$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

$backupFiles = @(
  "templates\base.html",
  "templates\core\home.html",
  "templates\designs\studio.html",
  "static\js\stage20-studio.js",
  "static\css\stage20-studio.css",
  "static\css\stage20-header-hotfix.css"
)
foreach ($f in $backupFiles) {
  if (Test-Path $f) {
    $dest = Join-Path $backup $f
    $dir = Split-Path $dest
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    Copy-Item $f $dest -Force
  }
}
Write-Host "Backup created: $backup" -ForegroundColor DarkGray

function Commit-ContainsMarker([string]$commit, [string]$path, [string]$marker) {
  & git grep -q -F -- $marker $commit -- $path 2>$null
  return ($LASTEXITCODE -eq 0)
}

function Find-PreStage20Commit([string]$path, [string]$marker) {
  $commits = @(& git log --format=%H -- $path 2>$null)
  foreach ($commit in $commits) {
    if (-not $commit) { continue }
    if (-not (Commit-ContainsMarker $commit.Trim() $path $marker)) {
      return $commit.Trim()
    }
  }
  return $null
}

function Restore-PreStage20File([string]$path, [string]$marker) {
  $commit = Find-PreStage20Commit $path $marker
  if (-not $commit) { return $false }

  & git checkout $commit -- $path 2>$null
  if ($LASTEXITCODE -ne 0) { return $false }
  & git reset --quiet HEAD -- $path 2>$null

  Write-Host "Restored safely: $path from $($commit.Substring(0,8))" -ForegroundColor Green
  return $true
}

$baseRestored = Restore-PreStage20File "templates/base.html" "site-header-v5"
$homeRestored = Restore-PreStage20File "templates/core/home.html" "v20-home-hero"

if (-not $baseRestored) {
  Write-Host "Could not find a pre-Stage20 base.html in Git history." -ForegroundColor Red
  exit 1
}
if (-not $homeRestored) {
  Write-Host "Could not find a pre-Stage20 home.html in Git history." -ForegroundColor Red
  exit 1
}

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item "$here\templates\designs\studio.html" ".\templates\designs\studio.html" -Force
Copy-Item "$here\static\js\stage20-studio.js" ".\static\js\stage20-studio.js" -Force
Copy-Item "$here\static\css\stage20-studio.css" ".\static\css\stage20-studio.css" -Force
Copy-Item "$here\static\css\stage20-header-hotfix.css" ".\static\css\stage20-header-hotfix.css" -Force

# Link responsive CSS using explicit UTF-8 without BOM.
$basePath = (Resolve-Path ".\templates\base.html").Path
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$baseBytes = [System.IO.File]::ReadAllBytes($basePath)
$baseText = $utf8NoBom.GetString($baseBytes)
$link = '<link rel="stylesheet" href="{% static ''css/stage20-header-hotfix.css'' %}">'
if ($baseText -notmatch [regex]::Escape("stage20-header-hotfix.css")) {
  if ($baseText.Contains("</head>")) {
    $baseText = $baseText.Replace("</head>", "    $link`r`n</head>")
    [System.IO.File]::WriteAllText($basePath, $baseText, $utf8NoBom)
    Write-Host "Responsive header hotfix linked." -ForegroundColor Green
  } else {
    Write-Host "Warning: </head> not found; CSS copied but not linked." -ForegroundColor Yellow
  }
}

# Sanity check for common mojibake lead characters without embedding non-ASCII literals.
$homePath = (Resolve-Path ".\templates\core\home.html").Path
$check = [System.IO.File]::ReadAllText($basePath, $utf8NoBom) + "`n" + [System.IO.File]::ReadAllText($homePath, $utf8NoBom)
$badChars = @([char]0x00C3, [char]0x00D8, [char]0x00D9)
$bad = $false
foreach ($ch in $badChars) {
  if ($check.IndexOf([string]$ch) -ge 0) { $bad = $true; break }
}
if ($bad) {
  Write-Host "Warning: suspicious mojibake characters are still present. Stop here and send the console output." -ForegroundColor Yellow
  exit 2
}

Write-Host "UTF-8 sanity check: OK" -ForegroundColor Green
Write-Host "Hotfix V3 applied." -ForegroundColor Green
Write-Host "Next command:" -ForegroundColor Cyan
Write-Host "docker compose -f docker-compose.yml -f docker-compose.dev.yml restart web"
Write-Host "Then press Ctrl+F5 in the browser."
