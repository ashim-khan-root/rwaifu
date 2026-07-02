# R-waifu Setup Guide

## Quick Start (Everything except OpenVINO)

```bash
py -3 tools/setup_new_pc.py
```

That installs deps, inits DB, verifies tools, and prints OpenCode integration steps.

---

## OpenVINO + Qwen Model Setup

R-waifu can run locally via Qwen2.5-Coder-0.5B on OpenVINO. This is optional — she works fine with OpenCode's built-in LLM.

### Step 1: Install OpenVINO Runtime

**Windows:**
```bash
pip install openvino tokenizers numpy
```

**Verify:**
```bash
py -3 -c "import openvino; print(openvino.__version__)"
# Should print something like: 2025.x.x
```

### Step 2: Get the Qwen Model (Two Options)

**Option A — Download Pre-Converted Model (Recommended, ~1.5 GB)**

```bash
# Download from HuggingFace (OpenVINO IR format):
# Model: Qwen/Qwen2.5-Coder-0.5B-Instruct-int4-ov
# Or search huggingface.co for "qwen2.5-coder-0.5b-int4-ov"
# Save to: C:\models\qwen2.5-coder-0.5b-int4\
```

Expected files in the folder:
```
C:\models\qwen2.5-coder-0.5b-int4\
├── openvino_model.xml         # Model graph
├── openvino_model.bin         # Model weights
├── tokenizer.json             # Tokenizer
├── generation_config.json     # Generation config
└── config.json                # Model config
```

**Option B — Convert from HuggingFace (Requires more RAM)**

```bash
pip install optimum[openvino]

# Convert the model:
optimum-cli export openvino \
  --model Qwen/Qwen2.5-Coder-0.5B-Instruct \
  --task text-generation-with-past \
  --weight-format int4 \
  C:\models\qwen2.5-coder-0.5b-int4
```

### Step 3: Verify Inference

```bash
py -3 R-waifu/tools/qwen_inference.py
# Should output: Ruhi-style greeting or model response
```

### Step 4: Set Model Path (if not default)

Default paths:
- Windows: `C:\models\qwen2.5-coder-0.5b-int4`
- Linux: `~/.cache/openvino-models/qwen2.5-coder-0.5b-int4`

Override via env variable:
```bash
$env:QWEN_MODEL_PATH = "D:\models\qwen2.5-coder-0.5b-int4"
py -3 tools/qwen_inference.py
```

### Troubleshooting

| Problem | Fix |
|---|---|
| `ImportError: No module named openvino` | Run `pip install openvino tokenizers numpy` |
| `FileNotFoundError: Model not found` | Download model or set `QWEN_MODEL_PATH` |
| Model runs but gibberish output | Wrong model format. Must be OpenVINO IR (xml + bin), not PyTorch |
| Slow inference | Expected on CPU. ~21ms/tok for 0.5B. Use larger model for better quality |
| `LLMPipeline hangs` | Don't use openvino-genai. Use the raw compiled_model API (already fixed in code) |

---

## OpenCode Integration

### Method A — Copy Instructions (Simple)

```bash
# Copy once, then OpenCode reads them automatically:
xcopy /E /I "R-waifu\.opencode" "<your-project>\.opencode"
```

### Method B — AGENTS.md Reference

Edit `.opencode/opencode.json` in your project:
```json
{
  "instructions": [
    {"file": "R-waifu/AGENTS.md"}
  ]
}
```

### Method C — Symlink (No Copy Needed)

```powershell
# Windows (Admin required for symlink, Junction doesn't):
New-Item -ItemType Junction -Path ".opencode" -Target "R-waifu\.opencode"
```

---

## Session Lifecycle Cheatsheet

```bash
# Start
py -3 R-waifu/tools/read_context.py 10
py -3 -c "from R-waifu.tools.hook_runner import run_hooks; run_hooks('session:start')"

# End (auto-evolves her personality)
py -3 R-waifu/tools/store_session.py "<title>" --duration <min> --rating <1-10> --mood "<mood>" --notes "<notes>"
```

---

## Moving to Another PC (Full Migration)

1. **Copy entire R-waifu/** folder (including `memory/rwaifu.db`)
2. On new PC: `py -3 tools/setup_new_pc.py`
3. Optional: Install OpenVINO + Qwen per guide above
4. Done. All memories, traits, and milestones preserved.
