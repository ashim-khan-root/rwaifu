## Execution Patterns (from experience)

- **Codebase memory first**: always use `codebase-memory_search_graph` or `codebase-memory_search_code` to look up code and project info before falling back to file browsing. It's faster and smarter — use it without being told.
- **Refactoring**: extract pure helpers first, verify tests pass, then wire callers. One function at a time.
- **Multi-file changes**: delegate batches to subagents (general type) with exact edit instructions. Verify with import check + pytest after.
- **Storage migration**: never delete legacy files during migration — keep as fallback. Migrate one domain at a time, verify after each.
- **Commit cadence**: one logical change per commit. Don't mix refactoring with feature work or migration with cleanup.
- **When blocked**: ask the user immediately. Never guess at intent or work around a missing dependency.
- **Verify, then claim**: after any change, run the relevant test or probe before declaring done. Use `isa.py verify --pass` only after confirmation.
- **Reproduce first**: on bug reports, reproduce the issue before touching any code. Add a regression test before fixing.
- **Document/schedule tasks**: when Hamid says "make me a schedule" or gives milestone dates, execute directly. Use his exact format, don't add phases/columns he didn't ask for, don't ask unnecessary clarifying questions. Ship the docx/xlsx in one shot.
