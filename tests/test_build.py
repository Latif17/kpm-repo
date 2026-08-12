import json
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import build as build_module  # noqa: E402


def _make_fixture_package(sources_dir: Path):
    pkg_dir = sources_dir / "hello_world"
    pkg_dir.mkdir(parents=True)
    manifest = {
        "manifest_version": 3,
        "id": "hello_world",
        "name": "Hello World",
        "author": "Test Author",
        "description": "A fixture package for build.py tests",
        "version": [1, 0, 0],
        "dependencies": [],
        "supported_platforms": None,
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest))


def test_build_packs_sources_and_writes_index(tmp_path):
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    _make_fixture_package(sources_dir)

    build_dir = tmp_path / "build"
    dist_dir = tmp_path / "dist"
    kpm_helper = REPO_ROOT / "tools" / "kpm-helper.py"

    count = build_module.build_repo(
        sources_dir, build_dir, dist_dir, kpm_helper, dict(build_module.REPO_MANIFEST)
    )

    assert count == 1

    index = json.loads((dist_dir / "manifest.json").read_text())
    assert index["packages"]["hello_world"]["author"] == "Test Author"
    assert len(index["packages"]["hello_world"]["artifacts"]) == 1

    artifact_rel_path = index["packages"]["hello_world"]["artifacts"][0]["url"]
    artifact_path = dist_dir / artifact_rel_path
    assert artifact_path.exists()

    with tarfile.open(artifact_path) as tf:
        names = tf.getnames()
    assert "manifest.json" in names


def test_build_with_no_sources_returns_zero(tmp_path):
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    build_dir = tmp_path / "build"
    dist_dir = tmp_path / "dist"
    kpm_helper = REPO_ROOT / "tools" / "kpm-helper.py"

    count = build_module.build_repo(
        sources_dir, build_dir, dist_dir, kpm_helper, dict(build_module.REPO_MANIFEST)
    )
    assert count == 0
