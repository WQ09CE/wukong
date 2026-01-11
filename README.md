# Wukong 🐵

> A Multi-Agent Orchestration Framework for Claude Code.
> 
> "Every task is a journey to the West. You don't just write code; you conquer challenges."

**Wukong** is a specialized framework designed to turn Claude Code into a high-performance engineering team. It transforms the single agent into an orchestrator that manages specialized avatars (Subagents) for different tasks.

## 🌟 Features

- **Dynamic Workflow Tracks**: Automatically switches between Feature (Waterfall), Fix (Surgical), and Refactor modes.
- **Role-Based Avatars**:
  - 🐵 **Wukong (Body)**: Orchestrator, user interaction.
  - 📝 **Req Wukong**: Requirements analyst.
  - 🏗️ **Arch Wukong**: System architect.
  - ⚔️ **Battle Wukong (斗战胜佛)**: The elite implementer.
  - 🔍 **Explore Wukong**: Codebase scout.
  - 🧪 **Test Wukong**: QA engineer.
- **Parallel Execution**: High-throughput patterns like "Scout & Infantry" and "TDD Pincer".
- **Strict Verification**: "Avatars can lie." - Mandatory proof of work (Build/Test/Lint).

## 🚀 Installation

### Option 1: Automatic Install (Mac/Linux)

Run this command in your project root:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/WQ09CE/wukong/main/install.sh)"
```

### Option 2: Manual Install

1. Download this repository.
2. Copy the `.wukong` folder to your project root.
3. Create `.claude/rules` if it doesn't exist.
4. Symlink or copy `.wukong/rules/*.md` into `.claude/rules/`.

## 📂 Structure

```
.
├── .claude/
│   └── rules/           # Active behaviors loaded by Claude
│       ├── 00-wukong-core.md
│       └── ...
├── .wukong/             # Knowledge base & Templates
│   ├── skills/          # Detailed persona guides
│   ├── templates/       # Markdown templates (design docs, etc.)
│   ├── plans/           # Execution plans
│   └── notepads/        # Scratchpads for avatars
```

## 🎮 Usage

Just talk to Claude Code naturally. Wukong will intercept and classify your intent.

- **New Feature**: "I want to add a user login system." (Triggers Feature Track)
- **Bug Fix**: "Fix the crash in the payment module." (Triggers Fix Track)
- **Refactoring**: "Clean up the legacy auth code." (Triggers Refactor Track)

## 📜 License

MIT
