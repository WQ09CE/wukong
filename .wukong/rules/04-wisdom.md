# Wisdom Inheritance Protocol (知识传承协议)

## Purpose (目的)

跨任务积累和传递知识，避免重复犯错，利用成功模式。

## Notepad Structure (笔记本结构)

```
.wukong/notepads/{plan-name}/
├── requirements.md    # 需求规格书
├── design.md          # 架构设计
├── learnings.md       # 发现和经验
├── decisions.md       # 决策记录
├── issues.md          # 问题跟踪
├── review.md          # 审查结果
└── verification.md    # 验证记录
```

## Reading Wisdom (读取知识)

**BEFORE starting any significant task:**

1. Check if notepad exists:
   ```
   Glob(".wukong/notepads/{plan-name}/*.md")
   ```

2. If exists, read relevant entries:
   ```
   Read(".wukong/notepads/{plan-name}/learnings.md")
   Read(".wukong/notepads/{plan-name}/issues.md")
   ```

3. Extract applicable wisdom

4. Include in task context:
   ```markdown
   ## 继承的知识

   ### 需要遵循的模式
   - {from learnings.md}

   ### 需要避免的问题
   - {from issues.md}

   ### 已做出的决策
   - {from decisions.md}
   ```

## Writing Wisdom (记录知识)

### requirements.md (需求规格书)

由需求悟空产出:

```markdown
# 需求规格书: {Feature Name}

## 创建时间: {date}
## 状态: Draft / Review / Approved

## 背景
{context}

## 用户故事
{user stories}

## 功能需求
{functional requirements}

## 非功能需求
{non-functional requirements}

## 验收标准
{acceptance criteria}
```

### design.md (架构设计)

由架构悟空产出:

```markdown
# 架构设计: {Feature Name}

## 创建时间: {date}
## 版本: 1.0

## 设计目标
{goals}

## 系统结构
{architecture}

## 接口设计
{interfaces}

## 技术选型
{technology choices}
```

### learnings.md (发现和经验)

Record when you discover:
- 代码库的规范
- 成功的方法
- 有用的模式
- 需要注意的细节

Format:
```markdown
# 学习记录: {Plan Name}

## {Date} - {Context}
- **发现**: {what you learned}
- **示例**: {code or reference}
- **应用场景**: {when to apply}

## 代码库规范
- {convention 1}
- {convention 2}

## 有效模式
- {pattern 1}
- {pattern 2}

## 注意事项
- {gotcha 1}
- {gotcha 2}
```

### decisions.md (决策记录)

Record when you make:
- 架构选择
- 技术选型
- 权衡分析

Format:
```markdown
# 决策记录: {Plan Name}

## {Date} - {Decision Title}

### 背景
{why decision was needed}

### 选项
| Option | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

### 决定
{the selection}

### 理由
{why this choice}

### 影响
{consequences and trade-offs}
```

### issues.md (问题跟踪)

Record when you encounter:
- Bug 或错误
- 意外行为
- 阻塞问题
- 技术债

Format:
```markdown
# 问题跟踪: {Plan Name}

## 活跃问题

### ISSUE-001: {Title}
- **状态**: Open / In Progress / Resolved
- **严重度**: Critical / Major / Minor
- **症状**: {what went wrong}
- **根因**: {why it happened}
- **解决方案**: {how to fix}
- **预防措施**: {how to prevent}

## 已解决问题
...

## 技术债
- [ ] {tech debt item 1}
- [ ] {tech debt item 2}
```

### review.md (审查结果)

由审查悟空产出:

```markdown
# 代码审查: {Plan Name}

## 审查时间: {date}
## 审查者: 审查悟空

## 总体评价
{overall assessment}

## 发现的问题
{issues found}

## 改进建议
{suggestions}

## 后续跟踪
- [ ] {action item 1}
- [ ] {action item 2}
```

### verification.md (验证记录)

Record after each verification:
```markdown
# 验证记录: {Plan Name}

## {Date} - {Task/Change}

### 构建
- 状态: Pass / Fail
- 输出: {build output}

### 测试
- 单元测试: {X/Y passed}
- 集成测试: {X/Y passed}
- 覆盖率: {percentage}

### 静态分析
- mypy: {result}
- ruff: {result}
- clang-tidy: {result}

### 问题
{any issues found}

### 解决
{how resolved}
```

## Passing Wisdom to Avatars (向分身传递知识)

When delegating tasks, include relevant wisdom:

```typescript
Task(
  subagent_type="general-purpose",
  prompt=`
## 继承的知识

### 代码库规范
- 使用 snake_case 命名 Python 函数
- C++ 类使用 PascalCase
- 所有 API 返回 Pydantic 模型

### 已知问题
- FFmpeg 在某些格式下会泄漏内存
- TensorRT 8.x 与 CUDA 12 有兼容问题

### 已有决策
- 使用 ONNX Runtime 而非 TensorRT (跨平台考虑)

## 你的任务
{actual task description}
`
)
```

## Wisdom Lifecycle (知识生命周期)

```
1. 开始任务
   └─ 读取现有知识

2. 任务执行中
   └─ 记录发现

3. 任务完成
   └─ 记录学习
   └─ 记录决策
   └─ 记录问题
   └─ 保存验证结果

4. 下一个任务
   └─ 继承之前的知识
   └─ 在此基础上构建
```

## Template Files

Create notepads from templates:

```bash
# Initialize a new plan notepad
cp -r .wukong/templates/notepad .wukong/notepads/{plan-name}
```
