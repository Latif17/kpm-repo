from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def test_kindlefetch_payload_exists():
    kindlefetch_dir = REPO_ROOT / "sources" / "kindlefetch"
    payload_dir = kindlefetch_dir / "payload"
    bin_dir = payload_dir / "bin"
    
    assert payload_dir.exists(), "kindlefetch payload directory is missing"
    assert bin_dir.exists(), "kindlefetch payload/bin directory is missing"
    assert (bin_dir / "kindlefetch.sh").exists(), "kindlefetch.sh script is missing"
