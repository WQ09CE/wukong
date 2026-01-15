# Orchestration - Track Orchestration Detailed Guide (轨道编排详细指南)

> This file defines detailed DAGs for workflow tracks and domain-specific patterns.
>
> **Related References:**
> - Summoning Protocol (4-part declaration + 7-section prompt) -> `summoning.md`
> - Cost-Based Routing -> `~/.wukong/scheduler/scheduler.py`
> - Parallel Execution -> `jindouyun.md`
> - Introspection Protocol -> `hui.md`
> - Todo Tracking -> `00-wukong-core.md`

---

## Domain-Specific Patterns

### C++ Projects

```markdown
## Build & Test Commands
- Configure: cmake -B build -DCMAKE_BUILD_TYPE=Release
- Build: cmake --build build -j$(nproc)
- Test: ctest --test-dir build --output-on-failure
- Coverage: gcov/lcov

## Code Patterns
- RAII for resource management
- Smart pointers (unique_ptr, shared_ptr)
- Exception safety guarantees
- const correctness
```

### Python Projects

```markdown
## Build & Test Commands
- Install: pip install -e ".[dev]"
- Test: pytest -v --cov
- Lint: ruff check . && mypy .
- Format: ruff format .

## Code Patterns
- Type hints (Python 3.10+)
- Pydantic for data validation
- async/await for I/O
- Dependency injection
```

### FastAPI Projects

```markdown
## Structure
src/
├── api/           # Route handlers
├── core/          # Config, security
├── models/        # Pydantic models
├── services/      # Business logic
└── repositories/  # Data access

## Patterns
- Dependency injection via Depends
- Async database operations
- Response models for validation
- OpenAPI documentation
```

### Video Processing

```markdown
## Libraries
- FFmpeg: transcoding, muxing
- GStreamer: pipeline processing
- OpenCV: frame analysis
- VAAPI/NVENC: hardware acceleration

## Patterns
- Zero-copy frame passing
- Pipeline parallelism
- Memory pool management
- Frame rate control
```

### AI Inference

```markdown
## Runtimes
- ONNX Runtime: cross-platform
- TensorRT: NVIDIA optimization
- OpenVINO: Intel optimization

## Patterns
- Batching for throughput
- Async inference
- Model versioning
- Input validation
```

---

## Workflow Tracks - Default DAG (轨道默认依赖图)

> **Parallel must be "predictable"** - Each track has a fixed default DAG to avoid "everyone working together but fighting each other".

---

### Track A: Feature Development (功能开发)

**Trigger**: "Add", "Create", "New", "Implement feature"

**Default DAG**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Requirements + Exploration (parallel)                  │
│  ┌─────────┐    ┌─────────┐                                      │
│  │ 👂 Ear   │    │ 👁 Eye   │  <- Can parallel, no dependencies   │
│  │ Req.     │    │ Explore  │                                      │
│  │ Clarify  │    │ Current  │                                      │
│  └────┬────┘    └────┬────┘                                      │
│       │              │                                            │
│       └──────┬───────┘                                            │
│              ▼                                                    │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: Design (serial)                                        │
│              ┌─────────┐                                          │
│              │ 🧠 Mind  │  <- Depends on Phase 1 output           │
│              │ Arch.    │                                          │
│              │ Design   │                                          │
│              └────┬────┘                                          │
│                   ▼                                               │
├─────────────────────────────────────────────────────────────────┤
│  ⏰ [Alaya T2] Inject after design freeze                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Query Alaya:                                                  │ │
│  │ - Extract tech choices -> retrieve related ADR [D type]      │ │
│  │ - Inject: historical decisions, known tradeoffs, rollbacks   │ │
│  │ - Word limit: ≤400 chars                                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  See: .wukong/skills/alaya-injection.md                          │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: Implementation (serial)                                │
│              ┌─────────┐                                          │
│              │ ⚔️ Body  │  <- Depends on design                   │
│              │ Code     │                                          │
│              │ Impl.    │                                          │
│              └────┬────┘                                          │
│                   ▼                                               │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: Verification + Review (parallel)                       │
│  ┌─────────┐    ┌─────────┐                                      │
│  │ 👅 Tongue│    │ 👃 Nose  │  <- Can parallel, no dependencies   │
│  │ Write    │    │ Code     │                                      │
│  │ Tests    │    │ Review   │                                      │
│  └────┬────┘    └────┬────┘                                      │
│       │              │                                            │
│       └──────┬───────┘                                            │
│              ▼                                                    │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5: Convergence (body)                                     │
│              ┌─────────┐                                          │
│              │ 🐵 Body  │  <- Summarize, verify, deliver report   │
│              │ Gate     │                                          │
│              │ Verify   │                                          │
│              └─────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

