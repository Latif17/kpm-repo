#!/bin/sh
# Name: Disable ADs
# Original author: Marek (https://scriptlets.notmarek.com/scriptlets/disable_ads.sh)
# Migrated for KPM by KindleTweaks. See MIGRATION_NOTES.md for provenance.
#
# Unlike the original scriptlet, this backs up what it removes so
# uninstall.sh can restore ad functionality. Every step that could delete
# or overwrite data is checked before proceeding, and failures leave data
# recoverable rather than lost.

ADUNITS_DIR="${DISABLE_ADS_ADUNITS_DIR:-/var/local/adunits}"
ASSETS_DIR="${DISABLE_ADS_ASSETS_DIR:-/mnt/us/.assets}"
APPREG_DB="${DISABLE_ADS_APPREG_DB:-/var/local/appreg.db}"
BACKUP_DIR="${DISABLE_ADS_BACKUP_DIR:-/mnt/us/documents/.kpm_disable_ads_backup}"
REBOOT_CMD="${DISABLE_ADS_REBOOT_CMD:-reboot}"

# Restores adunits/assets from $BACKUP_DIR back to their original locations,
# then removes $BACKUP_DIR. Never deletes anything it hasn't first
# successfully put back: if a restore mv fails, $BACKUP_DIR (and whatever
# is still inside it) is left in place for manual recovery, and this
# returns non-zero instead of removing it.
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
    if ! rm -rf "$BACKUP_DIR"; then
        echo "ERROR: failed to remove $BACKUP_DIR after restoring its contents." >&2
        return 1
    fi
    if [ -e "$BACKUP_DIR" ]; then
        echo "ERROR: $BACKUP_DIR still exists after attempting to remove it." >&2
        return 1
    fi
    return 0
}

# A backup is only safe to skip re-doing if it fully completed: the
# .complete marker exists AND the saved DB value is actually present.
# A marker with no corresponding value (e.g. partial disk damage) is
# treated as no backup at all.
_backup_is_complete() {
    [ -f "$BACKUP_DIR/.complete" ] && [ -s "$BACKUP_DIR/adunit_viewable.bak" ]
}

if [ "$1" != "upgrade" ] && ! _backup_is_complete; then
    echo "Backing up ad assets and current ad-viewable setting..."

    PRESERVED_ORIGINAL_VALUE=""
    if [ -d "$BACKUP_DIR" ]; then
        echo "Found an incomplete backup from a previous attempt - restoring it before proceeding."
        if [ -s "$BACKUP_DIR/adunit_viewable.bak" ]; then
            # This may be the only surviving record of the true original
            # value (e.g. if an intervening `install.sh upgrade` already
            # flipped the live DB to false) - keep it rather than re-reading
            # the DB below, which could now hold the wrong value.
            PRESERVED_ORIGINAL_VALUE=$(cat "$BACKUP_DIR/adunit_viewable.bak")
        fi
        if ! _restore_partial_backup; then
            echo "ERROR: could not fully restore the previous incomplete backup - aborting to avoid data loss. Manual recovery needed at $BACKUP_DIR." >&2
            exit 1
        fi
    fi

    if ! mkdir -p "$BACKUP_DIR"; then
        echo "ERROR: failed to create backup dir $BACKUP_DIR - aborting install." >&2
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

    if [ -n "$PRESERVED_ORIGINAL_VALUE" ]; then
        printf '%s\n' "$PRESERVED_ORIGINAL_VALUE" > "$BACKUP_DIR/adunit_viewable.bak"
    elif ! sqlite3 "$APPREG_DB" "select value from properties where name = 'adunit.viewable';" > "$BACKUP_DIR/adunit_viewable.bak"; then
        echo "ERROR: failed to read adunit.viewable from $APPREG_DB - aborting install." >&2
        _restore_partial_backup
        exit 1
    fi

    if [ ! -s "$BACKUP_DIR/adunit_viewable.bak" ]; then
        echo "ERROR: adunit_viewable.bak is empty after backup - aborting install." >&2
        _restore_partial_backup
        exit 1
    fi

    if ! touch "$BACKUP_DIR/.complete"; then
        echo "ERROR: failed to mark backup complete - aborting install." >&2
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
