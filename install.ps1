#Requires -Version 5.1
<#
.SYNOPSIS
    Wukong Installer for Windows
.DESCRIPTION
    Installs Wukong multi-agent framework for Claude Code on Windows.
.PARAMETER TargetDir
    Target directory for installation. Defaults to current directory.
.PARAMETER Clean
    Perform a clean install by removing existing Wukong files first.
.PARAMETER Uninstall
    Remove Wukong from the system.
.PARAMETER Force
    Skip confirmation prompts.
.PARAMETER ClearState
    Clear runtime state (notepads, plans, sessions) without reinstalling.
.EXAMPLE
    .\install.ps1
    .\install.ps1 -TargetDir "C:\Projects\myproject"
    .\install.ps1 C:\Projects\myproject
    .\install.ps1 -Clean
    .\install.ps1 -Uninstall
    .\install.ps1 -Uninstall -Force
    .\install.ps1 -ClearState
#>

param(
    [Parameter(Position = 0)]
    [string]$TargetDir,

    [switch]$Clean,
    [switch]$Uninstall,
    [switch]$Force,
    [switch]$ClearState
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

# ============================================================
# Python Command Detection
# ============================================================
function Get-PythonCommand {
    # Try python3 first (preferred on Unix-like systems)
    try {
        $null = & python3 --version 2>&1
        return "python3"
    } catch {}

    # Fall back to python (common on Windows)
    try {
        $null = & python --version 2>&1
        return "python"
    } catch {}

    # No Python found
    return $null
}

# Detect Python command early
$PythonCmd = Get-PythonCommand

# ============================================================
# Handle Uninstall
# ============================================================
if ($Uninstall) {
    Write-ColorOutput "Wukong Uninstaller" "Blue"
    Write-Host ""

    # Determine target directories
    $ProjectRoot = Get-Location
    if ([string]::IsNullOrEmpty($TargetDir)) {
        $TargetDir = $ProjectRoot
    }

    if ($TargetDir -like "*.claude" -or $TargetDir -like "*.claude\") {
        $ClaudeDir = $TargetDir
        $WukongDir = Join-Path (Split-Path $TargetDir -Parent) ".wukong"
    }
    else {
        $ClaudeDir = Join-Path $TargetDir ".claude"
        $WukongDir = Join-Path $TargetDir ".wukong"
    }
    $GlobalWukongDir = Join-Path $HOME ".wukong"

    # Confirm uninstall
    if (-not $Force) {
        Write-Host "This will remove Wukong files from:"
        Write-Host "  - $ClaudeDir" -ForegroundColor DarkGray
        Write-Host "  - $WukongDir" -ForegroundColor DarkGray
        Write-Host "  - $GlobalWukongDir" -ForegroundColor DarkGray
        Write-Host ""
        $Response = Read-Host "Continue? [y/N]"
        if ($Response -notmatch "^[Yy]") {
            Write-Host "Cancelled."
            exit 0
        }
    }

    Write-Host ""
    Write-ColorOutput "[1/3] Removing Project Files" "Blue"

    # Remove core rule
    $CoreRule = "$ClaudeDir\rules\00-wukong-core.md"
    if (Test-Path $CoreRule) {
        Remove-Item $CoreRule -Force
        Write-Step "ok" "Removed core rule"
    } else {
        Write-Step "skip" "Core rule not found" "Yellow"
    }

    # Remove Wukong skills (only known Wukong skills)
    $WukongSkills = @(
        "jie.md", "ding.md", "hui.md", "shi.md",
        "jindouyun.md", "summoning.md", "orchestration.md",
        "evidence.md"
    )
    $SkillsDir = "$ClaudeDir\skills"
    $RemovedSkills = 0
    foreach ($Skill in $WukongSkills) {
        $SkillPath = Join-Path $SkillsDir $Skill
        if (Test-Path $SkillPath) {
            Remove-Item $SkillPath -Force
            $RemovedSkills++
        }
    }
    if ($RemovedSkills -gt 0) {
        Write-Step "ok" "Removed $RemovedSkills skill files"
    } else {
        Write-Step "skip" "No skill files found" "Yellow"
    }

    # Remove Wukong commands (only known Wukong commands)
    $WukongCommands = @(
        "wukong.md", "schedule.md", "neiguan.md"
    )
    $CommandsDir = "$ClaudeDir\commands"
    $RemovedCommands = 0
    foreach ($Cmd in $WukongCommands) {
        $CmdPath = Join-Path $CommandsDir $Cmd
        if (Test-Path $CmdPath) {
            Remove-Item $CmdPath -Force
            $RemovedCommands++
        }
    }
    if ($RemovedCommands -gt 0) {
        Write-Step "ok" "Removed $RemovedCommands command files"
    } else {
        Write-Step "skip" "No command files found" "Yellow"
    }

    # Remove project .wukong directory
    if (Test-Path $WukongDir) {
        Remove-Item $WukongDir -Recurse -Force
        Write-Step "ok" "Removed $WukongDir"
    } else {
        Write-Step "skip" "Project .wukong not found" "Yellow"
    }

    Write-Host ""
    Write-ColorOutput "[2/3] Removing Global Files" "Blue"

    # Remove global hooks
    $GlobalHooksDir = Join-Path $GlobalWukongDir "hooks"
    if (Test-Path $GlobalHooksDir) {
        Remove-Item $GlobalHooksDir -Recurse -Force
        Write-Step "ok" "Removed global hooks"
    } else {
        Write-Step "skip" "Global hooks not found" "Yellow"
    }

    # Remove global scheduler
    $GlobalSchedulerDir = Join-Path $GlobalWukongDir "scheduler"
    if (Test-Path $GlobalSchedulerDir) {
        Remove-Item $GlobalSchedulerDir -Recurse -Force
        Write-Step "ok" "Removed global scheduler"
    } else {
        Write-Step "skip" "Global scheduler not found" "Yellow"
    }

    # Remove global context
    $GlobalContextDir = Join-Path $GlobalWukongDir "context"
    if (Test-Path $GlobalContextDir) {
        Remove-Item $GlobalContextDir -Recurse -Force
        Write-Step "ok" "Removed global context"
    } else {
        Write-Step "skip" "Global context not found" "Yellow"
    }

    # Remove entire global .wukong if empty
    if ((Test-Path $GlobalWukongDir) -and ((Get-ChildItem $GlobalWukongDir -Force | Measure-Object).Count -eq 0)) {
        Remove-Item $GlobalWukongDir -Force
        Write-Step "ok" "Removed empty $GlobalWukongDir"
    }

    Write-Host ""
    Write-ColorOutput "[3/3] Cleaning Hook Registration" "Blue"

    # Remove hook from settings.json
    $SettingsFile = Join-Path $HOME ".claude\settings.json"
    if (Test-Path $SettingsFile) {
        try {
            $SettingsContent = Get-Content $SettingsFile -Raw
            if ($SettingsContent -match "hui-extract\.py") {
                $Settings = $SettingsContent | ConvertFrom-Json -AsHashtable

                if ($Settings.ContainsKey("hooks") -and $Settings["hooks"].ContainsKey("PreCompact")) {
                    # Filter out Wukong hooks
                    $FilteredHooks = @()
                    foreach ($HookEntry in $Settings["hooks"]["PreCompact"]) {
                        $IsWukongHook = $false
                        if ($HookEntry -is [hashtable] -and $HookEntry.ContainsKey("hooks")) {
                            foreach ($Hook in $HookEntry["hooks"]) {
                                if ($Hook -is [hashtable] -and $Hook.ContainsKey("command")) {
                                    if ($Hook["command"] -match "hui-extract\.py") {
                                        $IsWukongHook = $true
                                        break
                                    }
                                }
                            }
                        }
                        if (-not $IsWukongHook) {
                            $FilteredHooks += $HookEntry
                        }
                    }
                    $Settings["hooks"]["PreCompact"] = $FilteredHooks

                    # Remove empty hooks section
                    if ($Settings["hooks"]["PreCompact"].Count -eq 0) {
                        $Settings["hooks"].Remove("PreCompact")
                    }
                    if ($Settings["hooks"].Count -eq 0) {
                        $Settings.Remove("hooks")
                    }

                    $Settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile -Encoding UTF8
                    Write-Step "ok" "Removed hook registration from settings.json"
                }
            } else {
                Write-Step "skip" "No Wukong hooks in settings.json" "Yellow"
            }
        }
        catch {
            Write-Step "warn" "Could not clean settings.json - $_" "Yellow"
        }
    } else {
        Write-Step "skip" "settings.json not found" "Yellow"
    }

    Write-Host ""
    Write-ColorOutput "Uninstall complete!" "Green"
    exit 0
}

# ============================================================
# Handle ClearState
# ============================================================
if ($ClearState) {
    Write-ColorOutput "Wukong State Cleaner" "Blue"
    Write-Host ""

    # Determine target directories
    $ProjectRoot = Get-Location
    if ([string]::IsNullOrEmpty($TargetDir)) {
        $TargetDir = $ProjectRoot
    }

    if ($TargetDir -like "*.claude" -or $TargetDir -like "*.claude\") {
        $WukongDir = Join-Path (Split-Path $TargetDir -Parent) ".wukong"
    }
    else {
        $WukongDir = Join-Path $TargetDir ".wukong"
    }

    $StateDirs = @(
        (Join-Path $WukongDir "notepads"),
        (Join-Path $WukongDir "plans"),
        (Join-Path $WukongDir "context\sessions"),
        (Join-Path $WukongDir "context\current")
    )

    $ClearedCount = 0
    foreach ($Dir in $StateDirs) {
        if (Test-Path $Dir) {
            $Items = Get-ChildItem $Dir -Force -ErrorAction SilentlyContinue
            if ($Items) {
                Remove-Item "$Dir\*" -Recurse -Force -ErrorAction SilentlyContinue
                Write-Step "ok" "Cleared $Dir"
                $ClearedCount++
            } else {
                Write-Step "skip" "$Dir is already empty" "Yellow"
            }
        } else {
            Write-Step "skip" "$Dir not found" "Yellow"
        }
    }

    Write-Host ""
    if ($ClearedCount -gt 0) {
        Write-ColorOutput "Cleared $ClearedCount directories!" "Green"
    } else {
        Write-ColorOutput "No state to clear." "Yellow"
    }
    exit 0
}

# ============================================================
# Main Installation
# ============================================================
Write-ColorOutput "Wukong Installer" "Blue"
Write-Host ""

# Check Python availability
if (-not $PythonCmd) {
    Write-ColorOutput "Warning: Python not found. Hooks may not work correctly." "Yellow"
    Write-Host "  Please install Python and ensure it's in your PATH." -ForegroundColor DarkGray
    Write-Host ""
} else {
    Write-Host "Python detected: " -NoNewline
    Write-ColorOutput $PythonCmd "Green"
    Write-Host ""
}

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
# 3. Handle Clean Install
# ============================================================
if ($Clean) {
    Write-ColorOutput "Clean install - removing existing Wukong files first..." "Yellow"
    Write-Host ""

    # Remove existing files silently
    $CoreRule = "$ClaudeDir\rules\00-wukong-core.md"
    if (Test-Path $CoreRule) {
        Remove-Item $CoreRule -Force
    }

    # Remove skills
    $WukongSkills = @(
        "jie.md", "ding.md", "hui.md", "shi.md",
        "jindouyun.md", "summoning.md", "orchestration.md",
        "evidence.md"
    )
    foreach ($Skill in $WukongSkills) {
        $SkillPath = Join-Path "$ClaudeDir\skills" $Skill
        if (Test-Path $SkillPath) {
            Remove-Item $SkillPath -Force
        }
    }

    # Remove commands
    $WukongCommands = @("wukong.md", "schedule.md", "neiguan.md")
    foreach ($Cmd in $WukongCommands) {
        $CmdPath = Join-Path "$ClaudeDir\commands" $Cmd
        if (Test-Path $CmdPath) {
            Remove-Item $CmdPath -Force
        }
    }

    # Remove project .wukong
    if (Test-Path $WukongDir) {
        Remove-Item $WukongDir -Recurse -Force
    }

    Write-Step "ok" "Cleaned existing installation"
    Write-Host ""
}

# ============================================================
# 4. Install project files
# ============================================================
Write-ColorOutput "[1/4] Project Files" "Blue"

# Create directory structure
$Directories = @(
    "$ClaudeDir\rules",
    "$ClaudeDir\commands",
    "$ClaudeDir\skills",
    "$WukongDir\notepads",
    "$WukongDir\plans",
    "$WukongDir\context\current",
    "$WukongDir\context\sessions",
    "$WukongDir\scheduler"
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

# Copy scheduler module (project level)
$SchedulerSource = Join-Path $SourceDir "scheduler"
if (Test-Path $SchedulerSource) {
    $SchedulerDest = Join-Path $WukongDir "scheduler"
    if (-not (Test-Path $SchedulerDest)) {
        New-Item -ItemType Directory -Path $SchedulerDest -Force | Out-Null
    }
    $SchedulerFiles = Get-ChildItem "$SchedulerSource\*.py" -ErrorAction SilentlyContinue
    if ($SchedulerFiles) {
        Copy-Item "$SchedulerSource\*.py" -Destination $SchedulerDest -Force
        Write-Step "ok" "Scheduler module ($($SchedulerFiles.Count) files)"
    }
}

# Copy context Python files (project level)
$ContextSource = Join-Path $SourceDir "context"
if (Test-Path $ContextSource) {
    $ContextDest = Join-Path $WukongDir "context"
    if (-not (Test-Path $ContextDest)) {
        New-Item -ItemType Directory -Path $ContextDest -Force | Out-Null
    }
    $ContextFiles = Get-ChildItem "$ContextSource\*.py" -ErrorAction SilentlyContinue
    if ($ContextFiles) {
        Copy-Item "$ContextSource\*.py" -Destination $ContextDest -Force
        Write-Step "ok" "Context module ($($ContextFiles.Count) files)"
    }
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
# 5. Install global hooks
# ============================================================
Write-ColorOutput "[2/4] Global Hooks" "Blue"

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

# Copy scheduler module (global)
$GlobalSchedulerDir = Join-Path $GlobalWukongDir "scheduler"
if (-not (Test-Path $GlobalSchedulerDir)) {
    New-Item -ItemType Directory -Path $GlobalSchedulerDir -Force | Out-Null
}
$SchedulerSource = Join-Path $SourceDir "scheduler"
if (Test-Path $SchedulerSource) {
    $SchedulerFiles = Get-ChildItem "$SchedulerSource\*.py" -ErrorAction SilentlyContinue
    if ($SchedulerFiles) {
        Copy-Item "$SchedulerSource\*.py" -Destination $GlobalSchedulerDir -Force
        Write-Step "ok" "Installed scheduler to ~\.wukong\scheduler\ ($($SchedulerFiles.Count) files)"
    }
}

# Copy context module (global)
$GlobalContextDir = Join-Path $GlobalWukongDir "context"
if (-not (Test-Path $GlobalContextDir)) {
    New-Item -ItemType Directory -Path $GlobalContextDir -Force | Out-Null
}
$ContextSource = Join-Path $SourceDir "context"
if (Test-Path $ContextSource) {
    $ContextFiles = Get-ChildItem "$ContextSource\*.py" -ErrorAction SilentlyContinue
    if ($ContextFiles) {
        Copy-Item "$ContextSource\*.py" -Destination $GlobalContextDir -Force
        Write-Step "ok" "Installed context to ~\.wukong\context\ ($($ContextFiles.Count) files)"
    }
}

Write-Host ""

# ============================================================
# 6. Register hooks to Claude Code
# ============================================================
Write-ColorOutput "[3/4] Hook Registration" "Blue"

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

        # Hook configuration - use detected Python command, fallback to python3
        $HookPython = if ($PythonCmd) { $PythonCmd } else { "python3" }
        $HookCommand = "$HookPython ~/.wukong/hooks/hui-extract.py"

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
                $ManualHookPython = if ($PythonCmd) { $PythonCmd } else { "python3" }
                Write-Host @"

  {
    "hooks": {
      "PreCompact": [{
        "matcher": "auto",
        "hooks": [{
          "type": "command",
          "command": "$ManualHookPython ~/.wukong/hooks/hui-extract.py",
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
        $ManualHookPython = if ($PythonCmd) { $PythonCmd } else { "python3" }
        Write-Host @"

  {
    "hooks": {
      "PreCompact": [{
        "matcher": "auto",
        "hooks": [{
          "type": "command",
          "command": "$ManualHookPython ~/.wukong/hooks/hui-extract.py",
          "timeout": 30
        }]
      }]
    }
  }
"@
    }
}

Write-Host ""

# ============================================================
# 7. Verify Installation
# ============================================================
Write-ColorOutput "[4/4] Verifying Installation" "Blue"

$VerificationItems = @(
    @{ Path = "$ClaudeDir\rules\00-wukong-core.md"; Name = "Core rule" },
    @{ Path = "$ClaudeDir\skills"; Name = "Skills directory" },
    @{ Path = "$ClaudeDir\commands"; Name = "Commands directory" },
    @{ Path = "$WukongDir\scheduler"; Name = "Scheduler module" },
    @{ Path = "$WukongDir\context"; Name = "Context module" },
    @{ Path = "$GlobalWukongDir\hooks"; Name = "Global hooks" },
    @{ Path = "$GlobalWukongDir\scheduler"; Name = "Global scheduler" },
    @{ Path = "$GlobalWukongDir\context"; Name = "Global context" }
)

$AllOk = $true
$VerifiedCount = 0
foreach ($Item in $VerificationItems) {
    if (Test-Path $Item.Path) {
        Write-Step "ok" $Item.Name
        $VerifiedCount++
    } else {
        Write-Step "fail" $Item.Name "Red"
        $AllOk = $false
    }
}

if (-not $AllOk) {
    Write-Host ""
    Write-ColorOutput "Warning: Some components may not have installed correctly." "Yellow"
}

# ============================================================
# 8. Cleanup and finish
# ============================================================

# Cleanup temp directory if we downloaded from GitHub
if ($TempDir -and (Test-Path $TempDir)) {
    Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-ColorOutput "Done! ($VerifiedCount/$($VerificationItems.Count) components verified)" "Green"
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
Write-Host "  ~\.wukong\scheduler\  " -NoNewline -ForegroundColor DarkGray
Write-Host "Scheduler module"
Write-Host "  ~\.wukong\context\    " -NoNewline -ForegroundColor DarkGray
Write-Host "Context module"
Write-Host ""
Write-Host "Python command: " -NoNewline
if ($PythonCmd) {
    Write-ColorOutput $PythonCmd "Green"
} else {
    Write-ColorOutput "Not found (hooks may not work)" "Yellow"
}
Write-Host ""
Write-Host "Start Claude Code and say: " -NoNewline
Write-ColorOutput "/wukong" "Green"
