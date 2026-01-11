# 架构设计: {Feature Name}

## 元信息
- 创建时间: {date}
- 版本: 1.0
- 状态: Draft / Review / Approved

## 目标
{设计要达成的目标，与需求规格书对应}

## 约束
- 技术约束: {language, platform, dependencies}
- 性能约束: {latency, throughput, memory}

## 现状分析
{现有架构的情况，如果是新项目可跳过}

## 设计选项

### 选项 A: {Name}
**描述**: {one paragraph}

**优点**:
- {pro 1}
- {pro 2}

**缺点**:
- {con 1}
- {con 2}

### 选项 B: {Name}
{same structure}

## 推荐方案

**选择**: 选项 {A/B}

**理由**:
1. {reason 1}
2. {reason 2}

## 详细设计

### 系统架构
```
{architecture diagram}
```

### 模块划分
| 模块 | 职责 | 依赖 |
|------|------|------|
| {module} | {responsibility} | {dependencies} |

### 接口设计
```python
# Python interface
def function_name(param: Type) -> ReturnType:
    """Description."""
    ...
```

```cpp
// C++ interface
ReturnType function_name(ParamType param);
```

### 数据流
```
{data flow diagram}
```

### 错误处理策略
| 错误类型 | 处理方式 | 恢复策略 |
|----------|----------|----------|
| {error type} | {handling} | {recovery} |

## 技术选型
| 组件 | 选择 | 理由 |
|------|------|------|
| {component} | {technology} | {rationale} |

## 风险评估
| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| {risk} | 高/中/低 | 高/中/低 | {mitigation} |

## 实施计划

### Phase 1: {name}
- [ ] {task 1}
- [ ] {task 2}

### Phase 2: {name}
- [ ] {task 3}
- [ ] {task 4}
