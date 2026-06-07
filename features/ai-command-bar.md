# Feature: AI Command Bar

A persistent natural-language input bar (always visible at the bottom of the app) backed
by Claude's tool-use API. You type a request in plain English; Claude reads/acts on your
Gmail and Calendar using the same action layer as the traditional UI.

## Basic Flow

1. User types a command (e.g. "Summarize my 5 most recent unread emails") and presses Send.
2. Frontend `POST /api/assistant/command { text }`.
3. Backend sends the text to Claude (`claude-sonnet-4-6` by default) with all 11 tools attached.
4. **Tool-use loop** runs up to 8 turns:
   - Claude returns a `tool_use` block → orchestrator checks if it's a **confirm-required** tool.
   - If **read-only** (list/get/search/free): execute immediately, feed result back to Claude, continue.
   - If **destructive/outbound** (send/reply/create/update/delete): stop the loop, return `pending`.
5. When the loop ends with `stop_reason="end_turn"`, the final `text` block is the reply.
6. **Confirm path:** frontend shows the pending action's `summary` + Confirm/Cancel buttons.
   Confirm → `POST /api/assistant/confirm { tool, input }` → executes the action directly
   (no Claude round-trip), returns result, frontend invalidates `["messages"]`/`["events"]`.
7. After any action, frontend invalidates TanStack Query keys so Inbox/Calendar refresh.

### Example interactions
| Input | What happens |
|---|---|
| "Summarize my unread emails" | `list_messages(is:unread)` + multiple `get_message()` calls → Claude summarises |
| "Draft a reply to the last email from Alice" | `list_messages(from:alice)` → `get_message()` → `create_draft()` (no confirm needed — drafts are safe) |
| "Schedule a 30-min sync tomorrow at 3pm" | `find_free_slots()` check → Claude proposes `create_event()` → **confirm prompt** → user clicks Confirm |
| "Delete my 9am meeting" | `list_events()` → Claude identifies the event → `delete_event()` → **confirm prompt** |

## Architecture

```
CommandBar (frontend)
    │ POST /api/assistant/command { text }
    │ POST /api/assistant/confirm { tool, input }
    ▼
routers/assistant.py
    │
    orchestrator.py  ─── Claude API (anthropic SDK)
    │    ▲  tool_use response
    │    └── tools.TOOL_FUNCTIONS[name](**input)
    │
    actions/{gmail_actions, calendar_actions}.py   ← same layer as REST routers
```

### Tool definitions (`assistant/tools.py`)
Each tool has a `name`, `description`, and JSON input schema following the Anthropic
tool-use format. The `TOOL_FUNCTIONS` dict maps names to the actual Python callables
(wrappers over the action layer that serialize output to JSON-safe dicts).

`CONFIRM_TOOLS` is a `set[str]` of tool names that need confirmation:
`{"send_email", "reply", "create_event", "update_event", "delete_event"}`.

### The tool-use loop (`assistant/orchestrator.py`)
```python
for turn in range(MAX_TURNS=8):
    resp = claude.messages.create(model, tools, messages)
    if resp.stop_reason != "tool_use":
        return final_reply        # done
    for block in tool_use_blocks:
        if block.name in CONFIRM_TOOLS:
            return CommandResult(pending=PendingAction(...))  # stop, ask user
        result = TOOL_FUNCTIONS[block.name](**block.input)
        append tool_result to messages
    # continue loop
```

### System prompt
Built in `orchestrator._system_prompt()` — injected every call. Includes:
- User's email address (from `/auth/status`)
- Current local datetime **with timezone offset** (so Claude can correctly compute RFC3339 event times)
- Instruction to propose destructive actions via tools rather than asking in text

### `human_summary(tool, input)`
Generates the short human-readable string shown in the confirm UI (e.g.
`Send email to alice@… — "Meeting tomorrow"`). Edit this when adding new confirm tools.

## Affected Files

| Path | Role |
|---|---|
| `backend/app/assistant/tools.py` | Tool definitions, `TOOL_FUNCTIONS`, `CONFIRM_TOOLS`, `human_summary()` |
| `backend/app/assistant/orchestrator.py` | Tool-use loop, system prompt, `run_command()`, `confirm_action()` |
| `backend/app/routers/assistant.py` | `/assistant/command` and `/assistant/confirm` endpoints |
| `backend/app/config.py` | `anthropic_api_key`, `anthropic_model` (default `claude-sonnet-4-6`) |
| `frontend/src/components/CommandBar.tsx` | Input, reply display, confirm/cancel UI, query invalidation |
| `frontend/src/api/client.ts` | `api.command()`, `api.confirm()` |
| `frontend/src/api/types.ts` | `CommandResult`, `PendingAction` |

## Adding a new AI-accessible action

1. Add the function to `actions/gmail_actions.py` or `actions/calendar_actions.py`.
2. Add a dispatch wrapper in `assistant/tools.py` → `TOOL_FUNCTIONS`.
3. Add it to `CONFIRM_TOOLS` if it sends data or mutates state.
4. Add a tool definition (name/description/input_schema) to the `TOOLS` list.
5. Add a `human_summary` case if it's a confirm tool.
6. Optionally expose it via a REST router if the traditional UI also needs it.
