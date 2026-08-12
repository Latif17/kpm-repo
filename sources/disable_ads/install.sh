#!/bin/sh
# Name: Disable ADs
# Original author: Marek (https://scriptlets.notmarek.com/scriptlets/disable_ads.sh)
# Migrated for KPM by KindleTweaks. See MIGRATION_NOTES.md for provenance.
#
# Unlike the original scriptlet, this backs up what it removes so
# uninstall.sh can restore ad functionality. If any backup step fails, this
# aborts before touching the real adunits/assets/DB, and removes the partial
# backup dir so a later retry doesn't mistake it for a completed backup.

ADUNITS_DIR="${DISABLE_ADS_ADUNITS_DIR:-/var/local/adunits}"
ASSETS_DIR="${DISABLE_ADS_ASSETS_DIR:-/mnt/us/.assets}"
APPREG_DB="${DISABLE_ADS_APPREG_DB:-/var/local/appreg.db}"
BACKUP_DIR="${DISABLE_ADS_BACKUP_DIR:-/mnt/us/documents/.kpm_disable_ads_backup}"
REBOOT_CMD="${DISABLE_ADS_REBOOT_CMD:-reboot}"

if [ "$1" != "upgrade" ] && [ ! -d "$BACKUP_DIR" ]; then
    echo "Backing up ad assets and current ad-viewable setting..."

    if ! mkdir -p "$BACKUP_DIR"; then
        echo "ERROR: could not create backup dir $BACKUP_DIR - aborting install." >&2
        rm -rf "$BACKUP_DIR"
        exit 1
    fi

    if [ -d "$ADUNITS_DIR" ]; then
        if ! mv "$ADUNITS_DIR" "$BACKUP_DIR/adunits"; then
            echo "ERROR: failed to back up $ADUNITS_DIR - aborting install." >&2
            rm -rf "$BACKUP_DIR"
            exit 1
        fi
    fi

    if [ -d "$ASSETS_DIR" ]; then
        if ! mv "$ASSETS_DIR" "$BACKUP_DIR/assets"; then
            echo "ERROR: failed to back up $ASSETS_DIR - aborting install." >&2
            rm -rf "$BACKUP_DIR"
            exit 1
        fi
    fi

    if ! sqlite3 "$APPREG_DB" "select value from properties where name = 'adunit.viewable';" > "$BACKUP_DIR/adunit_viewable.bak"; then
        echo "ERROR: failed to read adunit.viewable from $APPREG_DB - aborting install." >&2
        rm -rf "$BACKUP_DIR"
        exit 1
    fi

    if [ ! -s "$BACKUP_DIR/adunit_viewable.bak" ]; then
        echo "ERROR: backup of adunit.viewable came back empty - aborting install." >&2
        rm -rf "$BACKUP_DIR"
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
