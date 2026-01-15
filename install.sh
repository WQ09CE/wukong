#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

echo -e "${BLUE}Wukong Installer${NC}"
echo ""

PROJECT_ROOT=$(pwd)
SOURCE_DIR=""
GLOBAL_WUKONG_DIR="$HOME/.wukong"

# ============================================================
# 1. 确定源目录
# ============================================================
if [ -d "$PROJECT_ROOT/wukong-dist" ]; then
    # 新版：非隐藏目录
    SOURCE_DIR="$PROJECT_ROOT/wukong-dist"
elif [ -d "$PROJECT_ROOT/.wukong" ]; then
    # 旧版兼容：隐藏目录
    SOURCE_DIR="$PROJECT_ROOT/.wukong"
else
    TEMP_DIR=$(mktemp -d)
    trap 'rm -rf "$TEMP_DIR"' EXIT

    echo "Fetching Wukong from GitHub..."
    curl -fsSL "https://github.com/anthropics/wukong/archive/refs/heads/main.tar.gz" | tar -xz -C "$TEMP_DIR"

    # 尝试新版目录结构，回退到旧版
    if [ -d "$TEMP_DIR/wukong-main/wukong-dist" ]; then
        SOURCE_DIR="$TEMP_DIR/wukong-main/wukong-dist"
    else
        SOURCE_DIR="$TEMP_DIR/wukong-main/.wukong"
    fi

    if [ ! -d "$SOURCE_DIR" ]; then
        echo -e "${RED}Error: Failed to fetch Wukong from GitHub.${NC}"
        exit 1
    fi
fi

# ============================================================
# 2. 确定目标目录
# ============================================================
TARGET_DIR="$1"

if [ -z "$TARGET_DIR" ]; then
    echo -e "Installing to current directory: ${GREEN}$PROJECT_ROOT${NC}"
    TARGET_DIR="$PROJECT_ROOT"
fi

# 智能检测: 如果 TARGET_DIR 已经是 .claude 目录，直接使用
if [[ "$TARGET_DIR" == *".claude" ]] || [[ "$TARGET_DIR" == *".claude/" ]]; then
    CLAUDE_DIR="$TARGET_DIR"
    WUKONG_DIR="$(dirname "$TARGET_DIR")/.wukong"
else
    CLAUDE_DIR="$TARGET_DIR/.claude"
    WUKONG_DIR="$TARGET_DIR/.wukong"
fi

echo ""

# ============================================================
# 3. 安装项目文件
# ============================================================
echo -e "${BLUE}[1/3] Project Files${NC}"

# 创建目录结构
mkdir -p "$CLAUDE_DIR/rules"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/skills"
mkdir -p "$WUKONG_DIR/notepads"
mkdir -p "$WUKONG_DIR/plans"
mkdir -p "$WUKONG_DIR/context/current"
mkdir -p "$WUKONG_DIR/context/sessions"

# 复制核心规则
cp "$SOURCE_DIR"/rules/00-wukong-core.md "$CLAUDE_DIR/rules/"
echo -e "  ${GREEN}[ok]${NC} Core rule"

