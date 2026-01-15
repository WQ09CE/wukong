#!/bin/bash
#
# Wukong 安装脚本测试
# 验证 install.sh 能正确安装所有必需文件
#

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Testing Wukong installation..."
echo "Project root: $PROJECT_ROOT"
echo ""

# 创建临时测试目录
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

echo "Test directory: $TEST_DIR"
echo ""

# 运行安装脚本 (非交互模式，跳过 hook 注册)
cd "$PROJECT_ROOT"
echo "n" | ./install.sh "$TEST_DIR" > /dev/null 2>&1

# ============================================================
# 验证 .claude 目录结构
# ============================================================
echo "Checking .claude directory..."

CLAUDE_FILES=(
    ".claude/rules/00-wukong-core.md"
    ".claude/commands/wukong.md"
    ".claude/skills/jie.md"
    ".claude/skills/hui.md"
    ".claude/skills/shi.md"
    ".claude/skills/ding.md"
    ".claude/skills/explorer.md"
    ".claude/skills/architect.md"
    ".claude/skills/implementer.md"
    ".claude/skills/tester.md"
    ".claude/skills/code-reviewer.md"
    ".claude/skills/requirements-analyst.md"
    ".claude/skills/orchestration.md"
    ".claude/skills/jindouyun.md"
)

CLAUDE_PASS=0
CLAUDE_FAIL=0

for file in "${CLAUDE_FILES[@]}"; do
    if [[ -f "$TEST_DIR/$file" ]]; then
        echo -e "  ${GREEN}[ok]${NC} $file"
        ((++CLAUDE_PASS))
    else
        echo -e "  ${RED}[FAIL]${NC} $file"
        ((++CLAUDE_FAIL))
    fi
done

echo ""

# ============================================================
# 验证 .wukong 目录结构
# ============================================================
echo "Checking .wukong directory..."

WUKONG_FILES=(
    ".wukong/context/anchors.md"
)

WUKONG_DIRS=(
    ".wukong/notepads"
    ".wukong/plans"
    ".wukong/context/current"
    ".wukong/context/sessions"
    ".wukong/context/templates"
    ".wukong/templates"
)

WUKONG_PASS=0
WUKONG_FAIL=0

for file in "${WUKONG_FILES[@]}"; do
    if [[ -f "$TEST_DIR/$file" ]]; then
        echo -e "  ${GREEN}[ok]${NC} $file"
        ((++WUKONG_PASS))
    else
        echo -e "  ${RED}[FAIL]${NC} $file"
        ((++WUKONG_FAIL))
    fi
done

for dir in "${WUKONG_DIRS[@]}"; do
    if [[ -d "$TEST_DIR/$dir" ]]; then
        echo -e "  ${GREEN}[ok]${NC} $dir/"
        ((++WUKONG_PASS))
    else
        echo -e "  ${RED}[FAIL]${NC} $dir/"
        ((++WUKONG_FAIL))
    fi
done

echo ""

# ============================================================
# 验证文件内容
# ============================================================
echo "Checking file contents..."

# 核心规则必须包含关键内容
if grep -q "Wukong Core Protocol" "$TEST_DIR/.claude/rules/00-wukong-core.md" 2>/dev/null; then
    echo -e "  ${GREEN}[ok]${NC} Core rule contains expected content"
    ((CLAUDE_PASS++))
else
    echo -e "  ${RED}[FAIL]${NC} Core rule missing expected content"
    ((CLAUDE_FAIL++))
fi

# 路径引用必须使用正确的 ~/.claude/skills/ 路径
if grep -q "~/.claude/skills/" "$TEST_DIR/.claude/rules/00-wukong-core.md" 2>/dev/null; then
    echo -e "  ${GREEN}[ok]${NC} Core rule uses correct skills path"
    ((CLAUDE_PASS++))
else
    echo -e "  ${RED}[FAIL]${NC} Core rule uses wrong skills path"
    ((CLAUDE_FAIL++))
fi

# 不应该使用错误的 ~/.wukong/skills/ 路径
if grep -q "~/.wukong/skills/" "$TEST_DIR/.claude/rules/00-wukong-core.md" 2>/dev/null; then
    echo -e "  ${RED}[FAIL]${NC} Core rule contains wrong path ~/.wukong/skills/"
    ((CLAUDE_FAIL++))
else
    echo -e "  ${GREEN}[ok]${NC} Core rule does not contain wrong path"
    ((CLAUDE_PASS++))
fi

echo ""

# ============================================================
# 结果汇总
# ============================================================
TOTAL_PASS=$((CLAUDE_PASS + WUKONG_PASS))
TOTAL_FAIL=$((CLAUDE_FAIL + WUKONG_FAIL))

echo "============================================================"
echo "Results:"
echo "  .claude: $CLAUDE_PASS passed, $CLAUDE_FAIL failed"
echo "  .wukong: $WUKONG_PASS passed, $WUKONG_FAIL failed"
echo "  Total:   $TOTAL_PASS passed, $TOTAL_FAIL failed"
echo ""

if [ $TOTAL_FAIL -gt 0 ]; then
    echo -e "${RED}FAILED${NC}: Some tests did not pass"
    exit 1
else
    echo -e "${GREEN}PASSED${NC}: All installation tests passed!"
    exit 0
fi
