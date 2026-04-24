# Memory Query Rules

> Framework-managed file. Overwritten on upgrade. Do not edit manually.

## Trigger Strategy

**Core principle**: When task is new and unrelated to current context, MUST create a Memory Query Task.

**MUST trigger**:

- Task topic is new — not a continuation of recent conversation
- Task involves a project/domain not currently in context
- After session compaction (cold start)
- Comprehensive audit/inventory tasks

**Do NOT trigger**:

- Follow-up to active conversation thread
- MEMORY.md already contains relevant information
- Small talk / greetings / status queries

## How to Create

1. Load `manager-memory-query` skill
2. Create under **memory-query project** (projectId: 109, path: `~/VerdentProject/memory-query`)
3. Task uses `file_read`/`glob`/`grep_content` to explore memory files
4. Result written to `~/.verdent/artifacts/memory-query/{session_id}/result.json`
5. `before_model_hook` auto-injects result into next LLM call

## Agentic Exploration

Start from `memories/_index.md` → use `grep_content` for keywords → `file_read` for relevant sections → iterative deep-dive.

Priority: `knowledge/lessons/` > `rules/` > `state/daily/`

## Result Injection

- Result file → `before_model_hook` checks existence → reads + formats as system-notification → injects → deletes file
