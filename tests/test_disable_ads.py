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


def test_install_aborts_and_cleans_up_on_backup_failure(tmp_path):
    (tmp_path / "adunits").mkdir()
    (tmp_path / "adunits" / "unit1.png").write_text("fake asset")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "logo.png").write_text("fake asset")
    _make_appreg_db(tmp_path / "appreg.db", "true")

    # Make the backup dir's *parent* untraversable so `mkdir -p "$BACKUP_DIR"`
    # inside install.sh genuinely fails with EACCES. (A plain file planted
    # directly at the backup path won't work here: install.sh now clears any
    # stale non-.complete backup dir with `rm -rf "$BACKUP_DIR"` before the
    # mkdir, which would just delete a planted file and let mkdir succeed.)
    restrict_dir = tmp_path / "restrict"
    restrict_dir.mkdir()
    backup_path = restrict_dir / "backup"
    restrict_dir.chmod(0o000)

    try:
        env = os.environ.copy()
        env["DISABLE_ADS_ADUNITS_DIR"] = str(tmp_path / "adunits")
        env["DISABLE_ADS_ASSETS_DIR"] = str(tmp_path / "assets")
        env["DISABLE_ADS_APPREG_DB"] = str(tmp_path / "appreg.db")
        env["DISABLE_ADS_BACKUP_DIR"] = str(backup_path)
        env["DISABLE_ADS_REBOOT_CMD"] = "true"

        result = subprocess.run(
            ["sh", str(PACKAGE_DIR / "install.sh")],
            cwd=PACKAGE_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
    finally:
        restrict_dir.chmod(0o755)

    # The script must abort rather than silently continuing.
    assert result.returncode != 0

    # Nothing destructive should have happened: originals survive untouched.
    assert (tmp_path / "adunits" / "unit1.png").exists()
    assert (tmp_path / "assets" / "logo.png").exists()
    assert _read_adunit_viewable(tmp_path / "appreg.db") == "true"

    # No completion marker and no stray backup dir - a retried install must
    # attempt backup again rather than wrongly believing one already
    # succeeded and skipping straight to destroying real data.
    assert not (backup_path / ".complete").exists()


def test_install_restores_data_when_db_read_fails_after_moves(tmp_path):
    # Reproduces the reviewer's exact repro: both mv steps succeed (real
    # data is sitting inside $BACKUP_DIR), then the sqlite3 read step fails.
    # The failure-cleanup path must move that data back out to its original
    # location rather than deleting the backup dir (and the data inside it)
    # wholesale.
    (tmp_path / "adunits").mkdir()
    (tmp_path / "adunits" / "unit1.png").write_text("fake asset")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "logo.png").write_text("fake asset")
    db_path = tmp_path / "appreg.db"
    _make_appreg_db(db_path, "true")

    # Make the DB unreadable so the sqlite3 select fails only after both
    # mv steps have already completed successfully.
    db_path.chmod(0o000)

    try:
        env = os.environ.copy()
        env["DISABLE_ADS_ADUNITS_DIR"] = str(tmp_path / "adunits")
        env["DISABLE_ADS_ASSETS_DIR"] = str(tmp_path / "assets")
        env["DISABLE_ADS_APPREG_DB"] = str(db_path)
        env["DISABLE_ADS_BACKUP_DIR"] = str(tmp_path / "backup")
        env["DISABLE_ADS_REBOOT_CMD"] = "true"

        result = subprocess.run(
            ["sh", str(PACKAGE_DIR / "install.sh")],
            cwd=PACKAGE_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
    finally:
        db_path.chmod(0o600)

    assert result.returncode != 0

    # The data must be restored to its original location - not lost, and
    # not stuck inside a backup dir that then gets wiped out.
    assert (tmp_path / "adunits" / "unit1.png").exists()
    assert (tmp_path / "assets" / "logo.png").exists()

    # No completion marker and no stray backup dir left behind - a retry
    # must attempt backup again rather than skipping it.
    assert not (tmp_path / "backup" / ".complete").exists()
    assert not (tmp_path / "backup").exists()


def test_uninstall_normalizes_malicious_backup_value(tmp_path):
    _make_appreg_db(tmp_path / "appreg.db", "true")

    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    # A backup file that shouldn't exist in practice (install.sh only ever
    # writes 'true'/'false'), but simulate a corrupted/tampered one to prove
    # uninstall.sh doesn't interpolate it into SQL unchecked.
    (backup_dir / "adunit_viewable.bak").write_text(
        "true'; drop table properties; --"
    )

    result = _run_script("uninstall.sh", tmp_path)

    # Must not have executed the injected SQL - the properties table (and
    # the row in it) must still be intact and readable.
    assert _read_adunit_viewable(tmp_path / "appreg.db") == "true"
    assert result.returncode == 0
