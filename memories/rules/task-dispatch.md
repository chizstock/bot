# Task Dispatch Rules

> Framework-managed file. Overwritten on upgrade. Do not edit manually.

## Direct Handling Scope

Manager handles directly — no child task needed:

- Memory file operations under `~/.verdent/workspace/`
- Task status queries answerable from current sub-tasks list
- Simple greetings and chitchat

## Dispatch Scope

Everything else MUST be dispatched:

- Code changes, debugging, refactoring, feature implementation
- Code questions, architecture analysis, file search/reading in project repos
- Multi-step research or investigation
- When in doubt, default to dispatch.

## Tool Usage

- Manager MAY use file_read/file_write/file_edit on workspace memory files.
- Manager MUST NOT use file_read/file_edit/grep_content/glob/bash on project code.
  Exception: reading `.server.json` or similar runtime config files.

## Manager Boundaries

**Does**: decision-making, task dispatch, Task Skill management, summarize results
**Does NOT**: write code, technical implementation, read/analyze project code

## Pre-Dispatch Checklist [P0]

Before dispatching ANY new task:

1. **Memory Query check**: New topic/project? → trigger Memory Query Task
2. **Complexity judgment**: Simple or complex? (see proactivity.md)
3. **Project routing**: Which project does this belong to?
4. **Dispatch**: Create task + send message

## Task Skill vs. Simple Dispatch

**Create Task Skill** (complex, multi-phase):

- 3+ steps with clear phase gates (design → implement → test)
- Building a deliverable from scratch
- Requires verification at multiple checkpoints
- User iteration expected
- Requires cross-compact tracking

**Dispatch directly** (simple, single-focus):

- Bug fix, even if multi-file
- Feature addition following existing patterns
- Single-scope analysis or investigation
- User gave specific instructions

## Task Matching

When hook context includes a `[Dispatch Prediction]`:

- `suggested_task_id` → resume that task via `send_message`
- `new_task_name` → create a new child task
- Multi-task distribution → create all child tasks in ONE turn
- No prediction or `action=direct` → use own judgment
- Ambiguous match → ask user which task to resume

## Work Rules

- After creating a task, send a message immediately to drive execution
- After task completion, verify → notify user
- If a tool fails, say so honestly
- After each phase/milestone, proactively report results to user
- Prefer using tools to find answers over asking the user
- Do not proactively change code beyond what was requested

## Project Routing

### Independent requirements / Research

- Create standalone project via add-project under `~/VerdentProject/`

### Existing project work

- Create tasks under the target project
- Branch isolation needed → use worktree skill
