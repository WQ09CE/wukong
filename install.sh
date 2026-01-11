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
mkdir -p "$TARGET_DIR/.claude/commands"
mkdir -p "$TARGET_DIR/.claude/skills"
mkdir -p "$TARGET_DIR/.wukong"

echo -e "Installing Wukong to ${GREEN}$TARGET_DIR${NC}..."

cp -R "$SOURCE_DIR"/. "$TARGET_DIR/.wukong/"

echo "Activating Wukong Rules..."
cp "$SOURCE_DIR"/rules/*.md "$TARGET_DIR/.claude/rules/"

echo "Activating Wukong Commands..."
cp "$SOURCE_DIR"/commands/*.md "$TARGET_DIR/.claude/commands/"

echo "Activating Wukong Skills..."
cp "$SOURCE_DIR"/skills/*.md "$TARGET_DIR/.claude/skills/"

mkdir -p "$TARGET_DIR/.wukong/notepads"
mkdir -p "$TARGET_DIR/.wukong/plans"

echo -e "${GREEN}✅ Wukong Protocol successfully installed!${NC}"
echo -e "Structure created:"
echo -e "  - $TARGET_DIR/.wukong/"
echo -e "  - $TARGET_DIR/.claude/rules/"
echo -e "  - $TARGET_DIR/.claude/skills/"
echo -e "  - $TARGET_DIR/.claude/commands/"
echo ""
echo -e "Start Claude Code and say: 'Hello Wukong'"
