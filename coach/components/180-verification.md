## Verification

### Standard Checks
No linting. After changes:
- Run `py -3 -m pytest coach/tests/ -v --tb=short` to verify
- Run the script/file once to confirm it works (`py -3 path/to/file.py`)
- For freetoolz: **before pushing**, check if last 1-2 deploys were successful (`gh run list --repo ashim-khan-root/freetoolz --limit 3`). If they failed, diagnose first — don't push broken builds that waste GH Actions minutes.
- hugo.toml minification: keep `disableHTML = true` / `disableXML = true`. The `hugo --minify` CLI flag handles minification. Enabling both config + CLI causes the minifier to hang.

### Inline Verification Methods
Tasks and plans can carry explicit verification methods:

| Method | Usage |
|---|---|
| **CLI** | Run a command and check output |
| **Test** | Execute test suite and check pass/fail |
| **Static** | Analyze code structure |
| **Browser** | Playwright automation |
| **Grep** | Search for required/prohibited patterns |
| **Read** | Read file contents and validate |
| **Custom** | Task-specific verification steps |

Use: `py -3 coach/tools/task_manager.py add "<title>" <priority> --verify <method>`
