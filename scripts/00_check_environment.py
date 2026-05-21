"""Check local dependencies for miniproject 7."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil


PYTHON_PACKAGES = [
    "numpy",
    "pandas",
    "scipy",
    "sklearn",
    "matplotlib",
    "seaborn",
    "scanpy",
    "anndata",
    "scrublet",
    "docx",
]


def main() -> None:
    print("Python package status")
    for package in PYTHON_PACKAGES:
        status = "OK" if importlib.util.find_spec(package) else "MISSING"
        print(f"- {package}: {status}")

    print("\nExternal command status")
    rscript_candidates = [
        Path(r"C:\Program Files\R\R-4.6.0\bin\Rscript.exe"),
        Path(r"C:\Program Files\R\R-4.5.0\bin\Rscript.exe"),
    ]
    rscript = shutil.which("Rscript")
    if not rscript:
        rscript = next((str(path) for path in rscript_candidates if path.exists()), None)
    print(f"- Rscript: {rscript if rscript else 'MISSING'}")

    quarto = shutil.which("quarto")
    print(f"- quarto: {quarto if quarto else 'MISSING (optional; report is built with python-docx)'}")

    r_lib = Path(r"C:\Rlibs")
    print(f"- R package library: {r_lib if r_lib.exists() else 'MISSING'}")


if __name__ == "__main__":
    main()
