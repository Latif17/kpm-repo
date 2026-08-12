import os
import tarfile
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def test_kterm_install_hook():
    kterm_dir = REPO_ROOT / "sources" / "kterm"
    install_hook = kterm_dir / "install.sh"
    
    # Check if install hook exists
    assert install_hook.exists(), "install.sh is missing"
    
    # Check if the hook is executable (has +x bit)
    st = os.stat(install_hook)
    is_executable = bool(st.st_mode & stat.S_IXUSR)
    
    assert is_executable, "install.sh is missing the executable bit (+x), which will cause [ERR] could not execute install hook"
    
    # Additionally, we can check for CRLF line endings (Windows) which also break bash scripts
    content = install_hook.read_bytes()
    assert b'\r\n' not in content, "install.sh contains Windows CRLF line endings"
