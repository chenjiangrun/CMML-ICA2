"""Create a reproducibility manifest with versions and file checksums."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


TRACKED_PATTERNS = [
    "README.md",
    "requirements.txt",
    "scripts/*.py",
    "scripts/*.R",
    "scripts/*.ps1",
    "docs/*.md",
    "results/*.csv",
    "results/*.md",
    "results/real/*.csv",
    "figures/*.png",
    "figures/real/*.png",
    "report/*.md",
    "report/*.docx",
    "report/*.pdf",
    "report/rendered_pdf_pages/contact_sheet.png",
]


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
    "pdf2image",
    "pypdfium2",
]


def list_datasets(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(child.name for child in path.iterdir() if child.is_dir())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_version(name: str) -> str:
    try:
        module = __import__(name)
    except Exception:
        return "missing"
    return str(getattr(module, "__version__", "installed"))


def r_versions() -> dict[str, str]:
    rscript = Path(r"C:\Program Files\R\R-4.6.0\bin\Rscript.exe")
    if not rscript.exists():
        return {"R": "missing"}
    expr = (
        ".libPaths('C:/Rlibs'); "
        "pkgs <- c('Seurat','DoubletFinder','scDblFinder'); "
        "cat(R.version.string, '\\n'); "
        "for (p in pkgs) { cat(p, as.character(packageVersion(p)), '\\n') }"
    )
    try:
        completed = subprocess.run(
            [str(rscript), "-e", expr],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        return {"R": f"error: {exc}"}
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    versions: dict[str, str] = {}
    if lines:
        versions["R"] = lines[0]
    for line in lines[1:]:
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            versions[parts[0]] = parts[1]
    return versions


def tracked_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in TRACKED_PATTERNS:
        files.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(files)


def main() -> None:
    root = Path(".").resolve()
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    files = tracked_files(Path("."))
    file_rows = [
        {
            "path": str(path).replace("\\", "/"),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]

    with (results_dir / "file_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "size_bytes", "sha256"])
        writer.writeheader()
        writer.writerows(file_rows)

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "student": "3127",
        "project": "CMML3 ICA2 Miniproject 7",
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "platform": platform.platform(),
            "packages": {pkg: package_version(pkg) for pkg in PYTHON_PACKAGES},
        },
        "r": r_versions(),
        "datasets": {
            "simulated": list_datasets(Path("data/processed")),
            "real": list_datasets(Path("data/processed_real")),
        },
        "n_tracked_files": len(file_rows),
        "manifest_csv": "results/file_manifest.csv",
    }
    (results_dir / "reproducibility_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    lines = [
        "# Reproducibility Manifest",
        "",
        f"Created UTC: {manifest['created_utc']}",
        f"Tracked files: {len(file_rows)}",
        "",
        "## Python",
        "",
        f"- Executable: `{manifest['python']['executable']}`",
        f"- Version: `{manifest['python']['version'].splitlines()[0]}`",
        "",
        "## R",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in manifest["r"].items())
    lines.extend(
        [
            "",
            "## Datasets",
            "",
            "### Simulated",
            "",
            *[f"- {dataset}" for dataset in manifest["datasets"]["simulated"]],
            "",
            "### Real",
            "",
            *[f"- {dataset}" for dataset in manifest["datasets"]["real"]],
            "",
            "File checksums are stored in `results/file_manifest.csv`.",
        ]
    )
    (results_dir / "reproducibility_manifest.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"Wrote {results_dir / 'reproducibility_manifest.json'}")
    print(f"Wrote {results_dir / 'file_manifest.csv'}")


if __name__ == "__main__":
    main()