**Gate Requirement**: L2 + AC test coverage (L3 recommended for core flows)

---

## Eight Consciousness Verification Pipeline (八识验证流水线)

> **Six Roots Execute -> Manas Filter -> Sila/Samadhi/Prajna Verify -> Alaya Store**
> All tracks must go through this pipeline before Phase 5 convergence.

### Pipeline Architecture

```
Six Root Avatar Output (Eye/Ear/Nose/Tongue/Body/Mind)
          │
          ▼
┌─────────────────────────────────────────┐
│      Manas (Manas Filter)               │
│  ┌───────────────────────────────────┐  │
│  │ Check hidden assumptions:         │  │
│  │ □ Assumed conditions user didn't  │  │
│  │   mention?                        │  │
│  │ □ Assumed code behavior? (verify) │  │
│  │ □ Unverified performance          │  │
│  │   assumptions?                    │  │
│  │ □ Potential biases?               │  │
│  └───────────────────────────────────┘  │
│  Output: Assumption list + bias markers │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│           Sila Gate (戒关)              │
│  ┌───────────────────────────────────┐  │
│  │ Rule compliance check:            │  │
│  │ □ Output Contract complete?       │  │
│  │ □ Do/Don't boundaries respected?  │  │
│  │ □ Territory protocol respected?   │  │
│  │ □ Security requirements met?      │  │
│  └───────────────────────────────────┘  │
│  Pass -> Continue | Violate -> Return   │
│  to Six Roots for correction            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│           Samadhi Gate (定关)           │
│  ┌───────────────────────────────────┐  │
│  │ Reproducible/runnable check:      │  │
│  │ □ Executable verification         │  │
│  │   command?                        │  │
│  │ □ Locally reproducible?           │  │
│  │ □ Tests pass?                     │  │
│  │ □ Build succeeds?                 │  │
│  └───────────────────────────────────┘  │
│  Reach L2 -> Continue | Not -> Add      │
│  verification                           │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│           Prajna Gate (慧关)            │
│  ┌───────────────────────────────────┐  │
│  │ Verify & abstract check:          │  │
│  │ □ All AC satisfied?               │  │
│  │ □ Extractable patterns?           │  │
│  │ □ Need to create ADR anchor?      │  │
│  │ □ Experience worth recording?     │  │
│  └───────────────────────────────────┘  │
│  Reach L3 -> Continue | L2 enough ->    │
│  Mark passed                            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        Alaya Store (阿赖耶识)           │
│  ┌───────────────────────────────────┐  │
│  │ Karma accumulation:               │  │
│  │                                   │  │
│  │ Positive Karma (good seeds):      │  │
│  │   - Success -> notepads/learnings │  │
│  │   - Decision anchors ->           │  │
│  │     context/anchors               │  │
│  │   - Reusable patterns -> skills/  │  │
│  │                                   │  │
│  │ Negative Karma (debt):            │  │
│  │   - Tech debt -> issues.md        │  │
│  │   - Known risks -> risk-hotspots  │  │
│  │   - Temporary solutions ->        │  │
│  │     tech-debt-tracker             │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Pipeline Trigger Timing

| Track | Trigger Position | Verification Depth |
|-------|------------------|-------------------|
| Feature (Track A) | Between Phase 4->5 | Full pipeline |
| Fix (Track B) | Between Phase 3->4 | Focus Sila + Samadhi |
| Refactor (Track C) | Between Phase 4->5 | Focus behavior unchanged |
| Direct (Track D) | After avatar returns | Lightweight check |

### Pipeline Failure Handling

```
On verification failure:
├── Manas marks assumption -> Return to Six Roots, require assumption verification
├── Sila Gate violation -> Return to Six Roots, fix output format/boundaries
├── Samadhi Gate failure -> Return to Body avatar, add verification commands
└── Prajna Gate not met -> Body decides whether to accept L2 downgrade
```

### Pipeline Status Definitions

| Status | Meaning | Next Action |
|--------|---------|-------------|
| **PASS** | Pass current gate | Proceed to next gate |
| **REJECT** | Serious violation | Return to avatar for redo, pipeline terminates |
| **RETRY** | Fixable issue | Avatar fixes then retry current gate |
| **SKIP** | Can skip | Proceed to next gate directly |
| **FEEDBACK** | Needs feedback | Generate rule patch suggestion, continue flow |

### State Transition Diagram

```
                    ┌──────────────────────────────────────────────────────┐
                    │                                                      │
                    ▼                                                      │
