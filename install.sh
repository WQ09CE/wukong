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
SOURCE_DIR="$(dirname "$0")/.wukong"

if [ ! -d ".wukong" ]; then
    echo "Error: Run this script from the root of the wukong repository."
    echo "Usage: ./install.sh <target-project-path>"
    exit 1
fi

TARGET_DIR="$1"

if [ -z "$TARGET_DIR" ]; then
    echo -e "No target directory specified. Installing to current directory: ${GREEN}$PROJECT_ROOT${NC}"
    TARGET_DIR="$PROJECT_ROOT"
fi

mkdir -p "$TARGET_DIR/.claude/rules"
mkdir -p "$TARGET_DIR/.claude/commands"
mkdir -p "$TARGET_DIR/.wukong"

echo -e "Installing Wukong to ${GREEN}$TARGET_DIR${NC}..."

cp -R .wukong/* "$TARGET_DIR/.wukong/"

echo "Activating Wukong Rules..."
cp .wukong/rules/*.md "$TARGET_DIR/.claude/rules/"

echo "Activating Wukong Commands..."
cp .wukong/commands/*.md "$TARGET_DIR/.claude/commands/"

mkdir -p "$TARGET_DIR/.wukong/notepads"
mkdir -p "$TARGET_DIR/.wukong/plans"

echo -e "${GREEN}✅ Wukong Protocol successfully installed!${NC}"
echo -e "Structure created:"
echo -e "  - $TARGET_DIR/.wukong/"
echo -e "  - $TARGET_DIR/.claude/rules/"
echo ""
echo -e "Start Claude Code and say: 'Hello Wukong'"
