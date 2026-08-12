import os
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "sources"

def test_all_shell_scripts_are_executable_and_valid():
    """
    Common test to ensure all .sh scripts in all packages are executable
    and do not contain Windows CRLF line endings, which cause hook execution failures.
    """
    packages = [p for p in SOURCES_DIR.iterdir() if p.is_dir()]
    assert len(packages) > 0, "No packages found"

    for package_dir in packages:
        for script in package_dir.glob("*.sh"):
            # Check executable bit
            st = os.stat(script)
            is_executable = bool(st.st_mode & stat.S_IXUSR)
            assert is_executable, f"Script {script.relative_to(REPO_ROOT)} is missing the executable bit (+x)"
            
            # Check for Windows CRLF
            content = script.read_bytes()
            assert b'\r\n' not in content, f"Script {script.relative_to(REPO_ROOT)} contains Windows CRLF line endings"