Avatar Output ──→ [Sila] ──→ PASS ──→ [Samadhi] ──→ PASS ──→ [Prajna] ──→ PASS ──→ [Alaya] ──→ Done
                │                   │                   │
                │ REJECT            │ RETRY             │ FEEDBACK
                ▼                   ▼                   ▼
           Return for redo     Fix then retry     Rule patch suggestion
                │                   │                   │
                └───────────────────┴───────────────────┘
                        Re-enter pipeline
```

### Progressive Gate Rules

#### 1. Sila Gate → Samadhi Gate

| Sila Result | Enter Samadhi? | Note |
|-------------|----------------|------|
| **PASS** | ✅ YES | Normal flow |
| **REJECT** | ❌ NO | Return for redo, don't enter Samadhi |

**Key**: Sila REJECT = Pipeline terminates, must redo

```
Sila checklist:
├── Contract completeness → Missing required fields → REJECT
├── Do/Don't boundaries → Boundary violation → REJECT
└── Security check → Dangerous operations/sensitive info → REJECT
```

#### 2. Samadhi Gate → Prajna Gate

| Samadhi Result | Evidence Level | Enter Prajna? | Note |
|----------------|----------------|---------------|------|
| **PASS + L2/L3** | High | ✅ YES | Normal flow |
| **PASS + L1** | Medium | ⚠️ Conditional | Simple tasks can skip Prajna |
| **PASS + L0** | Low | ❌ NO | Return to add evidence |
| **RETRY** | - | ❌ NO | Fix then retry Samadhi |

**Conditions to skip Prajna** (any one allows skip):
- Track D (Direct) simple tasks
- Eye/Ear/Nose exploration/analysis output (non-implementation)
- User explicitly requests fast completion
- Single file, <20 lines small change

#### 3. Prajna Gate → Alaya

| Prajna Result | Write to Alaya? | Note |
|---------------|-----------------|------|
| **Found anchor worth preserving** | ✅ YES | Meets threshold, write |
| **No new anchors** | ⭕ Optional | Update compact.md |
| **Found rule issues** | ⚠️ FEEDBACK | Generate rule patch suggestion |
| **Found backtrack issue** | 🔄 Backtrack | Return to Sila/Samadhi for recheck |

**Alaya write threshold** (at least one):
- Repetition ≥ 2: Similar problem/decision appeared 2+ times
- High impact: Involves architecture, security, performance, multi-module
- Reusable: Has reference value in other projects/scenarios

### Failure Handling Classification

#### Severe Failure (REJECT) - Must Redo

| Failure Type | Gate | Detection | Handling |
|--------------|------|-----------|----------|
| **Security violation** | Sila | Sensitive path/dangerous command/credential exposure | Reject immediately, no retry |
| **Contract missing** | Sila | Required field empty | Return, require completion |
| **Boundary violation** | Sila | Do/Don't boundary violated | Return, point out violation |
| **L0 speculation no evidence** | Samadhi | "Should work"/"Probably can" | Return, require verification |

#### Fixable Failure (RETRY) - Fix Then Retry

| Failure Type | Gate | Detection | Handling |
|--------------|------|-----------|----------|
| **Format non-compliant** | Sila | Non-critical field missing/format error | Warn + require supplement |
| **L1 evidence insufficient** | Samadhi | Only reference, no local verification | Require L2 verification |
| **Test failure** | Samadhi | pytest/ctest failed | Avatar fixes then retry |
| **Build failure** | Samadhi | cmake/make error | Avatar fixes then retry |
| **Type check failure** | Samadhi | mypy error | Avatar fixes then retry |

**RETRY limits**:
```
1st failure → Fix then retry
2nd failure → Analyze root cause, then fix
3rd failure → Stop, escalate to user
```

#### Feedback Failure (FEEDBACK) - Needs Rule Improvement

| Failure Type | Gate | Detection | Handling |
|--------------|------|-----------|----------|
| **Rule conflict** | Prajna | Two rules contradict | Generate rule patch suggestion |
| **Efficiency issue** | Prajna | Obvious parallel/cache opportunity | Record deviation, suggest improvement |
| **Repeated issue** | Prajna | Similar issue 2nd occurrence | Preserve as problem anchor |
| **Boundary unclear** | Prajna | Do/Don't definition unclear | Suggest tighten/loosen rule |

### Backtracking Rules

#### When to Backtrack?

```
Prajna found issue
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│                    Issue Type Assessment                   │
├───────────────────────────────────────────────────────────┤
│ 1. Rule misunderstanding  → Backtrack to Sila (missed/misjudged)    │
│ 2. Insufficient verification → Backtrack to Samadhi (evidence level) │
│ 3. Efficiency suggestion  → No backtrack, record to Alaya (FEEDBACK) │
│ 4. New constraint found   → No backtrack, add to anchors (preserve)  │
└───────────────────────────────────────────────────────────┘
```

| Backtrack Type | Trigger Condition | Target | Recheck Content |
|----------------|-------------------|--------|-----------------|
| **Backtrack to Sila** | Found missed security issue | Sila | Full security check |
| **Backtrack to Sila** | Found Contract violation | Sila | Contract completeness |
| **Backtrack to Samadhi** | Found unreliable evidence | Samadhi | Add L2/L3 verification |
| **Backtrack to Samadhi** | Found missing test scenario | Samadhi | Add test cases |

**Backtrack limits**:
```
Same avatar output backtrack count:
├── Backtrack 1 time → Normal handling
├── Backtrack 2 times → Warning, detailed analysis
└── Backtrack 3 times → Stop, escalate to user
```

### Track-Specific Verification Rules

| Track | Sila Focus | Samadhi Threshold | Prajna Depth | Skip Prajna? |
|-------|------------|-------------------|--------------|--------------|
| **Feature** | Contract complete | L2 + AC tests all pass | Full introspection | ❌ Cannot skip |
| **Fix** | Security + regression risk | L2 + repro case + regression test | Problem anchor extraction | ⚠️ Small fix can skip |
| **Refactor** | Boundary + behavior preserved | L2 + behavior unchanged proof | Decision anchor extraction | ❌ Cannot skip |
| **Direct** | Basic security check | L1 acceptable | Can skip | ✅ Can skip |

### Parallel Verification Rules

> After each parallel batch completes, must immediately verify before starting next batch.

```
❌ Verify at end (problems accumulate):
Batch1 → Batch2 → Batch3 → Final verify → Found Batch1 issue → Major rework

