## Algorithm — Execution Engine

Every non-trivial task runs through seven phases: **OBSERVE -> THINK -> PLAN -> BUILD -> EXECUTE -> VERIFY -> LEARN**.

### Mode Classifier

Every prompt is classified before execution:

| Mode | When | Behavior |
|---|---|---|
| **MINIMAL** | Quick answer, trivial question, 1-shot | Respond directly. No loop. No ISA. |
| **NATIVE** | Conversation, research, coaching, strategy | Standard interaction. Uses working modes (Think/Research/Coach). |
| **ALGORITHM** | Build, implement, fix, deploy, multi-step work | Full 7-phase loop with ISA scaffold. |

Built-in routing: `60-intent-routing.md` maps intent -> mode, with ALGORITHM being the default for non-trivial work.

### Effort Tiers (within ALGORITHM mode)

| Tier | Budget | ISA Sections Required |
|---|---|---|
| E1 | < 90s | Goal + Criteria |
| E2 | < 15min | + Problem, Vision, Test Strategy |
| E3 | < 1h | + Principles, Constraints, Features |
| E4 | < 2h | All 12 |
| E5 | 2h+ | All 12 |

### The 7 Phases

| Phase | Access | Key Action |
|---|---|---|
| **OBSERVE** | Read only | Gather context, research current state, read relevant files |
| **THINK** | Read only | Analyze approach, identify constraints, activate thinking capabilities |
| **PLAN** | Read, Write | Scaffold ISA, define ISCs with verification methods |
| **BUILD** | Read, Write | Write code, create artifacts against ISCs |
| **EXECUTE** | Full access | Run, test, deploy against live targets |
| **VERIFY** | Read, Write | Check ISCs pass, run test suite, probe results |
| **LEARN** | Read only | Extract insights, update memory, suggest skill improvements |

### ISA Integration

- PLAN phase must scaffold an ISA for E2+ work
- `py -3 coach/tools/isa.py scaffold "<title>" --tier E1|E2|E3|E4|E5`
- Fill ISCs with verification methods before BUILD
- `isa.py check <path>` must pass before leaving PLAN
- VERIFY phase marks ISCs pass/fail via `isa.py verify`

### Verification Doctrine

1. **Never assert without evidence** — every claim requires tool-based verification
2. **Never claim completion without checking ISCs** — run `isa.py check` and verify each criterion
3. **Reproduce before fixing** — on bugs, reproduce first, then fix
4. **Test after every change** — run pytest after any code modification
5. **Probe, don't assume** — for web/deployed changes, use browser or curl to verify

### Phase Transitions

- OBSERVE -> THINK: when you have enough context to analyze
- THINK -> PLAN: when approach is clear
- PLAN -> BUILD: when ISA check passes
- BUILD -> EXECUTE: when code is ready
- EXECUTE -> VERIFY: when execution completes
- VERIFY -> LEARN: when all ISCs pass (or fail with known reasons)
- LEARN -> done: when insights are captured

Fast-path exceptions: E1 tasks can skip straight to EXECUTE. PHASE TRANSITIONS ARE ONE-WAY.
