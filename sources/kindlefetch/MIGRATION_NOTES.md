# KindleFetch Migration Notes

- **Upstream source**: https://github.com/justrals/KindleFetch
- **Original author**: justrals
- **Date migrated**: 2026-08-12

## Behavior changes from upstream

- Configured as a KPM package with an explicit dependency on `kterm`.
- KPM `launch.sh` explicitly calls `kterm` to run the `kindlefetch.sh` script, preserving the original KUAL behavior but adapted for the `kpm launch kindlefetch` workflow.
- Installation copies the tool into `/mnt/us/extensions/kindlefetch`. No configs are destroyed on install.