✅ Batch verify (find early):
Batch1 → Verify ✓ → Batch2 → Verify ✓ → Batch3 → Verify ✓ → Done
```

**Batch Verification Flow**:
```
Parallel batch completes
      │
      ▼
┌─────────────────────────────────────┐
│ Batch Verification (simplified 3 gates) │
├─────────────────────────────────────┤
│ 1. Quick Sila: Contract existence check  │
│ 2. Quick Samadhi: File exists + syntax   │
│ 3. Skip Prajna: Batch verify no reflect  │
└─────────────────────────────────────┘
      │
      ├─ PASS → Continue next batch
      └─ FAIL → Stop, fix then retry current batch
```

### Verification Commands Quick Reference

**Quick Verification (within batch)**:
```bash
# Python
python -m py_compile {file}  # Syntax check
python -c "import {module}"  # Import check

# C++
cmake --build build --target {target}  # Incremental build

# General
ls -la {expected_files}  # File existence check
```

**Full Verification (final)**:
```bash
# Python
ruff check . && mypy src/ && pytest -v

# C++
cmake -B build && cmake --build build -j && ctest --test-dir build

# FastAPI
pytest tests/api/ -v && curl http://localhost:8000/health
```

### Pipeline Status Report Template

```markdown
## Verification Pipeline Report

