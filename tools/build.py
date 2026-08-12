#!/usr/bin/env python3
"""Builds the KPM repository index from package sources in sources/."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "sources"
BUILD_DIR = REPO_ROOT / "build"
DIST_DIR = REPO_ROOT / "dist"
KPM_HELPER = REPO_ROOT / "tools" / "kpm-helper.py"

REPO_MANIFEST = {
    "manifest_version": 2,
    "id": "kindletweaks",
    "name": "KindleTweaks KPM Repository",
    "description": "Kindle tweaks migrated from Awesome-Kindle, packaged for KPM",
    "packages": {},
}


def _run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(str(c) for c in cmd)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def build_repo(
    sources_dir: Path,
    build_dir: Path,
    dist_dir: Path,
    kpm_helper: Path,
    repo_manifest: dict,
) -> int:
    """Packs every package folder under sources_dir and assembles the repo
    index in dist_dir. Returns the number of packages built."""
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    build_dir.mkdir(parents=True)
    dist_dir.mkdir(parents=True)

    (dist_dir / "manifest.json").write_text(json.dumps(repo_manifest))

    package_dirs = sorted(p for p in sources_dir.iterdir() if p.is_dir())
    for package_dir in package_dirs:
        print(f"Packing {package_dir.name}...")
        _run(
            [sys.executable, str(kpm_helper), "package", "pack", str(package_dir), str(build_dir)],
            cwd=REPO_ROOT,
        )

    kpkg_files = sorted(build_dir.glob("*.kpkg"))
    for kpkg_file in kpkg_files:
        print(f"Adding {kpkg_file.name} to repo index...")
        _run(
            [sys.executable, str(kpm_helper), "repo", "add", str(dist_dir), str(kpkg_file)],
            cwd=REPO_ROOT,
        )

    print(f"Built {len(kpkg_files)} package(s) into {dist_dir}")
    return len(kpkg_files)


def main():
    build_repo(SOURCES_DIR, BUILD_DIR, DIST_DIR, KPM_HELPER, dict(REPO_MANIFEST))


if __name__ == "__main__":
    main()
