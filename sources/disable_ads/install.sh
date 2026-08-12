#!/bin/sh
# Name: Disable ADs
# Original author: Marek (https://scriptlets.notmarek.com/scriptlets/disable_ads.sh)
# Migrated for KPM by KindleTweaks. See MIGRATION_NOTES.md for provenance.
#
# Unlike the original scriptlet, this backs up what it removes so
# uninstall.sh can restore ad functionality. If any backup step fails, this
# restores anything already moved into the backup dir back to its original
# location, removes the backup dir, and aborts before touching the real
# adunits/assets/DB any further - a failure at any point during backup
# should leave the device exactly as it was, never with data stuck in a
# half-made backup or destroyed outright.

ADUNITS_DIR="${DISABLE_ADS_ADUNITS_DIR:-/var/local/adunits}"
ASSETS_DIR="${DISABLE_ADS_ASSETS_DIR:-/mnt/us/.assets}"
APPREG_DB="${DISABLE_ADS_APPREG_DB:-/var/local/appreg.db}"
BACKUP_DIR="${DISABLE_ADS_BACKUP_DIR:-/mnt/us/documents/.kpm_disable_ads_backup}"
REBOOT_CMD="${DISABLE_ADS_REBOOT_CMD:-reboot}"

# Moves anything that already made it into the backup dir back to its
# original location, then removes the (now-empty, non-restorable) backup
# dir. Used on any backup-step failure so a partial backup never destroys
# data and never lingers as a false "already backed up" marker.
_restore_partial_backup() {
    [ -d "$BACKUP_DIR/adunits" ] && mv "$BACKUP_DIR/adunits" "$ADUNITS_DIR"
    [ -d "$BACKUP_DIR/assets" ] && mv "$BACKUP_DIR/assets" "$ASSETS_DIR"
    rm -rf "$BACKUP_DIR"
}

if [ "$1" != "upgrade" ] && [ ! -f "$BACKUP_DIR/.complete" ]; then
    echo "Backing up ad assets and current ad-viewable setting..."

    # Clear out any stale partial backup from a previous failed/interrupted
    # attempt. Safe: we already know there's no .complete marker, so
    # nothing under here is a real, restorable backup.
    rm -rf "$BACKUP_DIR"

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

    touch "$BACKUP_DIR/.complete"
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
