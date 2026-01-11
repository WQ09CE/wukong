# 验证记录: {Plan Name}

## 验证历史

### {Date} - {Task/Change}

#### 构建
- **状态**: Pass / Fail
- **命令**: `cmake --build build` / `python -m build`
- **输出**:
  ```
  {build output}
  ```

#### 测试
- **单元测试**: {X/Y passed}
- **集成测试**: {X/Y passed}
- **覆盖率**: {percentage}
- **命令**: `pytest -v` / `ctest`
- **输出**:
  ```
  {test output}
  ```

#### 静态分析
- **mypy**: Pass / Fail
- **ruff**: Pass / Fail
- **clang-tidy**: Pass / Fail

#### 问题
{any issues found}

#### 解决
{how resolved}

---

### {Date} - {Task/Change}
{same structure}
