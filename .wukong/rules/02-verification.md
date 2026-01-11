# Verification Protocol (验证协议)

## The Golden Rule (金规)

> **分身可能说谎** - 它们经常声称完成了实际未完成的工作。
> **没有证据 = 没有完成** (NO EVIDENCE = NOT DONE)

你必须亲自验证一切。永远不要在没有证据的情况下接受声明。

---

## Evidence Levels (证据等级)

> **证据是交付的通行证** - 不同等级的证据决定了能否通过 Gate。

| Level | 名称 | 说明 | 可信度 |
|-------|------|------|--------|
| **L0** | 推测 (Speculation) | 基于经验的猜测，无任何验证 | ❌ 禁止作为结论 |
| **L1** | 引用 (Reference) | 引用代码/路径/文档，但未执行验证 | ⚠️ 可用于方向，不能交付 |
| **L2** | 本地验证 (Local Verification) | 本地命令/测试/构建验证通过 | ✅ 默认交付门槛 |
| **L3** | 集成验证 (Integration Verification) | 端到端/CI/集成测试验证 | ✅✅ 关键路径建议 |

### 证据等级示例

```
L0 (禁止): "这个函数应该能处理空值"
L1 (不足): "在 utils.py:42 有空值处理" (但没运行过)
L2 (合格): "pytest test_utils.py::test_null_handling 通过"
L3 (优秀): "CI pipeline 全绿，含集成测试"
```

---

## Track Verification Gates (轨道验证门槛)

> **每条轨道有最低验证要求** - 未达到门槛不能标记 Done。

| Track | 最低门槛 | 额外要求 | 说明 |
|-------|----------|----------|------|
| **Fix** | L2 | + 复现用例 + 回归测试 | 必须证明 bug 已修复且不会复发 |
| **Feature** | L2 | + 覆盖 AC 的测试 | 核心流程建议 L3 |
| **Refactor** | L2 | + 行为不变证明 | 必须有对齐基准（前后输出一致） |
| **Direct** | L1 | - | 简单任务可降级，但仍需引用证据 |

### Gate 检查清单

```
Feature Gate ✅:
□ 所有 AC 有对应测试 (L2+)
□ 核心路径有集成测试 (L3 建议)
□ 无新增类型错误/lint 警告
□ 构建通过

Fix Gate ✅:
□ 有复现用例（证明之前会失败）
□ 修复后用例通过 (L2)
□ 回归测试通过
□ 无其他测试被破坏

Refactor Gate ✅:
□ 有行为基准（修改前的输出）
□ 修改后输出与基准一致 (L2)
□ 无功能变化
□ 代码质量提升（可量化）
```

---

## Delivery Report Template (交付报告模板)

> **每次交付必须附带交付报告** - 本体或舌分身生成。

```markdown
# 交付报告: {Task Name}

## 基本信息
- **轨道**: Feature / Fix / Refactor / Direct
- **证据等级**: L2 / L3
- **日期**: {date}

## AC Checklist
- [x] AC-1: {描述} → 证据: `pytest tests/test_x.py::test_ac1 ✅`
- [x] AC-2: {描述} → 证据: `{command} ✅`
- [ ] AC-3: {描述} → ⚠️ 未完成，原因: {reason}

## 验证命令与输出

### 构建验证
```bash
$ cmake --build build
# 输出: Build finished successfully
```

### 测试验证
```bash
$ pytest -v tests/
# 输出: 15 passed, 0 failed
```

### 类型检查 (如适用)
```bash
$ mypy src/
# 输出: Success: no issues found
```

## 风险点
- {risk 1}: {mitigation}
- {risk 2}: {mitigation}

## 回滚方式
```bash
# 如需回滚:
git revert {commit_hash}
# 或手动步骤:
1. {step 1}
2. {step 2}
```

## 遗留问题 (如有)
- [ ] {issue 1} - 后续处理
```

## 批次完成验证 (Batch Completion Verification)

> **每个并行批次完成后，必须立即验证，才能开始下一批次。**

### 为什么需要批次验证？

```
❌ 最后才验证 (问题积累):
批次1 → 批次2 → 批次3 → 最终验证 → 发现批次1有问题 → 大量返工

✅ 批次验证 (尽早发现):
批次1 → 验证 ✓ → 批次2 → 验证 ✓ → 批次3 → 验证 ✓ → 完成
              ↓
           发现问题 → 立即修复 → 继续
```

### 批次验证检查清单

每个批次完成后，本体必须执行：

```
□ 1. 文件存在检查
   → Glob 确认所有预期文件已创建
   → Read 确认文件内容非空

□ 2. 语法检查
   → Python: python -m py_compile <files>
   → C++: cmake --build (syntax only)

□ 3. 导入/编译检查
   → Python: python -c "import module"
   → C++: 完整编译

□ 4. 快速功能验证
   → 核心类可实例化
   → 关键方法可调用
```

### 批次验证脚本模板

