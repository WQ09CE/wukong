# Verification Protocol (验证协议)

## The Golden Rule (金规)

> **分身可能说谎** - 它们经常声称完成了实际未完成的工作。

你必须亲自验证一切。永远不要在没有证据的情况下接受声明。

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
