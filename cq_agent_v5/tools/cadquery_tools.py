"""
CadQuery execution and rendering tools for v4.
  execute_cadquery  — run code, return SUCCESS or error
  render_shape      — export SVG in 3 projections, return file paths
"""

import json
import os
import subprocess
import sys
import tempfile

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headless(code: str) -> str:
    return code.replace("show_object(", "#show_object(")


def _run_subprocess(script: str, timeout: int = 30) -> tuple[bool, str, str]:
    """Write script to temp file, run it, return (ok, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(script)
        path = f.name
    try:
        r = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=timeout,
        )
        return r.returncode == 0, r.stdout, r.stderr
    except Exception as e:
        return False, "", str(e)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def execute_cadquery(code: str) -> str:
    """Execute CadQuery Python code headlessly to verify it runs without errors.

    Returns 'SUCCESS' if the code is valid.
    Returns the full error traceback on failure.
    ALWAYS call this after writing or modifying code.
    If it fails, fix the error and call again (up to 5 attempts).
    """
    ok, stdout, stderr = _run_subprocess(_headless(code))
    if ok:
        return "SUCCESS - code is valid and ready for the editor."
    return f"FAILED:\n{(stderr or stdout).strip()}"


@tool
def render_shape(code: str) -> str:
    """Render the CadQuery shape to SVG files in 3 projections.

    Runs the code, exports isometric, front, and top SVG views.
    Returns a JSON string with paths to the SVG files, or an error message.

    Call this AFTER execute_cadquery returns SUCCESS.
    The reviewer agent uses these images to check the shape is correct.
    """
    tmp_dir = tempfile.mkdtemp(prefix="cq_render_")

    render_script = f"""\
import sys, json, os
import cadquery as cq

# --- user code (show_object replaced) ---
{_headless(code)}

# --- export 3 views ---
from cadquery import exporters

views = [
    ("isometric", (1.0, 1.0, 0.5)),
    ("front",     (0.0, -1.0, 0.0)),
    ("top",       (0.0,  0.0, 1.0)),
]
out = {{}}
tmp_dir = r"{tmp_dir}"
for name, proj in views:
    path = os.path.join(tmp_dir, name + ".svg")
    try:
        exporters.export(
            result, path,
            exportType=exporters.ExportTypes.SVG,
            opt={{"projectionDir": proj, "showAxes": False}},
        )
        out[name] = path
    except Exception as e:
        out[name] = f"ERROR: {{e}}"

print(json.dumps(out))
"""

    ok, stdout, stderr = _run_subprocess(render_script, timeout=45)
    if not ok:
        return f"RENDER_FAILED:\n{(stderr or stdout).strip()}"

    try:
        paths = json.loads(stdout.strip())
        good = {k: v for k, v in paths.items() if not str(v).startswith("ERROR")}
        if not good:
            return "RENDER_FAILED: all views errored"
        return json.dumps(good)
    except Exception as e:
        return f"RENDER_FAILED: could not parse output — {e}\nRaw: {stdout[:300]}"
