---
name: migrate-tweak
description: Use when converting an existing Kindle tweak (a KUAL scriptlet, KUAL extension, or standalone app) from Awesome-Kindle or elsewhere into a KPM package for this repository.
---

# Migrating a tweak to a KPM package

## Overview

This skill scaffolds a new package under `sources/<id>/` from an existing,
pre-KPM Kindle tweak, targeting Hackerdude's `KindleModding/KPM` (kindlemodding.org)
— not the unrelated `Gingrspacecadet/KPM` also listed in Awesome-Kindle. It is
interactive by design: destructive, irreversible, or platform-specific
behavior must be confirmed with the user, never guessed.

Read `docs/superpowers/specs/2026-08-12-kpm-repo-design.md` first for the
package conventions (id rules, author attribution, manifest schema) this
repo follows, and look at `sources/disable_ads/` as a worked example of a
migrated single-scriptlet tweak, including how it added backup/restore
behavior the original lacked.

## Inputs

You'll be given one of:
- A raw script URL (e.g. a `.sh` file hosted directly, like a KUAL scriptlet)
- A GitHub repo URL for a KUAL extension (has `config.xml` and/or `menu.json`)
- A GitHub repo URL for a standalone app/binary
- A local file or directory path

## Process

1. **Fetch and classify.** Retrieve the source. Determine which of the three
   types above it is by looking for `config.xml`/`menu.json` (KUAL extension)
   vs a single script (scriptlet) vs a larger app repo (standalone app).
   State which type you've identified and why, before continuing.

2. **Derive the package id.** Lowercase the tweak's name, replace spaces and
   other invalid characters with `_`, keeping only ASCII alphanumerics, `-`,
   and `_` (KPM's own id validation rule — anything else fails to pack).
   Confirm the id with the user if the source name is ambiguous.

3. **Draft `manifest.json`.** Use manifest_version 3. Set `author` to the
   *original* tweak author (never KindleTweaks or yourself), `description`
   from the source's own description/header/README, `version` to `[1, 0, 0]`
   unless the upstream source has its own version you should preserve, and
   `dependencies: []` unless the tweak has a documented dependency on another
   KPM package.

4. **Translate behavior into KPM hooks.**
   - Single scriptlet, one-shot state change (its whole purpose is to flip a
     setting or delete/move files once, with no "run it again" use case — as
     with `disable_ads`): its logic belongs directly in `install.sh` as an
     install-time action, not copied to a launchable location. There is no
     `launch.sh` in this case. `uninstall.sh` must restore whatever state was
     captured/changed (see the backup/restore requirement in step 5), not
     just remove a placed file. `sources/disable_ads/install.sh` and
     `sources/disable_ads/uninstall.sh` are the concrete example.
   - Single scriptlet, on-demand tool (meant to be invoked repeatedly, e.g. a
     utility a user runs from a launcher, not a one-time state change):
     `install.sh` should place it appropriately (commonly
     `/mnt/us/documents/`) and/or `launch.sh` should invoke it, following the
     `kpm launch <id>` convention described in the KPM package docs.
     `uninstall.sh` should remove exactly what `install.sh` placed, and
     nothing the tweak didn't put there itself.
   - KUAL extension: read `menu.json` to see what each menu action actually
     runs, and `config.xml` for metadata/icon. Map each action to either an
     install step (if it should happen once, at install time) or a
     `launch.sh` invocation (if it's meant to run on demand from a
     launcher). Note anything `menu.json` does that KPM doesn't have a direct
     equivalent for, and ask the user how to handle it rather than dropping
     it silently.
   - Standalone app/repo: identify the build/release artifact, how it's
     invoked, and where its data lives. This case has the most unknowns —
     lean towards asking rather than assuming.

5. **Stop and ask before finalizing anything that is destructive,
   irreversible, or platform-specific.** In particular:
   - If the tweak deletes, overwrites, or moves files with no existing undo
     path (as with the original `disable_ads.sh`), propose a backup/restore
     design similar to `sources/disable_ads/install.sh` and
     `sources/disable_ads/uninstall.sh` — back up before destroying, restore
     on uninstall — and confirm the specific backup location and restore
     behavior with the user before writing it.
   - If the tweak reboots, remounts rootfs read-write, or otherwise affects
     the whole device rather than just its own files, confirm whether that
     behavior should be preserved exactly, or made safer, before writing it.
   - If the tweak is hardware-specific (references particular screen
     resolutions, chipsets, or device generations), ask which
     `supported_platforms` values apply rather than defaulting to `null`
     (all platforms).

6. **Scaffold the package.** Create `sources/<id>/` with `manifest.json`, the
   hook scripts from step 4, and any payload files. Write
   `sources/<id>/MIGRATION_NOTES.md` recording: the upstream source URL, the
   original author, the date migrated, and a "Behavior changes from
   upstream" section documenting anything you changed and why (matching the
   style of `sources/disable_ads/MIGRATION_NOTES.md`).

7. **Stop there.** Do not run `tools/build.py`, do not touch `dist/`, and do
   not push or open a PR. Building and publishing are separate, explicit,
   human-triggered steps — tell the user the package is scaffolded and ready
   for their review.

## Quick Reference

| Tweak type | Signal | Install-time behavior | Ask before writing |
|---|---|---|---|
| Scriptlet | Single `.sh` file | `install.sh` places it and/or `launch.sh` invokes it | Any delete/overwrite with no undo path |
| KUAL extension | `config.xml` and/or `menu.json` present | Each menu action maps to an install step or a `launch.sh` invocation | Any `menu.json` action with no KPM equivalent |
| Standalone app | Larger repo, build/release artifacts | Identify artifact, invocation, data location | Almost everything — most unknowns of the three |

## Common Mistakes

- **Attributing the package to KindleTweaks or yourself.** `author` in
  `manifest.json` is always the *original* tweak author (e.g. "Marek" for
  `disable_ads`), never the migrator.
- **Silently choosing a backup/restore design.** Destructive behavior with no
  existing undo path always gets a proposed design confirmed with the user
  first — never write it straight into `install.sh`/`uninstall.sh`.
- **Assuming `supported_platforms: null`.** Only default to all platforms
  when there's no evidence of hardware-specificity; otherwise ask which
  platforms apply.
- **Running `tools/build.py` or touching `dist/`/`gh-pages`.** Scaffolding
  ends at step 6. Building and publishing are separate human-triggered steps.
