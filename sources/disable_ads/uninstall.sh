#!/bin/sh
# Name: Disable ADs (uninstall / restore)
# Original author: Marek (https://scriptlets.notmarek.com/scriptlets/disable_ads.sh)
# Migrated for KPM by KindleTweaks. See MIGRATION_NOTES.md for provenance.
#
# Restores ad assets and the original ad-viewable setting from the backup
# made by install.sh, since the original scriptlet had no undo path.

ADUNITS_DIR="${DISABLE_ADS_ADUNITS_DIR:-/var/local/adunits}"
ASSETS_DIR="${DISABLE_ADS_ASSETS_DIR:-/mnt/us/.assets}"
APPREG_DB="${DISABLE_ADS_APPREG_DB:-/var/local/appreg.db}"
BACKUP_DIR="${DISABLE_ADS_BACKUP_DIR:-/mnt/us/documents/.kpm_disable_ads_backup}"
REBOOT_CMD="${DISABLE_ADS_REBOOT_CMD:-reboot}"

if [ "$1" = "upgrade" ]; then
    echo "Upgrade in progress, not restoring ads."
    exit 0
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "No backup found at $BACKUP_DIR - nothing to restore."
    echo "Ads were likely already disabled before this package was installed."
    exit 0
fi

echo "Restoring ad assets..."
if [ -d "$BACKUP_DIR/adunits" ]; then
    rm -rf "$ADUNITS_DIR"
    mv "$BACKUP_DIR/adunits" "$ADUNITS_DIR"
fi

if [ -d "$BACKUP_DIR/assets" ]; then
    rm -rf "$ASSETS_DIR"
    mv "$BACKUP_DIR/assets" "$ASSETS_DIR"
fi

if [ -f "$BACKUP_DIR/adunit_viewable.bak" ]; then
    ORIGINAL_VALUE=$(cat "$BACKUP_DIR/adunit_viewable.bak")
    # adunit.viewable only ever holds 'true' or 'false' on the device.
    # Allowlist it before interpolating into SQL below - anything that
    # isn't exactly one of those two values falls back to "true" (the
    # same default already used for the empty/missing case).
    case "$ORIGINAL_VALUE" in
        true|false) ;;
        *) ORIGINAL_VALUE="true" ;;
    esac
    echo "Restoring adunit.viewable to $ORIGINAL_VALUE"
    sqlite3 "$APPREG_DB" "update properties set value = '$ORIGINAL_VALUE' where name = 'adunit.viewable';"
fi

rm -rf "$BACKUP_DIR"

echo "Ads restored. Rebooting in 5 seconds :)"
sleep 5
$REBOOT_CMD
