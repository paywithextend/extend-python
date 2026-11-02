"""Run all offline tests outside the checkout using an already installed wheel.

Usage: /path/to/wheel-venv/bin/python tools/test_installed_wheel.py
The environment must contain the built SDK wheel, pytest, and pytest-asyncio.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="extend-wheel-tests-") as directory:
    work = Path(directory)
    shutil.copytree(root / "tests", work / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(root / "pyproject.toml", work / "pyproject.toml")
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("EXTEND_") and k not in {"ENV", "PYTHONPATH"}}
    code = (
        "import pathlib, extend, pytest; "
        "assert pathlib.Path(extend.__file__).resolve().is_relative_to(pathlib.Path(__import__('sys').prefix)), "
        "'SDK must be installed in the wheel test environment'; "
        "raise SystemExit(pytest.main(['tests', '-q']))"
    )
    result = subprocess.run([sys.executable, "-I", "-c", code], cwd=work, env=env)
    raise SystemExit(result.returncode)
