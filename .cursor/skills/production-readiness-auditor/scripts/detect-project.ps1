# Safe read-only wrapper for Production Readiness Auditor.
# Prefers Python detector; falls back to minimal PowerShell heuristics.
[CmdletBinding()]
param(
    [string]$Root = ".",
    [switch]$Json,
    [switch]$Md,
    [string]$Output
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript = Join-Path $ScriptDir "detect-project.py"

function Find-Python {
    foreach ($name in @("python3", "python", "py")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

$py = Find-Python
if ($py) {
    $argsList = @($PyScript, "--root", $Root)
    if ($Md -and -not $Json) { $argsList += "--md" } else { $argsList += "--json" }
    if ($Output) { $argsList += @("-o", $Output) }
    & $py @argsList
    exit $LASTEXITCODE
}

Write-Warning "Python not found; emitting minimal PowerShell fallback JSON"
$RootAbs = (Resolve-Path $Root).Path
$platforms = @()
if (Test-Path (Join-Path $RootAbs "pubspec.yaml")) { $platforms += "flutter" }
if (Test-Path (Join-Path $RootAbs "package.json")) {
    $pkg = Get-Content (Join-Path $RootAbs "package.json") -Raw -ErrorAction SilentlyContinue
    if ($pkg -match "react-native") { $platforms += "react-native" }
    if ($pkg -match "electron") { $platforms += "electron" }
}
if (Get-ChildItem -Path $RootAbs -Filter "*.xcodeproj" -ErrorAction SilentlyContinue) { $platforms += "ios-ipados" }
if ((Test-Path (Join-Path $RootAbs "build.gradle")) -or (Test-Path (Join-Path $RootAbs "build.gradle.kts")) -or (Test-Path (Join-Path $RootAbs "settings.gradle")) -or (Test-Path (Join-Path $RootAbs "settings.gradle.kts"))) {
    $platforms += "android"
}
if ((Get-ChildItem -Path $RootAbs -Filter "*.sln" -ErrorAction SilentlyContinue) -or (Get-ChildItem -Path $RootAbs -Filter "*.csproj" -ErrorAction SilentlyContinue)) {
    $platforms += "dotnet"
}
if ((Test-Path (Join-Path $RootAbs "src-tauri/Cargo.toml")) -or (Test-Path (Join-Path $RootAbs "tauri.conf.json"))) {
    $platforms += "tauri"
}

$commit = $null
$branch = $null
$dirty = $false
if (Get-Command git -ErrorAction SilentlyContinue) {
    $commit = (git -C $RootAbs rev-parse HEAD 2>$null)
    $branch = (git -C $RootAbs rev-parse --abbrev-ref HEAD 2>$null)
    $status = (git -C $RootAbs status --porcelain 2>$null)
    if ($status) { $dirty = $true }
}

$manifest = [ordered]@{
    schema_version     = 1
    generator          = "production-readiness-auditor/detect-project.ps1-fallback"
    root               = $RootAbs
    git                = @{ available = $true; commit = $commit; branch = $branch; dirty = $dirty }
    platforms_detected = $platforms
    notes              = @("Python unavailable; used minimal PowerShell fallback. Prefer detect-project.py.")
    safety             = @{
        read_only             = $true
        installs_packages     = $false
        mutates_project       = $false
        prints_secret_values  = $false
    }
}

$text = $manifest | ConvertTo-Json -Depth 6
if ($Output) {
    $dir = Split-Path -Parent $Output
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    Set-Content -Path $Output -Value $text -Encoding UTF8
    Write-Output "wrote $Output"
} else {
    Write-Output $text
}
