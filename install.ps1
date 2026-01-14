#Requires -Version 5.1
<#
.SYNOPSIS
    Wukong Installer for Windows
.DESCRIPTION
    Installs Wukong multi-agent framework for Claude Code on Windows.
.PARAMETER TargetDir
    Target directory for installation. Defaults to current directory.
.EXAMPLE
    .\install.ps1
    .\install.ps1 -TargetDir "C:\Projects\myproject"
    .\install.ps1 C:\Projects\myproject
#>

param(
    [Parameter(Position = 0)]
    [string]$TargetDir
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Step {
    param([string]$Status, [string]$Message, [string]$Color = "Green")
    Write-Host "  [" -NoNewline
    Write-Host $Status -ForegroundColor $Color -NoNewline
    Write-Host "] $Message"
}

Write-ColorOutput "Wukong Installer" "Blue"
Write-Host ""

$ProjectRoot = Get-Location
$SourceDir = ""

# ============================================================
# 1. Determine source directory
# ============================================================
if (Test-Path "$ProjectRoot\wukong-dist" -PathType Container) {
    # New version: non-hidden directory
    $SourceDir = "$ProjectRoot\wukong-dist"
}
elseif (Test-Path "$ProjectRoot\.wukong" -PathType Container) {
    # Legacy: hidden directory
    $SourceDir = "$ProjectRoot\.wukong"
}
else {
    # Download from GitHub
    Write-Host "Fetching Wukong from GitHub..."

    $TempDir = Join-Path $env:TEMP "wukong-install-$(Get-Random)"
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

    try {
        $ZipUrl = "https://github.com/WQ09CE/wukong/archive/refs/heads/main.zip"
        $ZipPath = Join-Path $TempDir "wukong.zip"

        # Download
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing

        # Extract
        Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

        # Find source directory
        if (Test-Path "$TempDir\wukong-main\wukong-dist" -PathType Container) {
            $SourceDir = "$TempDir\wukong-main\wukong-dist"
        }
        else {
            $SourceDir = "$TempDir\wukong-main\.wukong"
        }

        if (-not (Test-Path $SourceDir -PathType Container)) {
            Write-ColorOutput "Error: Failed to fetch Wukong from GitHub." "Red"
            exit 1
        }
    }
    catch {
        Write-ColorOutput "Error: Failed to download Wukong - $_" "Red"
        if (Test-Path $TempDir) { Remove-Item $TempDir -Recurse -Force }
        exit 1
    }
}

# ============================================================
# 2. Determine target directory
# ============================================================
if ([string]::IsNullOrEmpty($TargetDir)) {
    Write-Host "Installing to current directory: " -NoNewline
    Write-ColorOutput "$ProjectRoot" "Green"
    $TargetDir = $ProjectRoot
}

# Smart detection: if TargetDir is already .claude directory
if ($TargetDir -like "*.claude" -or $TargetDir -like "*.claude\") {
    $ClaudeDir = $TargetDir
    $WukongDir = Join-Path (Split-Path $TargetDir -Parent) ".wukong"
}
else {
    $ClaudeDir = Join-Path $TargetDir ".claude"
    $WukongDir = Join-Path $TargetDir ".wukong"
}

Write-Host ""

# ============================================================
# 3. Install project files
# ============================================================
Write-ColorOutput "[1/3] Project Files" "Blue"

# Create directory structure
$Directories = @(
    "$ClaudeDir\rules",
    "$ClaudeDir\commands",
    "$ClaudeDir\skills",
    "$WukongDir\notepads",
    "$WukongDir\plans",
    "$WukongDir\context\current",
    "$WukongDir\context\sessions"
)

foreach ($Dir in $Directories) {
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }
}

# Copy core rules
$RulesSource = Join-Path $SourceDir "rules\00-wukong-core.md"
if (Test-Path $RulesSource) {
    Copy-Item $RulesSource -Destination "$ClaudeDir\rules\" -Force
    Write-Step "ok" "Core rule"
}

# Copy commands
$CommandsSource = Join-Path $SourceDir "commands"
if (Test-Path $CommandsSource) {
    $CmdFiles = Get-ChildItem "$CommandsSource\*.md" -ErrorAction SilentlyContinue
    if ($CmdFiles) {
        Copy-Item "$CommandsSource\*.md" -Destination "$ClaudeDir\commands\" -Force
        Write-Step "ok" "Commands ($($CmdFiles.Count) files)"
    }
}