**Task**: {task_name}
**Track**: {track}
**Avatar**: {avatar}

### Pipeline Status

| Gate | Status | Detail |
|------|--------|--------|
| Sila | ✅ PASS | Contract complete, no security issues |
| Samadhi | ✅ PASS (L2) | Tests passed 15/15 |
| Prajna | ✅ PASS | Extracted anchor [D003] |
| Alaya | ✅ Written | anchors.md updated |

### Verification Details

#### Sila Gate
- [x] Contract completeness
- [x] Do/Don't boundaries
- [x] Security check

#### Samadhi Gate
- **Evidence Level**: L2
- **Verification Command**: `pytest -v`
- **Result**: 15 passed, 0 failed

#### Prajna Gate
- **Introspection Score**: B
- **New Anchor**: [D003] xxx
- **Rule Patch**: None

### Backtrack Record (if any)
| Count | Target | Reason | Result |
|-------|--------|--------|--------|
| 1 | Samadhi | Missing regression test | Supplemented |
```

### Pipeline Constraints

**NEVER**:
- Skip Sila to directly enter Samadhi
- L0 speculation pass Samadhi
- Trigger Alaya write without threshold check
- Unlimited backtrack (max 3 times)
- Continue next batch after batch verification fails

**ALWAYS**:
- Sila REJECT = Pipeline terminates
- Samadhi at least L1, complex tasks at least L2
- Prajna check threshold before triggering Alaya
- Record backtrack reason and count
- Verify batch before continuing

---

### Track B: Bug Fix (问题修复)

**Trigger**: "Fix", "Bug", "Error", "Crash", "Issue"

**Default DAG**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Locate + Review (parallel)                             │
│  ┌─────────┐    ┌─────────┐                                      │
│  │ 👁 Eye   │    │ 👃 Nose  │  <- Can parallel: explore + review  │
│  │ Problem  │    │ Root     │  problem code                       │
│  │ Locate   │    │ Cause    │                                      │
│  └────┬────┘    └────┬────┘                                      │
│       │              │                                            │
│       └──────┬───────┘                                            │
│              ▼                                                    │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: Fix (serial)                                           │
│              ┌─────────┐                                          │
│              │ ⚔️ Body  │  <- Depends on locate result, no full   │
│              │ Code     │  design needed                          │
│              │ Fix      │                                          │
│              └────┬────┘                                          │
│                   ▼                                               │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: Regression Test (serial)                               │
│              ┌─────────┐                                          │
│              │ 👅 Tongue│  <- Add reproduction case + regression  │
│              │ Test     │  tests                                   │
│              │ Verify   │                                          │
│              └────┬────┘                                          │
│                   ▼                                               │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: Postmortem (optional)                                  │
│              ┌─────────┐                                          │
│              │ 🔮 Intro │  <- Recommend postmortem for complex    │
│              │ spection │  bugs, extract lessons                   │
│              │ Lessons  │                                          │
│              └─────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

**Gate Requirement**: L2 + reproduction case + regression tests pass

---

### Track C: Refactoring (代码重构)

**Trigger**: "Refactor", "Clean", "Modernize", "Optimize"

**Default DAG**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Status Analysis (serial)                               │
│              ┌─────────┐                                          │
│              │ 👁 Eye   │  <- Analyze status, coupling, deps     │
│              │ Current  │                                          │
│              │ Coupling │                                          │
│              └────┬────┘                                          │
│                   ▼                                               │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: Refactor Strategy (serial)                             │
│              ┌─────────┐                                          │
│              │ 🧠 Mind  │  <- Define refactor strategy (not full │
│              │ Refactor │  arch design)                           │
│              │ Strategy │                                          │
│              └────┬────┘                                          │
│                   ▼                                               │
├─────────────────────────────────────────────────────────────────┤
│  ⏰ [Alaya T2] Inject after strategy freeze                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Query Alaya:                                                  │ │
│  │ - Extract tech choices from strategy -> retrieve ADR [D]     │ │
│  │ - Inject: historical decisions, known tradeoffs, rollbacks   │ │
│  │ - Word limit: ≤400 chars                                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  See: .wukong/skills/alaya-injection.md                          │
├─────────────────────────────────────────────────────────────────┤
│  Phase 3: Execute (serial)                                       │
│              ┌─────────┐                                          │
│              │ ⚔️ Body  │  <- Execute per strategy, keep behavior │
│              │ Code     │  unchanged                               │
│              │ Refactor │                                          │
│              └────┬────┘                                          │
│                   ▼                                               │
├─────────────────────────────────────────────────────────────────┤
│  Phase 4: Verify (parallel)                                      │
│  ┌─────────┐    ┌─────────┐                                      │
│  │ 👃 Nose  │    │ 👅 Tongue│  <- Can parallel: maintainability   │
│  │ Maintain │    │ Regres  │  review + regression tests           │
│  │ ability  │    │ sion    │                                      │
│  └────┬────┘    └────┬────┘                                      │
│       │              │                                            │
│       └──────┬───────┘                                            │
│              ▼                                                    │
├─────────────────────────────────────────────────────────────────┤
│  Phase 5: Gate                                                   │
│              ┌─────────┐                                          │
│              │ 🐵 Body  │  <- Verify behavior unchanged + quality │
│              │ Behavior │  improved                                │
│              │ Aligned  │                                          │
│              └─────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

**Gate Requirement**: L2 + behavior unchanged proof (before/after output consistent)

---

### Track D: Direct (直接执行)

**Trigger**: Simple commands, explicit user summon (@syntax)

**Default DAG**:
```
┌─────────────────────────────────────────────────────────────────┐
│  User explicitly summons avatar -> Avatar executes -> Must      │
│  still go through verification Gate                              │
│                                                                   │
│  @Eye explore X -> 👁 Eye Avatar -> Return exploration report    │
│  @Mind design X -> 🧠 Mind Avatar -> Return design document      │
│  @Body implement X -> ⚔️ Body Avatar -> Return impl report ->   │
│  Gate verify                                                      │
│                                                                   │
│  Note: Even with direct summon, implementation tasks must pass   │
│  L1+ verification                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Gate Requirement**: L1 (can downgrade for simple tasks, but still need evidence)