# 复制命令
if [ -d "$SOURCE_DIR/commands" ] && ls "$SOURCE_DIR"/commands/*.md 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/commands/*.md "$CLAUDE_DIR/commands/"
    CMD_COUNT=$(ls -1 "$SOURCE_DIR"/commands/*.md 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Commands ($CMD_COUNT files)"
fi

# 复制技能
if [ -d "$SOURCE_DIR/skills" ] && ls "$SOURCE_DIR"/skills/*.md 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/skills/*.md "$CLAUDE_DIR/skills/"
    SKILL_COUNT=$(ls -1 "$SOURCE_DIR"/skills/*.md 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Skills ($SKILL_COUNT files)"
fi

# 复制模板
if [ -d "$SOURCE_DIR/templates" ]; then
    mkdir -p "$WUKONG_DIR/templates"
    cp -R "$SOURCE_DIR"/templates/. "$WUKONG_DIR/templates/"
    echo -e "  ${GREEN}[ok]${NC} Templates"
fi

# 复制上下文模板 (跳过相同文件)
if [ -d "$SOURCE_DIR/context/templates" ]; then
    mkdir -p "$WUKONG_DIR/context/templates"
    cp -R "$SOURCE_DIR"/context/templates/. "$WUKONG_DIR/context/templates/" 2>/dev/null || true
    echo -e "  ${GREEN}[ok]${NC} Context templates"
fi

# 复制调度器模块 (项目级)
if [ -d "$SOURCE_DIR/scheduler" ]; then
    mkdir -p "$WUKONG_DIR/scheduler"
    cp "$SOURCE_DIR"/scheduler/*.py "$WUKONG_DIR/scheduler/"
    SCHED_COUNT=$(ls -1 "$SOURCE_DIR"/scheduler/*.py 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Scheduler ($SCHED_COUNT files) → project"

    # 同时安装到全局 ~/.wukong/scheduler/ (用户级，优先发现)
    mkdir -p "$GLOBAL_WUKONG_DIR/scheduler"
    cp "$SOURCE_DIR"/scheduler/*.py "$GLOBAL_WUKONG_DIR/scheduler/"
    echo -e "  ${GREEN}[ok]${NC} Scheduler ($SCHED_COUNT files) → global"
fi

# 复制上下文优化模块
if [ -d "$SOURCE_DIR/context" ] && ls "$SOURCE_DIR"/context/*.py 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/context/*.py "$WUKONG_DIR/context/"
    CTX_COUNT=$(ls -1 "$SOURCE_DIR"/context/*.py 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Context modules ($CTX_COUNT files)"
fi

# 初始化锚点文件
if [ ! -f "$WUKONG_DIR/context/anchors.md" ]; then
    cat > "$WUKONG_DIR/context/anchors.md" << 'EOF'
# Anchors (锚点)

Global anchors for this project.

## Decision Anchors [D]

*No anchors yet*

## Problem Anchors [P]

*No anchors yet*
EOF
    echo -e "  ${GREEN}[ok]${NC} Initialized anchors.md"
fi

echo ""

# ============================================================
# 4. 安装全局 Hooks
# ============================================================
echo -e "${BLUE}[2/3] Global Hooks${NC}"

GLOBAL_WUKONG_DIR="$HOME/.wukong"
GLOBAL_HOOKS_DIR="$GLOBAL_WUKONG_DIR/hooks"

mkdir -p "$GLOBAL_HOOKS_DIR"

# 复制 hook 脚本
if [ -d "$SOURCE_DIR/hooks" ] && ls "$SOURCE_DIR"/hooks/*.py 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/hooks/*.py "$GLOBAL_HOOKS_DIR/"
    HOOK_COUNT=$(ls -1 "$SOURCE_DIR"/hooks/*.py 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Installed hooks to ~/.wukong/hooks/ ($HOOK_COUNT files)"
else
    echo -e "  ${YELLOW}[skip]${NC} No hook scripts found"
fi

echo ""

# ============================================================
# 5. 注册 Hooks 到 Claude Code
# ============================================================
echo -e "${BLUE}[3/3] Hook Registration${NC}"

SETTINGS_FILE="$HOME/.claude/settings.json"

# 检查是否已注册
ALREADY_REGISTERED=false
if [ -f "$SETTINGS_FILE" ]; then
    if grep -q "hui-extract.py" "$SETTINGS_FILE" 2>/dev/null; then
        ALREADY_REGISTERED=true
    fi
fi

if [ "$ALREADY_REGISTERED" = true ]; then
    echo -e "  ${GREEN}[ok]${NC} Hooks already registered"
else
    echo "  Wukong uses hooks to extract knowledge before context compaction."
    echo -e "  This requires adding configuration to ${DIM}~/.claude/settings.json${NC}"
    echo ""

    # 交互确认
    read -p "  Register hooks? [Y/n] " -n 1 -r REPLY
    echo ""

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # 创建或更新 settings.json
        mkdir -p "$HOME/.claude"

        if [ ! -f "$SETTINGS_FILE" ]; then
            # 创建新文件
            cat > "$SETTINGS_FILE" << 'EOF'
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.wukong/hooks/hui-extract.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
EOF
            echo -e "  ${GREEN}[ok]${NC} Created ~/.claude/settings.json with hooks"
        else
            # 更新现有文件 - 使用 Python 进行 JSON 合并
            if command -v python3 &>/dev/null; then
                python3 << 'PYTHON_SCRIPT'
import json
import os

settings_path = os.path.expanduser("~/.claude/settings.json")

# Load existing settings
with open(settings_path, "r") as f:
    settings = json.load(f)

# Define new hook
new_hook = {
    "matcher": "auto",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.wukong/hooks/hui-extract.py",
            "timeout": 30
        }
    ]
}

# Merge hooks
if "hooks" not in settings:
    settings["hooks"] = {}

if "PreCompact" not in settings["hooks"]:
    settings["hooks"]["PreCompact"] = []

# Check for duplicates
is_duplicate = False
for hook_entry in settings["hooks"]["PreCompact"]:
    for hook in hook_entry.get("hooks", []):
        if "hui-extract.py" in hook.get("command", ""):
            is_duplicate = True
            break

if not is_duplicate:
    settings["hooks"]["PreCompact"].append(new_hook)

# Write back
with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print("ok")
PYTHON_SCRIPT
                echo -e "  ${GREEN}[ok]${NC} Updated ~/.claude/settings.json with hooks"
            else
                echo -e "  ${RED}[error]${NC} Python3 not found, cannot merge JSON"
                echo ""
                echo -e "  ${YELLOW}Please manually add this to ~/.claude/settings.json:${NC}"
                echo ""
                echo '  {'
                echo '    "hooks": {'
                echo '      "PreCompact": [{'
                echo '        "matcher": "auto",'
                echo '        "hooks": [{'
                echo '          "type": "command",'
                echo '          "command": "python3 ~/.wukong/hooks/hui-extract.py",'
                echo '          "timeout": 30'
                echo '        }]'
                echo '      }]'
                echo '    }'
                echo '  }'
            fi
        fi
    else
        echo -e "  ${DIM}Skipped hook registration${NC}"
        echo ""
        echo -e "  ${YELLOW}To enable hooks manually, add this to ~/.claude/settings.json:${NC}"
        echo ""
        echo '  {'
        echo '    "hooks": {'
        echo '      "PreCompact": [{'
        echo '        "matcher": "auto",'
        echo '        "hooks": [{'
        echo '          "type": "command",'
        echo '          "command": "python3 ~/.wukong/hooks/hui-extract.py",'
        echo '          "timeout": 30'
        echo '        }]'
        echo '      }]'
        echo '    }'
        echo '  }'
    fi
fi

# ============================================================
# 6. 完成
# ============================================================
echo ""
echo -e "${GREEN}Done!${NC}"
echo ""
echo "Installed to:"
echo -e "  ${DIM}$CLAUDE_DIR/rules/${NC}     Core rules (auto-loaded)"
echo -e "  ${DIM}$CLAUDE_DIR/skills/${NC}    Avatar skills"
echo -e "  ${DIM}$CLAUDE_DIR/commands/${NC}  Commands"
echo -e "  ${DIM}$WUKONG_DIR/${NC}           Work data"
echo -e "  ${DIM}~/.wukong/hooks/${NC}       Global hooks"
echo ""
echo -e "Start Claude Code and say: ${GREEN}/wukong${NC}"
