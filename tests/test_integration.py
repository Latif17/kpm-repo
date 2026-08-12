import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import build as build_module  # noqa: E402


def test_real_sources_build_into_a_valid_repo_index():
    build_dir = REPO_ROOT / "build"
    dist_dir = REPO_ROOT / "dist"
    kpm_helper = REPO_ROOT / "tools" / "kpm-helper.py"

    count = build_module.build_repo(
        REPO_ROOT / "sources", build_dir, dist_dir, kpm_helper, dict(build_module.REPO_MANIFEST)
    )

    assert count >= 1

    index = json.loads((dist_dir / "manifest.json").read_text())
    assert index["id"] == "kindletweaks"
    assert "disable_ads" in index["packages"]
    assert index["packages"]["disable_ads"]["author"] == "Marek"