#### Track D Two Modes

**Mode 1: @ Explicit Summon**

User uses `@` syntax to directly specify avatar:
- `@眼` / `@explorer` - Eye Avatar
- `@耳` / `@analyst` - Ear Avatar
- `@鼻` / `@reviewer` - Nose Avatar
- `@舌` / `@tester` - Tongue Avatar
- `@身` / `@impl` / `@斗战胜佛` - Body Avatar
- `@意` / `@architect` - Mind Avatar

Verification requirements: **Still need to pass Sila/Samadhi/Prajna checks**
- Eye/Ear/Nose (CHEAP): Lightweight (Sila Gate + L1)
- Tongue (MEDIUM): Standard (Sila/Samadhi Gate + L1/L2)
- Body/Mind (EXPENSIVE): Full (Sila/Samadhi/Prajna Gate + L2+)

**Mode 2: Trivial Tasks**

Simple requests that don't trigger any track keywords:
- Single file view/edit (<10 lines)
- Quick Q&A
- Config queries

Verification requirements: **Can downgrade to minimal verification**
- Body can execute directly (no avatar summon needed)
- Only need Sila Gate security check
- No L2+ evidence needed

#### Direct Track Threshold Definition

| Scenario | Avatar | Verification Level | Background? | Note |
|----------|--------|-------------------|-------------|------|
| `@眼 explore X` | Eye | Sila + L1 | Required | Exploration doesn't need L2 |
| `@耳 analyze req` | Ear | Sila + L1 | Optional | Req analysis doesn't need verify |
| `@鼻 review code` | Nose | Sila + L1 | Required | Review itself is verification |
| `@舌 write tests` | Tongue | Sila/Samadhi + L2 | Optional | Tests need to be runnable |
| `@身 implement X` | Body | Sila/Samadhi/Prajna + L2+ | Forbidden | Implementation must fully verify |
| `@意 design X` | Mind | Sila/Samadhi + L1/L2 | Forbidden | Design needs review but not run |
| Simple query | Body | Sila security | - | No avatar needed |
| Simple edit (<10 lines) | Body | Sila security | - | Body can do directly |

