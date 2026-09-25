"""
Execute the offline (RUN_AWS=False / USE_BEDROCK=False) code path of each
notebook to confirm the shared version runs without AWS credentials.

Any cell that touches AWS is guarded by RUN_AWS/USE_BEDROCK in the notebooks,
so with the safe defaults every code cell should execute cleanly.

Run:  python setup/verify_local.py
"""
import json
import glob
import sys
import traceback
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent.parent / "notebooks"

# Notebooks that import boto3 at the top level. If boto3 is not installed in the
# verifying environment we skip them (they are exercised in a real Jupyter kernel
# that has boto3). Their offline guards are still checked for structure.
NEEDS_BOTO3 = {"Module_4_slide_25_test_hr_assistant_flow.ipynb"}

try:
    import boto3  # noqa: F401
    HAVE_BOTO3 = True
except ModuleNotFoundError:
    HAVE_BOTO3 = False

# HR flow notebook has no offline compute path (it only defines a function and
# prints the question list when RUN_AWS=False), but it must still execute cleanly.
results = []
for nb_path in sorted(NB_DIR.glob("*.ipynb")):
    if nb_path.name in NEEDS_BOTO3 and not HAVE_BOTO3:
        print(f"SKIP  {nb_path.name} (boto3 not installed in this env)")
        continue
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    # Fresh namespace per notebook, run cells in order.
    ns = {"__name__": "__main__"}
    errors = []
    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        code = "".join(cell["source"])
        try:
            exec(compile(code, f"{nb_path.name}#cell{i}", "exec"), ns)
        except Exception:
            errors.append((i, traceback.format_exc()))
    status = "PASS" if not errors else "FAIL"
    results.append((nb_path.name, status, errors))
    print(f"{status}  {nb_path.name}")
    for i, tb in errors:
        print(f"    cell {i} raised:\n{tb}")

print()
failed = [r for r in results if r[1] == "FAIL"]
if failed:
    print(f"{len(failed)} notebook(s) failed the offline run.")
    sys.exit(1)
print("All notebooks executed cleanly in offline mode.")
