import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def test_kterm_payload_exists():
    kterm_dir = REPO_ROOT / "sources" / "kterm"
    payload_dir = kterm_dir / "payload"
    bin_dir = payload_dir / "bin"
    
    assert payload_dir.exists(), "kterm payload directory is missing"
    assert bin_dir.exists(), "kterm payload/bin directory is missing"
    
    # Check that required binaries are present
    assert (bin_dir / "kterm_armhf").exists(), "kterm_armhf binary is missing"
    assert (bin_dir / "kterm_softfp").exists(), "kterm_softfp binary is missing"