#### Direct Track Decision Flow

```
User Request
    │
    ▼
┌─────────────────────────────┐
│ 1. Contains @ marker?       │
└─────────────────────────────┘
    │
    ├── YES -> Parse target avatar
    │         │
    │         ▼
    │   ┌─────────────────────────────┐
    │   │ 2. Avatar cost level?       │
    │   ├─────────────────────────────┤
    │   │ CHEAP (Eye/Ear/Nose)        │
    │   │ -> Lightweight verify +     │
    │   │    background exec          │
    │   ├─────────────────────────────┤
    │   │ MEDIUM (Tongue)             │
    │   │ -> Standard verify          │
    │   ├─────────────────────────────┤
    │   │ EXPENSIVE (Body/Mind)       │
    │   │ -> Full verify + blocking   │
    │   │    exec                     │
    │   └─────────────────────────────┘
    │
    └── NO -> Mode 2: Trivial task
             │
             ▼
       ┌─────────────────────────────┐
       │ 3. Can Body do directly?    │
       ├─────────────────────────────┤
       │ - Single Glob/Grep/Read     │
       │ - Simple edit (<10 lines)   │
       │ - Quick Q&A                 │
       └─────────────────────────────┘
             │
             ├── YES -> Body exec + Sila security check
             │
             └── NO -> Upgrade to other Track (A/B/C)
```

---

### DAG Selection Decision Tree

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ⏰ [Alaya T1] Inject before task starts                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Query Alaya:                                                 │ │
│ │ - Extract keywords -> retrieve related anchors [P/C/M type] │ │
│ │ - Inject: risk labels, constraint reminders, anti-patterns  │ │
│ │ - Word limit: ≤300 chars                                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ See: .wukong/skills/alaya-injection.md                          │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ Using @ to explicitly summon?   │
└─────────────────────────────────┘
    │
    ├── YES -> Track D (Direct)
    │
    ▼ NO
