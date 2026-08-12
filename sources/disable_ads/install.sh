#!/bin/sh
# Name: Disable ADs
# Original author: Marek (https://scriptlets.notmarek.com/scriptlets/disable_ads.sh)
# Migrated for KPM by KindleTweaks. See MIGRATION_NOTES.md for provenance.
#
# Unlike the original scriptlet, this backs up what it removes so
# uninstall.sh can restore ad functionality.

ADUNITS_DIR="${DISABLE_ADS_ADUNITS_DIR:-/var/local/adunits}"
ASSETS_DIR="${DISABLE_ADS_ASSETS_DIR:-/mnt/us/.assets}"
APPREG_DB="${DISABLE_ADS_APPREG_DB:-/var/local/appreg.db}"
BACKUP_DIR="${DISABLE_ADS_BACKUP_DIR:-/mnt/us/documents/.kpm_disable_ads_backup}"
REBOOT_CMD="${DISABLE_ADS_REBOOT_CMD:-reboot}"

if [ "$1" != "upgrade" ] && [ ! -d "$BACKUP_DIR" ]; then
    echo "Backing up ad assets and current ad-viewable setting..."
    mkdir -p "$BACKUP_DIR"

    if [ -d "$ADUNITS_DIR" ]; then
        mv "$ADUNITS_DIR" "$BACKUP_DIR/adunits"
    fi

    if [ -d "$ASSETS_DIR" ]; then
        mv "$ASSETS_DIR" "$BACKUP_DIR/assets"
    fi

    sqlite3 "$APPREG_DB" "select value from properties where name = 'adunit.viewable';" > "$BACKUP_DIR/adunit_viewable.bak"
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
