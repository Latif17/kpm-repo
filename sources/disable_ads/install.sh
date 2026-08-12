#!/bin/sh
# Name: Disable ADs
# Original author: Marek (https://scriptlets.notmarek.com/scriptlets/disable_ads.sh)
# Migrated for KPM by KindleTweaks. See MIGRATION_NOTES.md for provenance.
#
# Unlike the original scriptlet, this backs up what it removes so
# uninstall.sh can restore ad functionality. If any backup step fails, or if
# a previous install attempt was interrupted before completing its backup
# (power loss, kill, reboot mid-script), this restores anything sitting in
# the backup dir back to its original location rather than ever deleting it
# blind - the safe failure mode is "stuck but recoverable in $BACKUP_DIR",
# never "gone".

ADUNITS_DIR="${DISABLE_ADS_ADUNITS_DIR:-/var/local/adunits}"
ASSETS_DIR="${DISABLE_ADS_ASSETS_DIR:-/mnt/us/.assets}"
APPREG_DB="${DISABLE_ADS_APPREG_DB:-/var/local/appreg.db}"
BACKUP_DIR="${DISABLE_ADS_BACKUP_DIR:-/mnt/us/documents/.kpm_disable_ads_backup}"
REBOOT_CMD="${DISABLE_ADS_REBOOT_CMD:-reboot}"

# Moves anything sitting in the backup dir back to its original location,
# then removes the backup dir - but ONLY once everything that needed
# restoring was actually restored. If a restore-mv fails, the backup dir
# (and whatever's still in it) is deliberately left in place for manual
# recovery instead of being deleted. This makes it safe to call whenever
# $BACKUP_DIR might hold data from a partial or interrupted attempt: it
# never deletes anything it hasn't first put back. Returns non-zero if a
# restore step failed and the backup dir was left in place.
_restore_partial_backup() {
    if [ -d "$BACKUP_DIR/adunits" ]; then
        if ! mv "$BACKUP_DIR/adunits" "$ADUNITS_DIR"; then
            echo "ERROR: failed to restore $ADUNITS_DIR from backup - leaving $BACKUP_DIR in place for manual recovery." >&2
            return 1
        fi
    fi
    if [ -d "$BACKUP_DIR/assets" ]; then
        if ! mv "$BACKUP_DIR/assets" "$ASSETS_DIR"; then
            echo "ERROR: failed to restore $ASSETS_DIR from backup - leaving $BACKUP_DIR in place for manual recovery." >&2
            return 1
        fi
    fi
    rm -rf "$BACKUP_DIR"
    return 0
}

if [ "$1" != "upgrade" ] && [ ! -f "$BACKUP_DIR/.complete" ]; then
    echo "Backing up ad assets and current ad-viewable setting..."

    if [ -d "$BACKUP_DIR" ]; then
        echo "Found an incomplete backup from a previous attempt - restoring it before proceeding."
        if ! _restore_partial_backup; then
            echo "ERROR: could not fully restore the previous incomplete backup - aborting to avoid data loss. Manual recovery needed at $BACKUP_DIR." >&2
            exit 1
        fi
    fi

    if ! mkdir -p "$BACKUP_DIR"; then
        echo "ERROR: could not create backup dir $BACKUP_DIR - aborting install." >&2
        _restore_partial_backup
        exit 1
    fi

    if [ -d "$ADUNITS_DIR" ]; then
        if ! mv "$ADUNITS_DIR" "$BACKUP_DIR/adunits"; then
            echo "ERROR: failed to back up $ADUNITS_DIR - aborting install." >&2
            _restore_partial_backup
            exit 1
        fi
    fi

    if [ -d "$ASSETS_DIR" ]; then
        if ! mv "$ASSETS_DIR" "$BACKUP_DIR/assets"; then
            echo "ERROR: failed to back up $ASSETS_DIR - aborting install." >&2
            _restore_partial_backup
            exit 1
        fi
    fi

    if ! sqlite3 "$APPREG_DB" "select value from properties where name = 'adunit.viewable';" > "$BACKUP_DIR/adunit_viewable.bak"; then
        echo "ERROR: failed to read adunit.viewable from $APPREG_DB - aborting install." >&2
        _restore_partial_backup
        exit 1
    fi

    if [ ! -s "$BACKUP_DIR/adunit_viewable.bak" ]; then
        echo "ERROR: backup of adunit.viewable came back empty - aborting install." >&2
        _restore_partial_backup
        exit 1
    fi

    if ! touch "$BACKUP_DIR/.complete"; then
        echo "ERROR: failed to mark backup as complete - aborting install." >&2
        _restore_partial_backup
        exit 1
    fi
fi

echo "Removing adunits folder"
rm -rf "$ADUNITS_DIR"
echo "Removing ad assets"
rm -rf "$ASSETS_DIR"
echo "Updating appreg.db"
sqlite3 "$APPREG_DB" "update properties set value = 'false' where name = 'adunit.viewable';"
echo "Rebooting in 5 seconds :)"
sleep 5
$REBOOT_CMD