┌─────────────────────────────────┐
│ Keyword recognition             │
├─────────────────────────────────┤
│ "Add/Create/New/Feature"  -> Track A (Feature)
│ "Fix/Bug/Error/Crash"     -> Track B (Fix)
│ "Refactor/Clean/Optimize" -> Track C (Refactor)
│ Other simple tasks        -> Track D (Direct)
└─────────────────────────────────┘
```

---

## Conflict Arbitration Protocol (冲突仲裁协议)

> **Most common multi-agent situation: avatars disagree** - Must have clear arbitration rules.

### Common Conflict Scenarios

```
Conflict type examples:
├── 🧠Mind says: "This design is more elegant"
├── 👃Nose says: "Too risky, security concern"
├── ⚔️Body says: "Implementation cost too high"
└── 👅Tongue says: "This approach is untestable"
```

### Conflict Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Make conflict explicit                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Who       │ Opinion                 │ Evidence             │ │
│  │───────────│─────────────────────────│──────────────────────│ │
│  │ 🧠Mind    │ Use microservices       │ Better scalability   │ │
│  │ 👃Nose    │ Monolith is safer       │ Reduces attack       │ │
│  │           │                         │ surface              │ │
│  │ ⚔️Body    │ Monolith has lower cost │ Estimate: 2 days vs  │ │
│  │           │                         │ 2 weeks              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: Body arbitrates by priority                             │
│                                                                   │
│  Three arbitration principles (by priority):                     │
│                                                                   │
│  1️⃣ Satisfy AC first                                            │
│     -> Which approach satisfies acceptance criteria? Exclude     │
│     approaches that don't satisfy AC                             │
│                                                                   │
│  2️⃣ Controllable risk first                                     │
│     -> Security/data loss/irreversible risks must be considered │
│     first                                                        │
│     -> Better to sacrifice elegance than security                │
│                                                                   │
│  3️⃣ Minimal change first                                        │
│     -> Especially for Fix track, prefer small fixes over big    │
│     changes                                                       │
│     -> Avoid over-engineering                                    │
│                              │                                   │
│                              ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: Output Decision Log                                     │
│                                                                   │
│  ```markdown                                                      │
│  ## Decision Log: {decision_id}                                   │
│                                                                   │
│  **Date**: {date}                                                 │
│  **Conflict**: {describe conflict}                                │
│                                                                   │
│  **Positions**:                                                   │
│  - 🧠Mind: {opinion} (evidence: {evidence})                       │
│  - 👃Nose: {opinion} (evidence: {evidence})                       │
│  - ⚔️Body: {opinion} (evidence: {evidence})                       │
│                                                                   │
│  **Decision**: {final decision}                                   │
│  **Basis**: {which principle}                                     │
│  **Impact**: {scope of impact}                                    │
│  **Anchor**: [D0xx] {brief description}                           │
│  ```                                                              │
│                              │                                   │
│                              ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│  Step 4: Create anchor (reuse next time)                         │
│                                                                   │
│  Create decision anchor after arbitration:                       │
│  [D0xx] {decision} - Based on {principle}, chose {approach}      │
│  instead of {alternative}                                         │
│                                                                   │
│  Next time similar conflict occurs, directly reference anchor,   │
│  no need to repeat discussion                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Arbitration Rules Quick Reference

| Conflict Type | Arbitration Principle | Example |
|---------------|----------------------|---------|
| Design elegance vs Security risk | 2️⃣ Controllable risk first | Choose secure approach |
| Feature complete vs Delivery time | 1️⃣ Satisfy AC first | Features not covered by AC can be deferred |
| Major refactor vs Minor patch | 3️⃣ Minimal change first | Fix track chooses minor patch |
| Performance vs Readability | 1️⃣ Satisfy AC first | If AC has no perf requirement, choose readable |
| New tech vs Mature solution | 2️⃣ Controllable risk first | Unless clear benefit, choose mature |

### Forbidden Arbitration Behaviors

```
❌ Forbidden:
├── Fence-sitting ("Both sides have a point, figure it out yourselves")
├── Arbitration without evidence ("I think it should be...")
├── Delaying arbitration ("Let's discuss next time")
├── Not recording after arbitration (repeat discussion next time)
└── Overturning recorded anchors (unless new strong evidence)
```

---

## Stage Flow Reference (阶段流程参考)

> Quick reference for stage inputs/outputs. See Track DAGs above for detailed flow.

### Stage 1: Requirement Gathering

```
Input: User request
Avatar: 👂 Ear Avatar (Listen)
Tasks: Parse explicit/implicit requirements, identify edge cases, confirm constraints
Output: requirements.md
```

### Stage 2: Solution Design

```
Input: requirements.md
Avatar: 🧠 Mind Avatar (Think)
Tasks: Analyze architecture, design solution, tech selection, identify risks
Output: design.md
```

### Stage 3: Implementation

```
Input: design.md
Avatar: ⚔️ Body Avatar (Act) + 👁️ Eye Avatar (Observe) (parallel)
Tasks: Eye researches related code (background), Body implements, incremental verify
Output: Code changes
```

### Stage 4: Testing

```
Input: Code changes
Avatar: 👅 Tongue Avatar (Speak)
Tasks: Unit tests, integration tests, boundary validation, coverage check
Output: Tests passed
```

### Stage 5: Code Review

```
Input: Code changes + tests
Avatar: 👃 Nose Avatar (Sense)
Tasks: Quality check, design consistency, potential issues, improvement suggestions
Output: review.md
```
