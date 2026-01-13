# 定 (Ding) - 可复现验证模块

> **定**：心止一处，不动不乱。检查结果是否可复现、可运行。

## 职责

定模块负责验证分身输出的可复现性：
- 证据等级评估 (L0-L3)
- 构建/测试验证
- 批次完成验证

## 触发时机

```
分身输出 ──→ 戒 ──→ 定 ──→ 慧 ──→ 识
                   ↑
                 当前位置
```

## 金规

> **分身可能说谎** - 没有证据 = 没有完成 (NO EVIDENCE = NOT DONE)

## 证据等级

| Level | 名称 | 说明 | 可信度 |
|-------|------|------|--------|
| **L0** | 推测 | 基于经验的猜测 | ❌ 不可信 |
| **L1** | 引用 | 引用但未验证 | ⚠️ 条件可信 |
| **L2** | 本地验证 | 本地命令验证 | ✅ 默认可信 |
| **L3** | 集成验证 | 端到端验证 | ✅✅ 完全可信 |

### L0 危险信号 (必须拦截)

```
"应该可以..." / "大概能..." → 推测
"我觉得..." / "我认为..." → 主观判断
"一般来说..." / "通常..." → 泛化假设
"显然..." / "当然..." → 隐藏假设
"没有问题" / "应该没事" → 乐观偏见
```

### 健康信号 (可通过)

```
"根据 {path}:{line}，..." → 有证据引用
"执行 {command} 输出 {result}" → 有验证
"测试 {test_name} 通过" → 有测试
```

## 轨道门槛

| 轨道 | 最低门槛 | 额外要求 |
|------|----------|----------|
| **Fix** | L2 | + 复现用例 + 回归测试 |
| **Feature** | L2 | + AC 测试覆盖 |
| **Refactor** | L2 | + 行为不变证明 |
| **Direct** | L1 | 简单任务可降级 |

## 验证命令

### Python 项目

```bash
# 语法检查
python -m py_compile <file>

# 类型检查
mypy src/

# Lint
ruff check .

# 测试
pytest -v --tb=short

# 覆盖率
pytest --cov=src --cov-report=term-missing

# 全部检查
ruff check . && mypy src/ && pytest -v
```

### C++ 项目

```bash
# 配置
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# 构建
cmake --build build -j$(nproc)

# 测试
ctest --test-dir build --output-on-failure

# 静态分析
clang-tidy -p build src/*.cpp

# 内存检查
valgrind --leak-check=full ./build/tests/unit_tests
```

### FastAPI 项目

```bash
# 启动测试
uvicorn main:app --host 0.0.0.0 --port 8000

# API 测试
pytest tests/api/ -v

# OpenAPI 验证
curl http://localhost:8000/openapi.json | python -m json.tool
```

## 批次验证

> 每个并行批次完成后，必须立即验证，才能开始下一批次。

### 为什么需要批次验证？

```
❌ 最后才验证 (问题积累):
批次1 → 批次2 → 批次3 → 最终验证 → 发现批次1有问题 → 大量返工

✅ 批次验证 (尽早发现):
批次1 → 验证 ✓ → 批次2 → 验证 ✓ → 批次3 → 验证 ✓ → 完成
```

### 批次验证检查

```
□ 1. 文件存在检查
   → Glob 确认所有预期文件已创建
   → Read 确认文件内容非空

□ 2. 语法检查
   → python -m py_compile / cmake syntax

□ 3. 导入/编译检查
   → python -c "import module" / 完整编译

□ 4. 快速功能验证
   → 核心类可实例化
   → 关键方法可调用
```

### 验证失败处理

```
批次验证失败:
├── 1. 停止后续批次
├── 2. 定位失败的模块
├── 3. 召唤原分身修复
├── 4. 重新验证
└── 5. 通过后继续下一批次
```

## 证据要求

| 声明 | 要求证据 |
|------|----------|
| "File created" | Glob + Read 确认 |
| "Build passes" | cmake/make 输出 |
| "Tests pass" | pytest/ctest 输出 |
| "No type errors" | mypy 输出 |
| "Bug fixed" | Before/After 对比 |
| "Feature complete" | AC 验证清单 |

## 失败升级

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

## 输出格式

```markdown
## 定关检查

**证据等级**: L{0-3}
**状态**: ✅ 通过 / ❌ 不通过

### 验证执行
| 检查项 | 命令 | 结果 |
|--------|------|------|
| 构建 | `cmake --build build` | ✅ |
| 测试 | `pytest -v` | ✅ 15/15 |
| 类型 | `mypy src/` | ✅ |

### 证据记录
```bash
$ pytest -v tests/
# 输出: 15 passed, 0 failed
```

### 问题 (如有)
| 检查 | 错误 | 下一步 |
|------|------|--------|
| {检查项} | {错误信息} | {修复/重试/升级} |
```

## 与其他模块关系

```
戒 (规则) ──→ 定 (复现) ──→ 慧 (反思) ──→ 识 (存储)
              │
              └── L0/L1 不充分则补充验证
```
