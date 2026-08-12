# Migration notes: disable_ads

- **Upstream source:** https://scriptlets.notmarek.com/scriptlets/disable_ads.sh
- **Original author:** Marek
- **Fetched:** 2026-08-12
- **Listed in:** [Awesome-Kindle](https://github.com/KindleTweaks/Awesome-Kindle) under Quality of Life

## Behavior changes from upstream

The original scriptlet was a one-way operation: it deleted `/var/local/adunits`
and `/mnt/us/.assets`, flipped `adunit.viewable` to `false` in
`/var/local/appreg.db`, and rebooted after 5 seconds, with no way to undo it.

This package keeps the same install behavior (including the unprompted 5-second
reboot — confirmed deliberately, not a guess) but adds a real uninstall path:
`install.sh` backs up the removed folders and the original DB value to
`/mnt/us/documents/.kpm_disable_ads_backup/` before making any changes.
`uninstall.sh` restores from that backup. Both scripts skip the backup/restore
step when called with an `upgrade` argument, since that's a mid-upgrade call,
not a real install or uninstall.

## Known limitations

- `install.sh`'s backup step checks each `mkdir`/`mv`/`sqlite3` call and, on
  failure, moves any already-backed-up data back to its original location
  before aborting (see the `_restore_partial_backup` helper) — a failure
  partway through backup should never lose or strand data.
  `uninstall.sh`'s restore path (the `mv "$BACKUP_DIR/adunits" "$ADUNITS_DIR"`
  / `mv "$BACKUP_DIR/assets" "$ASSETS_DIR"` steps) does **not** have the
  equivalent checks yet — a failed `mv` there is currently unchecked and
  shares the same class of risk that was just fixed in `install.sh`. Fixing
  it is out of scope for this round; flagging it here for a future pass.

## Verified

- [ ] Tested on real hardware (install, confirm ads gone, uninstall, confirm ads
      and original assets restored). Not yet done — no hardware access available
      during migration; do this before recommending the package to anyone.
