#!/bin/sh
# Name: Disable ADs
# Original author: Marek (https://scriptlets.notmarek.com/scriptlets/disable_ads.sh)
# Migrated for KPM by KindleTweaks. See MIGRATION_NOTES.md for provenance.
#
# Unlike the original scriptlet, this backs up what it removes so
# uninstall.sh can restore ad functionality. The original adunit_viewable
# DB value is captured and durably written to disk before any risky
# move/delete happens, and is never re-derived from the live DB once a
# backup attempt has started - the live DB can no longer be trusted once
# any part of an install has run (e.g. a later `install.sh upgrade` call
# flips it independently of this backup lifecycle).

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

_backup_is_complete() {
    [ -f "$BACKUP_DIR/.complete" ] && [ -s "$BACKUP_DIR/adunit_viewable.bak" ]
}

if [ "$1" != "upgrade" ] && ! _backup_is_complete; then
    echo "Backing up ad assets and current ad-viewable setting..."

    # Determine the original value to preserve BEFORE touching anything
    # destructive. This is the one and only place the live DB is ever
    # read for this purpose - once $BACKUP_DIR exists at all, a previous
    # attempt has started and the live DB can no longer be trusted (it
    # may already have been flipped to false by an intervening
    # `install.sh upgrade` call).
    ORIGINAL_VALUE=""
    if [ -d "$BACKUP_DIR" ]; then
        if [ -s "$BACKUP_DIR/adunit_viewable.bak" ]; then
            ORIGINAL_VALUE=$(cat "$BACKUP_DIR/adunit_viewable.bak")
        fi
        if [ -z "$ORIGINAL_VALUE" ]; then
            # A previous attempt started but left no usable record of the
            # true original value (e.g. disk damage, or a whitespace-only
            # file). The live DB may already be corrupted by an
            # intervening upgrade, so it is not a safe source here either.
            # Default to "true" - the common case for anyone installing
            # this package - matching uninstall.sh's own default for this
            # same ambiguous situation.
            echo "WARNING: found an incomplete backup with no usable saved value - defaulting to 'true'." >&2
            ORIGINAL_VALUE="true"
        fi
        echo "Found an incomplete backup from a previous attempt - restoring it before proceeding."
        if ! _restore_partial_backup; then
            echo "ERROR: could not fully restore the previous incomplete backup - aborting to avoid data loss. Manual recovery needed at $BACKUP_DIR." >&2
            exit 1
        fi
    else
        if ! ORIGINAL_VALUE=$(sqlite3 "$APPREG_DB" "select value from properties where name = 'adunit.viewable';"); then
            echo "ERROR: failed to read adunit.viewable from $APPREG_DB - aborting install." >&2
            exit 1
        fi
        if [ -z "$ORIGINAL_VALUE" ]; then
            echo "ERROR: adunit.viewable read back empty from $APPREG_DB - aborting install." >&2
            exit 1
        fi
    fi

    if ! mkdir -p "$BACKUP_DIR"; then
        echo "ERROR: failed to create backup dir $BACKUP_DIR - aborting install." >&2
        exit 1
    fi

    # Persist the determined value immediately, before any mv, so an
    # interruption during the moves below can never lose it.
    if ! printf '%s\n' "$ORIGINAL_VALUE" > "$BACKUP_DIR/adunit_viewable.bak"; then
        echo "ERROR: failed to write adunit_viewable.bak - aborting install." >&2
        rm -rf "$BACKUP_DIR"
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