# Copy skills
$SkillsSource = Join-Path $SourceDir "skills"
if (Test-Path $SkillsSource) {
    $SkillFiles = Get-ChildItem "$SkillsSource\*.md" -ErrorAction SilentlyContinue
    if ($SkillFiles) {
        Copy-Item "$SkillsSource\*.md" -Destination "$ClaudeDir\skills\" -Force
        Write-Step "ok" "Skills ($($SkillFiles.Count) files)"
    }
}

# Copy templates
$TemplatesSource = Join-Path $SourceDir "templates"
if (Test-Path $TemplatesSource) {
    $TemplatesDest = Join-Path $WukongDir "templates"
    if (-not (Test-Path $TemplatesDest)) {
        New-Item -ItemType Directory -Path $TemplatesDest -Force | Out-Null
    }
    Copy-Item "$TemplatesSource\*" -Destination $TemplatesDest -Recurse -Force
    Write-Step "ok" "Templates"
}

# Copy context templates
$ContextTemplatesSource = Join-Path $SourceDir "context\templates"
if (Test-Path $ContextTemplatesSource) {
    $ContextTemplatesDest = Join-Path $WukongDir "context\templates"
    if (-not (Test-Path $ContextTemplatesDest)) {
        New-Item -ItemType Directory -Path $ContextTemplatesDest -Force | Out-Null
    }
    Copy-Item "$ContextTemplatesSource\*" -Destination $ContextTemplatesDest -Recurse -Force
    Write-Step "ok" "Context templates"
}

# Initialize anchors file
$AnchorsFile = Join-Path $WukongDir "context\anchors.md"
if (-not (Test-Path $AnchorsFile)) {
    $AnchorsContent = @"
# Anchors (Anchor Points)

Global anchors for this project.

## Decision Anchors [D]

*No anchors yet*

## Problem Anchors [P]

*No anchors yet*
"@
    Set-Content -Path $AnchorsFile -Value $AnchorsContent -Encoding UTF8
    Write-Step "ok" "Initialized anchors.md"
}

Write-Host ""

# ============================================================
# 4. Install global hooks
# ============================================================
Write-ColorOutput "[2/3] Global Hooks" "Blue"

$GlobalWukongDir = Join-Path $HOME ".wukong"
$GlobalHooksDir = Join-Path $GlobalWukongDir "hooks"

if (-not (Test-Path $GlobalHooksDir)) {
    New-Item -ItemType Directory -Path $GlobalHooksDir -Force | Out-Null
}

# Copy hook scripts
$HooksSource = Join-Path $SourceDir "hooks"
if (Test-Path $HooksSource) {
    $HookFiles = Get-ChildItem "$HooksSource\*.py" -ErrorAction SilentlyContinue
    if ($HookFiles) {
        Copy-Item "$HooksSource\*.py" -Destination $GlobalHooksDir -Force
        Write-Step "ok" "Installed hooks to ~\.wukong\hooks\ ($($HookFiles.Count) files)"
    }
    else {
        Write-Step "skip" "No hook scripts found" "Yellow"
    }
}
else {
    Write-Step "skip" "No hooks directory found" "Yellow"
}

Write-Host ""

# ============================================================
# 5. Register hooks to Claude Code
# ============================================================
Write-ColorOutput "[3/3] Hook Registration" "Blue"

$SettingsFile = Join-Path $HOME ".claude\settings.json"
$AlreadyRegistered = $false

if (Test-Path $SettingsFile) {
    $SettingsContent = Get-Content $SettingsFile -Raw -ErrorAction SilentlyContinue
    if ($SettingsContent -match "hui-extract\.py") {
        $AlreadyRegistered = $true
    }
}