```bash
# Python 项目批次验证
for file in src/*.py; do
    python -m py_compile "$file" || echo "FAIL: $file"
done

# 导入检查
python -c "
from src.credentials import Credentials
from src.sanitizer import Sanitizer
print('All imports OK')
"
```

### 验证失败处理

```
批次验证失败:
├── 1. 停止后续批次
├── 2. 定位失败的模块
├── 3. 召唤原分身修复（或新分身）
├── 4. 重新验证
└── 5. 通过后继续下一批次
```

## Mandatory Verification Steps

### For C++ Projects

```
□ 1. FILES EXIST
   → Glob("**/path/to/file.*")
   → Read files to confirm content

□ 2. BUILD PASSES
   → cmake --build build
   → No compilation errors
   → No linker errors

□ 3. STATIC ANALYSIS CLEAN
   → clang-tidy (if configured)
   → No warnings with -Wall -Wextra

□ 4. TESTS PASS
   → ctest --test-dir build --output-on-failure
   → All tests green

□ 5. SANITIZERS CLEAN (if applicable)
   → AddressSanitizer: no memory errors
   → UndefinedBehaviorSanitizer: no UB
   → ThreadSanitizer: no data races

□ 6. VALGRIND CLEAN (if applicable)
   → No memory leaks
   → No invalid accesses
```

### For Python Projects

```
□ 1. FILES EXIST
   → Glob("**/path/to/file.py")
   → Read files to confirm content

□ 2. SYNTAX VALID
   → python -m py_compile <file>
   → No syntax errors

□ 3. TYPE CHECK PASSES
   → mypy --strict (or configured settings)
   → No type errors

□ 4. LINT PASSES
   → ruff check .
   → No lint errors

□ 5. TESTS PASS
   → pytest -v --tb=short
   → All tests green

□ 6. COVERAGE ADEQUATE
   → pytest --cov --cov-report=term-missing
   → Coverage meets threshold
```

### For FastAPI Projects

```
□ All Python checks above PLUS:

□ 7. API STARTS
   → uvicorn main:app --host 0.0.0.0 --port 8000
   → No startup errors

□ 8. OPENAPI VALID
   → /docs loads correctly
   → /openapi.json is valid

□ 9. API TESTS PASS
   → pytest tests/api/ -v
   → All endpoints tested
```

## Evidence Requirements

| Claim | Required Evidence |
|-------|-------------------|
| "File created" | Glob shows file, Read shows content |
| "Build passes" | cmake/make output shows success |
| "Tests pass" | pytest/ctest output shows all green |
| "No type errors" | mypy output clean |
| "Bug fixed" | Before/after behavior demonstrated |
| "Feature complete" | All acceptance criteria verified |

## Verification Commands Quick Reference

### C++

```bash
# Configure
cmake -B build -DCMAKE_BUILD_TYPE=Debug \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# Build
cmake --build build -j$(nproc)

# Test
ctest --test-dir build --output-on-failure

# Static analysis
clang-tidy -p build src/*.cpp

# Memory check
valgrind --leak-check=full ./build/tests/unit_tests
```

### Python

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Type check
mypy src/

# Lint
ruff check .

# Format check
ruff format --check .

# Test with coverage
pytest -v --cov=src --cov-report=term-missing

# All checks
ruff check . && mypy src/ && pytest -v
```

### FastAPI

```bash
# Start server (test)
uvicorn app.main:app --reload

# Run API tests
pytest tests/api/ -v

# Check OpenAPI
curl http://localhost:8000/openapi.json | python -m json.tool
```

## Verification Outcomes

### All Checks Pass
```
✓ 验证完成
- Files: [已验证的文件列表]
- Build: 成功
- Tests: [X/X 通过]
- Static Analysis: 无警告
- 继续下一个任务
```

### Any Check Fails
```
✗ 验证失败
- 失败检查: [哪个步骤]
- 错误: [实际错误信息]
- 下一步: [修复/重试/升级]
```

## Failure Escalation (失败升级)

```
第1次失败 → 修复后重试
第2次失败 → 分析根本原因
第3次失败 → 停止并升级

升级步骤:
1. 记录所有尝试
2. 捕获错误信息
3. 识别可能原因
4. 向用户请求指导
```

## Recording Results

After each verification cycle, record in `.wukong/notepads/{plan}/verification.md`:

```markdown
## 验证: {date} - {task}

### 执行的检查
- [ ] 文件存在
- [ ] 构建通过
- [ ] 静态分析通过
- [ ] 测试通过
- [ ] 无回归

### 结果
{每个检查的实际输出}

### 发现的问题
{发现的任何问题}

### 解决方案
{问题如何解决}
```

## Anti-Patterns (禁忌)

**NEVER (绝不):**
- 跳过验证"节省时间"
- 不检查就信任分身的声明
- 没有证据就标记任务完成
- 忽略失败的测试
- 用 `#pragma warning disable` 或 `# type: ignore` 压制错误
- 不确定时声称成功

**ALWAYS (始终):**
- 用实际命令验证每个声明
- 捕获并记录输出
- 在继续之前解决失败
- 对已验证和假设的内容保持诚实
