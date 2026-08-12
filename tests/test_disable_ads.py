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

    # Plant a plain file (not a directory) at the exact backup path, so
    # `mkdir -p "$BACKUP_DIR"` inside install.sh fails with a real conflict
    # (target exists as non-directory) regardless of which user runs the
    # test - unlike a chmod-based permission trick, this isn't defeated by
    # a process running as root. Since the planted path isn't a directory,
    # install.sh's `[ -d "$BACKUP_DIR" ]` "incomplete backup from a
    # previous attempt" check is false, so it goes straight to `mkdir -p`,
    # which then genuinely fails.
    backup_path = tmp_path / "backup"
    backup_path.write_text("not a directory")

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

    # The script must abort rather than silently continuing.
    assert result.returncode != 0

    # Nothing destructive should have happened: originals survive untouched.
    assert (tmp_path / "adunits" / "unit1.png").exists()
    assert (tmp_path / "assets" / "logo.png").exists()
    assert _read_adunit_viewable(tmp_path / "appreg.db") == "true"

    # No completion marker left behind - a retried install must attempt
    # backup again rather than wrongly believing one already succeeded and
    # skipping straight to destroying real data.
    assert not (backup_path / ".complete").exists()


def test_install_recovers_interrupted_prior_backup_without_losing_data(tmp_path):
    # Simulate a crash mid-install: an earlier run got as far as moving
    # adunits/assets into $BACKUP_DIR but was interrupted (power loss, kill,
    # reboot mid-script) before writing the ".complete" marker or finishing
    # the sqlite3 read. The real ADUNITS_DIR/ASSETS_DIR are already gone,
    # exactly as they would be mid-backup - only $BACKUP_DIR has the data.
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "adunits").mkdir()
    (backup_dir / "adunits" / "unit1.png").write_text("fake asset")
    (backup_dir / "assets").mkdir()
    (backup_dir / "assets" / "logo.png").write_text("fake asset")
    # No .complete marker, no adunit_viewable.bak - the crash happened
    # before those steps.

    _make_appreg_db(tmp_path / "appreg.db", "true")

    env = os.environ.copy()
    env["DISABLE_ADS_ADUNITS_DIR"] = str(tmp_path / "adunits")
    env["DISABLE_ADS_ASSETS_DIR"] = str(tmp_path / "assets")
    env["DISABLE_ADS_APPREG_DB"] = str(tmp_path / "appreg.db")
    env["DISABLE_ADS_BACKUP_DIR"] = str(backup_dir)
    env["DISABLE_ADS_REBOOT_CMD"] = "true"

    result = subprocess.run(
        ["sh", str(PACKAGE_DIR / "install.sh")],
        cwd=PACKAGE_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    # The interrupted attempt's data must never simply vanish. It must end
    # up either restored to its original location (and, if the rest of this
    # run's backup succeeds, re-backed-up from there), or still sitting
    # recoverably inside $BACKUP_DIR if something failed along the way.
    adunits_recoverable = (tmp_path / "backup" / "adunits" / "unit1.png").exists() or (
        tmp_path / "adunits" / "unit1.png"
    ).exists()
    assets_recoverable = (tmp_path / "backup" / "assets" / "logo.png").exists() or (
        tmp_path / "assets" / "logo.png"
    ).exists()

    assert adunits_recoverable, (
        "interrupted-attempt adunits data was lost entirely:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert assets_recoverable, (
        "interrupted-attempt assets data was lost entirely:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


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


def test_install_preserves_true_original_value_across_interrupted_backup_and_upgrade(
    tmp_path,
):
    # Simulate: (1) an install run was interrupted after moving
    # adunits/assets into $BACKUP_DIR and writing a correct
    # adunit_viewable.bak ("true"), but before the .complete marker was
    # written. (2) KPM later calls `install.sh upgrade` as a normal
    # lifecycle event - this skips the whole backup block (guarded by
    # `$1 != upgrade`) but still runs the unconditional bottom section that
    # flips the live DB to "false". (3) A later plain `install.sh` re-run
    # must not lose the true original ("true") value by re-deriving it from
    # the now-"false" live DB.
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "adunits").mkdir()
    (backup_dir / "adunits" / "unit1.png").write_text("fake asset")
    (backup_dir / "assets").mkdir()
    (backup_dir / "assets" / "logo.png").write_text("fake asset")
    (backup_dir / "adunit_viewable.bak").write_text("true")
    # No .complete marker - the interrupted attempt never got that far.
    # No adunits/assets dirs at their original locations - they were
    # already moved into backup, that's the interrupted state.

    # Step 2: the intervening `install.sh upgrade` DB flip already happened,
    # so the live DB is built already showing "false".
    _make_appreg_db(tmp_path / "appreg.db", "false")

    # Step 3: a plain reinstall attempt.
    _run_script("install.sh", tmp_path)

    # The freshly-written adunit_viewable.bak (written after this run moves
    # adunits/assets back into backup) must hold the preserved original
    # ("true"), not a value re-derived from the live DB (which would
    # incorrectly be "false"). Read the file directly, not via the live DB -
    # the live DB correctly ends up "false" after this run's own bottom
    # section flips it, which is expected and not what's being checked here.
    assert (backup_dir / "adunit_viewable.bak").read_text().strip() == "true"
    assert (backup_dir / ".complete").exists()

    # End-to-end check: the preserved value must actually flow through to a
    # real restore, not just sit correctly in a file nobody reads.
    _run_script("uninstall.sh", tmp_path)
    assert _read_adunit_viewable(tmp_path / "appreg.db") == "true"


def test_install_defaults_to_true_when_prior_attempt_left_no_saved_value(tmp_path):
    # Simulate the "hollow backup" state: a previous attempt got far enough
    # to move adunits/assets into $BACKUP_DIR but left no usable record of
    # the original adunit.viewable value (no adunit_viewable.bak at all -
    # e.g. it crashed before writing it, or the file was lost to disk
    # damage). Reaching this state at all proves a prior attempt ran, which
    # means the live DB may already have been flipped to "false" by an
    # intervening `install.sh upgrade` - so the live DB is NOT a safe
    # source for the original value here.
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    (backup_dir / "adunits").mkdir()
    (backup_dir / "adunits" / "unit1.png").write_text("fake asset")
    (backup_dir / "assets").mkdir()
    (backup_dir / "assets" / "logo.png").write_text("fake asset")
    # Deliberately no adunit_viewable.bak and no .complete marker.

    # The live DB is already corrupted by that intervening event.
    _make_appreg_db(tmp_path / "appreg.db", "false")

    result = _run_script("install.sh", tmp_path)

    # Must fall back to the safe default ("true" - the common case for
    # anyone installing this package, and the same default uninstall.sh
    # uses for its own ambiguous case), NOT re-derive it from the live DB
    # (which would wrongly yield "false" and permanently strand the user
    # with ads disabled even after uninstalling). Read the file directly:
    # the live DB legitimately ends up "false" after this run's own bottom
    # section flips it, so it can't answer this question.
    assert (backup_dir / "adunit_viewable.bak").read_text().strip() == "true"
    assert (backup_dir / ".complete").exists()
    assert "defaulting to 'true'" in result.stderr

    # End-to-end: the safe default must actually flow through to a restore.
    _run_script("uninstall.sh", tmp_path)
    assert _read_adunit_viewable(tmp_path / "appreg.db") == "true"


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