if ($AlreadyRegistered) {
    Write-Step "ok" "Hooks already registered"
}
else {
    Write-Host "  Wukong uses hooks to extract knowledge before context compaction."
    Write-Host "  This requires adding configuration to " -NoNewline
    Write-Host "~\.claude\settings.json" -ForegroundColor DarkGray
    Write-Host ""

    $Response = Read-Host "  Register hooks? [Y/n]"

    if ($Response -notmatch "^[Nn]") {
        # Create .claude directory if not exists
        $ClaudeHome = Join-Path $HOME ".claude"
        if (-not (Test-Path $ClaudeHome)) {
            New-Item -ItemType Directory -Path $ClaudeHome -Force | Out-Null
        }

        # Hook configuration - use forward slashes for cross-platform compatibility
        $HookCommand = "python3 ~/.wukong/hooks/hui-extract.py"

        $NewHook = @{
            matcher = "auto"
            hooks = @(
                @{
                    type = "command"
                    command = $HookCommand
                    timeout = 30
                }
            )
        }

        if (-not (Test-Path $SettingsFile)) {
            # Create new settings file
            $Settings = @{
                hooks = @{
                    PreCompact = @($NewHook)
                }
            }
            $Settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile -Encoding UTF8
            Write-Step "ok" "Created ~\.claude\settings.json with hooks"
        }
        else {
            # Update existing settings file
            try {
                $Settings = Get-Content $SettingsFile -Raw | ConvertFrom-Json -AsHashtable

                if (-not $Settings.ContainsKey("hooks")) {
                    $Settings["hooks"] = @{}
                }

                if (-not $Settings["hooks"].ContainsKey("PreCompact")) {
                    $Settings["hooks"]["PreCompact"] = @()
                }

                # Check for duplicates
                $IsDuplicate = $false
                foreach ($HookEntry in $Settings["hooks"]["PreCompact"]) {
                    if ($HookEntry -is [hashtable] -and $HookEntry.ContainsKey("hooks")) {
                        foreach ($Hook in $HookEntry["hooks"]) {
                            if ($Hook -is [hashtable] -and $Hook.ContainsKey("command")) {
                                if ($Hook["command"] -match "hui-extract\.py") {
                                    $IsDuplicate = $true
                                    break
                                }
                            }
                        }
                    }
                }

                if (-not $IsDuplicate) {
                    $Settings["hooks"]["PreCompact"] += $NewHook
                }

                $Settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile -Encoding UTF8
                Write-Step "ok" "Updated ~\.claude\settings.json with hooks"
            }
            catch {
                Write-Step "error" "Failed to update settings.json - $_" "Red"
                Write-Host ""
                Write-ColorOutput "  Please manually add this to ~\.claude\settings.json:" "Yellow"
                Write-Host @"

  {
    "hooks": {
      "PreCompact": [{
        "matcher": "auto",
        "hooks": [{
          "type": "command",
          "command": "python3 ~/.wukong/hooks/hui-extract.py",
          "timeout": 30
        }]
      }]
    }
  }
"@
            }
        }
    }
    else {
        Write-Host "  Skipped hook registration" -ForegroundColor DarkGray
        Write-Host ""
        Write-ColorOutput "  To enable hooks manually, add this to ~\.claude\settings.json:" "Yellow"
        Write-Host @"

  {
    "hooks": {
      "PreCompact": [{
        "matcher": "auto",
        "hooks": [{
          "type": "command",
          "command": "python3 ~/.wukong/hooks/hui-extract.py",
          "timeout": 30
        }]
      }]
    }
  }
"@
    }
}

# ============================================================
# 6. Cleanup and finish
# ============================================================

# Cleanup temp directory if we downloaded from GitHub
if ($TempDir -and (Test-Path $TempDir)) {
    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-ColorOutput "Done!" "Green"
Write-Host ""
Write-Host "Installed to:"
Write-Host "  $ClaudeDir\rules\     " -NoNewline -ForegroundColor DarkGray
Write-Host "Core rules (auto-loaded)"
Write-Host "  $ClaudeDir\skills\    " -NoNewline -ForegroundColor DarkGray
Write-Host "Avatar skills"
Write-Host "  $ClaudeDir\commands\  " -NoNewline -ForegroundColor DarkGray
Write-Host "Commands"
Write-Host "  $WukongDir\           " -NoNewline -ForegroundColor DarkGray
Write-Host "Work data"
Write-Host "  ~\.wukong\hooks\      " -NoNewline -ForegroundColor DarkGray
Write-Host "Global hooks"
Write-Host ""
Write-Host "Start Claude Code and say: " -NoNewline
Write-ColorOutput "/wukong" "Green"
