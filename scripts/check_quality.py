"""Run the project's code-quality gate: Black, Flake8, mypy (strict), pytest.

Usage:
    python -m scripts.check_quality        # run everything
    python -m scripts.check_quality --fix  # auto-format with Black first

Exits non-zero if any check fails, so it doubles as a CI entry point
(see .github/workflows/quality.yml) and a local pre-push habit.
"""

import subprocess
import sys

CHECKS = [
    ("Black (format check)", ["black", "--check", "app", "tests", "streamlit_app.py"]),
    ("Flake8 (lint)", ["flake8", "app", "tests", "streamlit_app.py"]),
    ("mypy --strict (types)", ["mypy", "--strict", "app"]),
    ("pytest (tests)", ["pytest", "-q"]),
]


def run(label: str, args: list[str]) -> bool:
    """Run one check and report pass/fail. Returns True on success."""
    print(f"\n=== {label} ===")
    result = subprocess.run([sys.executable, "-m", *args])
    return result.returncode == 0


def main() -> int:
    if "--fix" in sys.argv:
        print("=== Black (auto-format) ===")
        subprocess.run(
            [sys.executable, "-m", "black", "app", "tests", "streamlit_app.py"]
        )

    results = {label: run(label, args) for label, args in CHECKS}

    print("\n=== Summary ===")
    for label, passed in results.items():
        print(f"{'PASS' if passed else 'FAIL'}  {label}")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
