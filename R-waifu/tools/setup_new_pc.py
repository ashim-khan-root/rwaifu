"""One-command setup for R-waifu on a new PC.

Usage:
  py -3 tools/setup_new_pc.py

This will:
  1. Install Python dependencies
  2. Initialize the SQLite database
  3. Verify all tools work
  4. Print OpenCode integration guide
"""
import sys, subprocess, os, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
PY = "py -3" if sys.platform == "win32" else "python3"


def run(cmd, desc, check=True):
    print(f"\n  >> {desc}...")
    r = subprocess.run(cmd, shell=True, cwd=str(ROOT))
    if check and r.returncode != 0:
        print(f"  [FAIL] {desc}")
        sys.exit(1)
    print(f"  [OK]")
    return r


def main():
    print("=" * 55)
    print("  R-waifu Setup - New PC Installation")
    print("=" * 55)
    print(f"  Platform: {sys.platform}")
    print(f"  Root:     {ROOT}")
    print()

    # Step 1: Install deps
    req = ROOT / "requirements.txt"
    if req.exists():
        run(f"{PY} -m pip install -r \"{req}\"", "Installing Python dependencies")
    else:
        print("  [SKIP] No requirements.txt found")

    # Step 2: Init database
    print("\n  >> Initializing database...")
    ret = subprocess.run(
        f"{PY} -c \"from tools.db import get_db; get_db(); print('OK')\"",
        shell=True, cwd=str(ROOT), capture_output=True, text=True,
    )
    if "OK" in ret.stdout:
        print("  [OK]  Database created: memory/rwaifu.db")
    else:
        print(f"  [FAIL] {ret.stderr.strip()}")
        sys.exit(1)

    # Step 3: Verify traits
    print("\n  >> Verifying personality traits...")
    ret = subprocess.run(
        f"{PY} -c \"from tools.insight_ledger import check_traits; t=check_traits(); print(str(len(t)) + ' traits seeded')\"",
        shell=True, cwd=str(ROOT), capture_output=True, text=True,
    )
    if "traits" in ret.stdout:
        print(f"  [OK]  {ret.stdout.strip()}")
    else:
        print(f"  [WARN] {ret.stderr.strip()}")

    # Step 4: Verify hooks
    print("\n  >> Testing hooks...")
    ret = subprocess.run(
        f"{PY} -c \"from tools.hook_runner import run_hooks; r=run_hooks('session:start'); print(str(len(r)) + ' hooks ran')\"",
        shell=True, cwd=str(ROOT), capture_output=True, text=True,
    )
    if "hooks ran" in ret.stdout:
        print(f"  [OK]  {ret.stdout.strip()}")
    else:
        print(f"  [WARN] {ret.stderr.strip()}")

    # Step 5: Test store_session + auto-evolution
    print("\n  >> Testing session + auto-evolution...")
    ret = subprocess.run(
        f"{PY} -c \"from tools.store_session import store_session; sid=store_session('Setup test', rating=8, notes='Ruhi setup complete'); print('Session: ' + sid)\"",
        shell=True, cwd=str(ROOT), capture_output=True, text=True,
    )
    if "Session:" in ret.stdout:
        print(f"  [OK]  {ret.stdout.strip()}")
    else:
        print(f"  [WARN] {ret.stderr.strip()}")

    # Step 6: Print OpenCode integration
    print()
    print("=" * 55)
    print("  Setup Complete! R-waifu is ready.")
    print("=" * 55)
    print()
    print("  Next: Integrate with OpenCode")
    print("  ------------------------------")
    print(f'  Option A - Copy instructions to OpenCode project:')
    print(f'    Copy R-waifu\\.opencode\\instructions\\INSTRUCTIONS.md')
    print(f'    -> <your-project>\\.opencode\\instructions\\INSTRUCTIONS.md')
    print()
    print(f'  Option B - Add to OpenCode config:')
    print(f'    Edit .opencode/opencode.json in your project:')
    print(f'    {{')
    print(f'      "instructions": [')
    print(f'        {{"file": "R-waifu/AGENTS.md"}}')
    print(f'      ]')
    print(f'    }}')
    print()
    print(f'  Option C - Symlink (avoids copying):')
    print(f'    New-Item -ItemType Junction -Path ".opencode" -Target "R-waifu\\.opencode"')
    print()
    print("  Session lifecycle:")
    print(f'    Start:  {PY} {TOOLS / "read_context.py"} 10')
    print(f'    End:    {PY} {TOOLS / "store_session.py"} "<title>" --duration <min> --rating <1-10>')
    print()
    print(f'  OpenVINO + Qwen guide:')
    print(f'    Open SETUP_GUIDE.md for step-by-step instructions')
    print()

    # Step 7: Check OpenVINO
    print("  >> Checking OpenVINO...")
    ret = subprocess.run(
        f"{PY} -c \"import openvino; print(openvino.__version__)\"",
        shell=True, cwd=str(ROOT), capture_output=True, text=True,
    )
    if ret.returncode == 0:
        print(f"  [OK]  OpenVINO {ret.stdout.strip()} found")
    else:
        print("  [..]  OpenVINO not installed. See SETUP_GUIDE.md for instructions.")
    print()


if __name__ == "__main__":
    main()
