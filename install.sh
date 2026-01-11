#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' 

echo -e "${BLUE}🐵 Wukong Installer${NC}"

PROJECT_ROOT=$(pwd)
CLAUDE_DIR="$PROJECT_ROOT/.claude"
RULES_DIR="$CLAUDE_DIR/rules"
WUKONG_DIR="$PROJECT_ROOT/.wukong"
SOURCE_DIR=""

if [ -d "$PROJECT_ROOT/.wukong" ]; then
    SOURCE_DIR="$PROJECT_ROOT/.wukong"
else
    TEMP_DIR=$(mktemp -d)
    trap 'rm -rf "$TEMP_DIR"' EXIT

    echo "Fetching Wukong rules..."
    curl -fsSL "https://github.com/WQ09CE/wukong/archive/refs/heads/main.tar.gz" | tar -xz -C "$TEMP_DIR"
    SOURCE_DIR="$TEMP_DIR/wukong-main/.wukong"

    if [ ! -d "$SOURCE_DIR" ]; then
        echo "Error: Failed to fetch Wukong rules from GitHub."
        echo "Usage: ./install.sh <target-project-path>"
        exit 1
    fi
fi

TARGET_DIR="$1"

if [ -z "$TARGET_DIR" ]; then
    echo -e "No target directory specified. Installing to current directory: ${GREEN}$PROJECT_ROOT${NC}"
    TARGET_DIR="$PROJECT_ROOT"
fi

mkdir -p "$TARGET_DIR/.claude/rules"
mkdir -p "$TARGET_DIR/.claude/rules-extended"
mkdir -p "$TARGET_DIR/.claude/commands"
mkdir -p "$TARGET_DIR/.claude/skills"

echo -e "Installing Wukong to ${GREEN}$TARGET_DIR${NC}..."

# 复制精简规则到 .claude/rules (启动时加载)
echo "Activating Wukong Core Rules (lite)..."
if [ -d "$SOURCE_DIR/rules-lite" ]; then
    cp "$SOURCE_DIR"/rules-lite/*.md "$TARGET_DIR/.claude/rules/"
else
    # 兼容旧版：如果没有 rules-lite，使用原规则
    cp "$SOURCE_DIR"/rules/*.md "$TARGET_DIR/.claude/rules/"
fi

# 复制扩展规则到 .claude/rules-extended (按需加载)
echo "Installing Extended Rules (on-demand)..."
if [ -d "$SOURCE_DIR/rules-extended" ]; then
    cp "$SOURCE_DIR"/rules-extended/*.md "$TARGET_DIR/.claude/rules-extended/"
fi

echo "Activating Wukong Commands..."
cp "$SOURCE_DIR"/commands/*.md "$TARGET_DIR/.claude/commands/"

echo "Activating Wukong Skills..."
cp "$SOURCE_DIR"/skills/*.md "$TARGET_DIR/.claude/skills/"

# 只创建必要的工作目录 (笔记本、计划、上下文、模板)
mkdir -p "$TARGET_DIR/.wukong/notepads"
mkdir -p "$TARGET_DIR/.wukong/plans"
mkdir -p "$TARGET_DIR/.wukong/context/current"
mkdir -p "$TARGET_DIR/.wukong/context/sessions"

# 复制模板文件 (如果存在)
if [ -d "$SOURCE_DIR/templates" ]; then
    mkdir -p "$TARGET_DIR/.wukong/templates"
    cp -R "$SOURCE_DIR"/templates/. "$TARGET_DIR/.wukong/templates/"
fi

# 复制上下文模板 (如果存在)
if [ -d "$SOURCE_DIR/context/templates" ]; then
    mkdir -p "$TARGET_DIR/.wukong/context/templates"
    cp -R "$SOURCE_DIR"/context/templates/. "$TARGET_DIR/.wukong/context/templates/"
fi

# 初始化锚点文件
if [ ! -f "$TARGET_DIR/.wukong/context/anchors.md" ]; then
    echo "# Anchors (锚点)" > "$TARGET_DIR/.wukong/context/anchors.md"
    echo "" >> "$TARGET_DIR/.wukong/context/anchors.md"
    echo "Global anchors for this project." >> "$TARGET_DIR/.wukong/context/anchors.md"
fi

echo -e "${GREEN}✅ Wukong Protocol successfully installed!${NC}"
echo -e "Structure created:"
echo -e "  - $TARGET_DIR/.claude/rules/          (精简核心规则 - 启动加载)"
echo -e "  - $TARGET_DIR/.claude/rules-extended/ (扩展规则 - 按需加载)"
echo -e "  - $TARGET_DIR/.claude/skills/         (分身技能)"
echo -e "  - $TARGET_DIR/.claude/commands/       (命令)"
echo -e "  - $TARGET_DIR/.wukong/                (工作数据)"
echo ""
echo -e "Start Claude Code and say: 'Hello Wukong'"
