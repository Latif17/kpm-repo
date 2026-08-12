# kterm Migration Notes

- **Upstream source**: https://github.com/bfabiszewski/kterm
- **Original author**: baf
- **Date migrated**: 2026-08-12

## Behavior changes from upstream

- Configured as a KPM package. Installation is now dynamically confined to the execution directory instead of hardcoding `/mnt/us/extensions/kterm`.
- Packaged both `armhf` (for FW >= 5.16.3) and `softfp` (for older FW) binaries. `install.sh` dynamically checks the firmware version and installs the correct binary within the payload folder.
- KPM `launch.sh` explicitly calls the extension's `kterm.sh` script from the local directory to launch the app, enabling KPM's `kpm launch kterm` mechanism.
