import os
import sqlite3
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "sources" / "disable_ads"


def _make_appreg_db(path: Path, initial_value: str):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE properties (name TEXT, value TEXT)")
    conn.execute(
        "INSERT INTO properties (name, value) VALUES ('adunit.viewable', ?)",
        (initial_value,),
    )
    conn.commit()
    conn.close()


def _read_adunit_viewable(db_path: Path) -> str:
    conn = sqlite3.connect(db_path)
    value = conn.execute(
        "select value from properties where name = 'adunit.viewable'"
    ).fetchone()[0]
    conn.close()
    return value


def _run_script(script_name, tmp_path, extra_args=None):
    env = os.environ.copy()
    env["DISABLE_ADS_ADUNITS_DIR"] = str(tmp_path / "adunits")
    env["DISABLE_ADS_ASSETS_DIR"] = str(tmp_path / "assets")
    env["DISABLE_ADS_APPREG_DB"] = str(tmp_path / "appreg.db")
    env["DISABLE_ADS_BACKUP_DIR"] = str(tmp_path / "backup")
    env["DISABLE_ADS_REBOOT_CMD"] = "true"

    cmd = ["sh", str(PACKAGE_DIR / script_name)]
    if extra_args:
        cmd += extra_args

    result = subprocess.run(cmd, cwd=PACKAGE_DIR, env=env, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"{script_name} failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return result


def test_install_disables_ads_and_backs_up(tmp_path):
    (tmp_path / "adunits").mkdir()
    (tmp_path / "adunits" / "unit1.png").write_text("fake asset")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "logo.png").write_text("fake asset")
    _make_appreg_db(tmp_path / "appreg.db", "true")

    _run_script("install.sh", tmp_path)

    assert not (tmp_path / "adunits").exists()
    assert not (tmp_path / "assets").exists()
    assert _read_adunit_viewable(tmp_path / "appreg.db") == "false"

    assert (tmp_path / "backup" / "adunits" / "unit1.png").exists()
    assert (tmp_path / "backup" / "assets" / "logo.png").exists()
    assert (tmp_path / "backup" / "adunit_viewable.bak").read_text().strip() == "true"


def test_uninstall_restores_ads_from_backup(tmp_path):
    (tmp_path / "adunits").mkdir()
    (tmp_path / "adunits" / "unit1.png").write_text("fake asset")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "logo.png").write_text("fake asset")
    _make_appreg_db(tmp_path / "appreg.db", "true")

    _run_script("install.sh", tmp_path)
    _run_script("uninstall.sh", tmp_path)

    assert (tmp_path / "adunits" / "unit1.png").exists()
    assert (tmp_path / "assets" / "logo.png").exists()
    assert _read_adunit_viewable(tmp_path / "appreg.db") == "true"
    assert not (tmp_path / "backup").exists()


def test_uninstall_with_no_backup_warns_and_succeeds(tmp_path):
    _make_appreg_db(tmp_path / "appreg.db", "true")

    result = _run_script("uninstall.sh", tmp_path)

    assert "nothing to restore" in result.stdout.lower()


def test_upgrade_call_skips_backup_and_restore(tmp_path):
    (tmp_path / "adunits").mkdir()
    (tmp_path / "adunits" / "unit1.png").write_text("fake asset")
    _make_appreg_db(tmp_path / "appreg.db", "true")

    _run_script("install.sh", tmp_path)
    backup_mtime_before = (tmp_path / "backup" / "adunit_viewable.bak").stat().st_mtime

    _run_script("install.sh", tmp_path, extra_args=["upgrade"])
    backup_mtime_after = (tmp_path / "backup" / "adunit_viewable.bak").stat().st_mtime
    assert backup_mtime_before == backup_mtime_after

    result = _run_script("uninstall.sh", tmp_path, extra_args=["upgrade"])
    assert (tmp_path / "backup").exists()
    assert "upgrade in progress" in result.stdout.lower()
