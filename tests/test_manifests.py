import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "sources"

def test_all_manifests_follow_correct_format():
    manifests = list(SOURCES_DIR.glob("*/manifest.json"))
    assert len(manifests) > 0, "No manifests found to test"
    
    expected_keys = {
        "manifest_version",
        "id",
        "name",
        "author",
        "description",
        "version",
        "dependencies",
        "supported_platforms"
    }

    for manifest_path in manifests:
        try:
            data = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON in {manifest_path}: {e}")

        # Check required keys
        missing_keys = expected_keys - set(data.keys())
        assert not missing_keys, f"Manifest {manifest_path} is missing keys: {missing_keys}"

        # Check types and formats
        assert isinstance(data["manifest_version"], int), f"{manifest_path}: manifest_version must be int"
        assert isinstance(data["id"], str), f"{manifest_path}: id must be str"
        assert isinstance(data["name"], str), f"{manifest_path}: name must be str"
        assert isinstance(data["author"], str), f"{manifest_path}: author must be str"
        assert isinstance(data["description"], str), f"{manifest_path}: description must be str"
        
        # Check version array
        version = data["version"]
        assert isinstance(version, list), f"{manifest_path}: version must be a list"
        assert len(version) == 3, f"{manifest_path}: version must have 3 elements"
        assert all(isinstance(v, int) for v in version), f"{manifest_path}: version elements must be ints"

        # Check dependencies
        deps = data["dependencies"]
        assert isinstance(deps, list), f"{manifest_path}: dependencies must be a list"
        for d in deps:
            assert isinstance(d, dict), f"{manifest_path}: dependency must be an object"
            assert "id" in d, f"{manifest_path}: dependency must have 'id'"
            assert isinstance(d["id"], str), f"{manifest_path}: dependency 'id' must be a string"
            if "min" in d and d["min"] is not None:
                assert isinstance(d["min"], list) and len(d["min"]) == 3, f"{manifest_path}: dependency 'min' must be 3-element list"
            if "max" in d and d["max"] is not None:
                assert isinstance(d["max"], list) and len(d["max"]) == 3, f"{manifest_path}: dependency 'max' must be 3-element list"

        # Check supported_platforms
        platforms = data["supported_platforms"]
        if platforms is not None:
            assert isinstance(platforms, list), f"{manifest_path}: supported_platforms must be null or list"
            assert all(isinstance(p, str) for p in platforms), f"{manifest_path}: platforms must be strings"
