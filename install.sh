#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🐵 Wukong Installer${NC}"

PROJECT_ROOT=$(pwd)
SOURCE_DIR=""

# 确定源目录
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

# 智能检测: 如果 TARGET_DIR 已经是 .claude 目录，直接使用
# 否则在 TARGET_DIR 下创建 .claude/
if [[ "$TARGET_DIR" == *".claude" ]] || [[ "$TARGET_DIR" == *".claude/" ]]; then
    CLAUDE_DIR="$TARGET_DIR"
    WUKONG_DIR="$(dirname "$TARGET_DIR")/.wukong"
else
    CLAUDE_DIR="$TARGET_DIR/.claude"
    WUKONG_DIR="$TARGET_DIR/.wukong"
fi

# 创建目标目录结构
mkdir -p "$CLAUDE_DIR/rules"
mkdir -p "$CLAUDE_DIR/rules-extended"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/skills"

echo -e "Installing Wukong to ${GREEN}$TARGET_DIR${NC}..."

# ============================================================
# 核心规则: rules-lite/ → rules/ (启动时加载)
# ============================================================
echo "Activating Wukong Core Rules (lite)..."
if [ -d "$SOURCE_DIR/rules-lite" ]; then
    cp "$SOURCE_DIR"/rules-lite/*.md "$CLAUDE_DIR/rules/"
else
    # 兼容旧版：如果没有 rules-lite，只复制核心文件
    cp "$SOURCE_DIR"/rules/00-wukong-core.md "$CLAUDE_DIR/rules/"
fi

# ============================================================
# 扩展规则: rules/ → rules-extended/ (按需加载)
# 单一真相源: 从 rules/ 复制，自动去掉序号前缀
# ============================================================
echo "Installing Extended Rules (on-demand, from single source of truth)..."
if [ -d "$SOURCE_DIR/rules" ]; then
    for file in "$SOURCE_DIR"/rules/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            # 去掉序号前缀: "01-task-orchestration.md" → "task-orchestration.md"
            # 但保留 "00-wukong-core.md" → "wukong-core.md"
            newname=$(echo "$filename" | sed 's/^[0-9]*-//')
            cp "$file" "$CLAUDE_DIR/rules-extended/$newname"
        fi
    done
fi

# ============================================================
# 命令和技能
# ============================================================
echo "Activating Wukong Commands..."
cp "$SOURCE_DIR"/commands/*.md "$CLAUDE_DIR/commands/"

echo "Activating Wukong Skills..."
cp "$SOURCE_DIR"/skills/*.md "$CLAUDE_DIR/skills/"

# ============================================================
# 工作目录和模板
# ============================================================
mkdir -p "$WUKONG_DIR/notepads"
mkdir -p "$WUKONG_DIR/plans"
mkdir -p "$WUKONG_DIR/context/current"
mkdir -p "$WUKONG_DIR/context/sessions"

# 复制模板文件 (如果存在)
if [ -d "$SOURCE_DIR/templates" ]; then
    mkdir -p "$WUKONG_DIR/templates"
    cp -R "$SOURCE_DIR"/templates/. "$WUKONG_DIR/templates/"
fi

# 复制上下文模板 (如果存在)
if [ -d "$SOURCE_DIR/context/templates" ]; then
    mkdir -p "$WUKONG_DIR/context/templates"
    cp -R "$SOURCE_DIR"/context/templates/. "$WUKONG_DIR/context/templates/"
fi

# 初始化锚点文件
if [ ! -f "$WUKONG_DIR/context/anchors.md" ]; then
    echo "# Anchors (锚点)" > "$WUKONG_DIR/context/anchors.md"
    echo "" >> "$WUKONG_DIR/context/anchors.md"
    echo "Global anchors for this project." >> "$WUKONG_DIR/context/anchors.md"
fi

# ============================================================
# 完成
# ============================================================
echo -e "${GREEN}✅ Wukong Protocol successfully installed!${NC}"
echo -e "Structure created:"
echo -e "  - $CLAUDE_DIR/rules/          (精简核心规则 - 启动加载)"
echo -e "  - $CLAUDE_DIR/rules-extended/ (完整规则 - 按需加载, 单一真相源)"
echo -e "  - $CLAUDE_DIR/skills/         (分身技能)"
echo -e "  - $CLAUDE_DIR/commands/       (命令)"
echo -e "  - $WUKONG_DIR/                (工作数据)"
echo ""
echo -e "${YELLOW}💡 Tip: rules-extended/ 现在直接从 rules/ 复制，保证内容完整一致${NC}"
echo ""
echo -e "Start Claude Code and say: 'Hello Wukong'"
