---
title: "Upgrade agent.py to Level 4 Dispatcher"
created: "2026-07-08 10:27"
status: draft
tier: E2
isa_id: "c6254419"
supersedes: ""
---

# ISA: Upgrade agent.py to Level 4 Dispatcher

## 1. Problem

In `agent.py`, structured command parsing uses regex patterns. Substring checks are used for fallback. This keyword-based dispatching is fragile, bypasses the LLM router, and blocks/ignores commands like `Plan`, `Anki`, and `Reflect` from running their corresponding tools. We need a robust, fully LLM-based tool triggering dispatcher that leverages the existing `DISPATCHER_PROMPT` to route all commands/inputs.

## 2. Vision

`agent.py` has no regex command parsing or keyword detection. All user queries (including commands like `session_complete`, `plan`, `anki`, `reflect`) are parsed and routed by `dispatch_tool` calling the LLM. Fallbacks are handled cleanly without regex.

## 3. Out of Scope

Modifying the actual prompt templates or tools themselves, except for testing or ensuring integration.

## 4. Principles

1. Simple and clean codebase.
2. Rely on LLM for classification and argument extraction.
3. Don't bypass the tools system.

## 5. Constraints

Must keep compatibility with current configuration and local LLM runtime (Llama 3.2 3B).

## 6. Goal

Refactor `coach/agent.py` to route all inputs through `dispatch_tool` utilizing the LLM dispatcher, removing `discover_tools_fallback` and `parse_command`/regex patterns entirely, while maintaining full functionality.

## 7. Criteria (ISC)

ID-stable criteria. Never re-number on edit. Splits become `ISC-N.M`. Drops become tombstones marked `[OBSOLETE]`.

- [x] ISC-1 [CRITICAL] Remove regex-based `parse_command` and `PATTERNS` from `coach/agent.py`. All user input must flow through the LLM dispatcher. -- verify: Static
- [x] ISC-2 [HIGH] Remove `discover_tools_fallback` keyword detection. If the LLM dispatcher fails, log the error and handle it gracefully (e.g. general conversation fallback or prompt user) without regex keyword triggering. -- verify: Static
- [x] ISC-3 [HIGH] Ensure commands like `session_complete` are correctly classification-dispatched to their tool scripts (`store_session.py`, etc.) and arguments are passed properly. -- verify: CLI
- [x] ISC-4 [MEDIUM] Add unit/integration tests to verify the routing logic. -- verify: Test

## 8. Test Strategy

How each criterion will be verified. Per-method or per-ISC detail.

| ISC | Method | How |
|-----|--------|-----|
| ISC-1 | Static | Verify `PATTERNS` and `parse_command` are removed from `coach/agent.py`. |
| ISC-2 | Static | Verify `discover_tools_fallback` is removed from `coach/agent.py`. |
| ISC-3 | CLI | Run `py -3 coach/agent.py` and test structured commands manually, checking subprocess logs. |
| ISC-4 | Test | Add unit tests to `coach/tests/` and run `py -3 -m pytest`. |

## 9. Features

What will be built, changed, or delivered. Concrete artifacts.

- Updated `coach/agent.py`
- Added tests in `coach/tests/test_agent_dispatcher.py`

## 10. Decisions

Key decisions and rationale. Updated as decisions are made.

| Decision | Rationale | Date |
|----------|-----------|------|
| Remove regex | To align with Level 4 LLM-based dispatching. | 2026-07-08 |

## 11. Changelog

Changes to this ISA after creation.

| Date | Change | Reason |
|------|--------|--------|
| 2026-07-08 | Initial | Initial E2 ISA plan. |

## 12. Verification

Results of verification. Updated as criteria pass/fail.

| ISC | Status | Date | Evidence |
|-----|--------|------|----------|
| ISC-1 | ⬜ Pending | | |
| ISC-2 | ⬜ Pending | | |
| ISC-3 | ⬜ Pending | | |
| ISC-4 | ⬜ Pending | | |
