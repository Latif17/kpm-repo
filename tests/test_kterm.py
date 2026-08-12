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

import subprocess
import shutil

def test_kterm_install_is_idempotent(tmp_path):
    kterm_dir = REPO_ROOT / "sources" / "kterm"
    dest = tmp_path / "kterm"
    shutil.copytree(kterm_dir, dest)
    
    install_script = dest / "install.sh"
    
    res1 = subprocess.run([str(install_script)], cwd=str(dest), capture_output=True, text=True)
    assert res1.returncode == 0, f"First install failed: {res1.stderr}"
    
    res2 = subprocess.run([str(install_script)], cwd=str(dest), capture_output=True, text=True)
    assert res2.returncode == 0, f"Second install failed (not idempotent): {res2.stderr}"
