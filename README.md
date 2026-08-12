# KindleTweaks KPM Repository

A [KPM](https://kindlemodding.org/kindle-dev/kpm/index.html) repository of Kindle
tweaks, migrated from [Awesome-Kindle](https://github.com/KindleTweaks/Awesome-Kindle)
now that the community is moving away from KUAL (unsupported by the latest Vera
jailbreak).

> [!IMPORTANT]
> **This targets [`KindleModding/KPM`](https://github.com/KindleModding/KPM) by
> Hackerdude** — the tool documented at kindlemodding.org and recommended as of
> `hdnext` for Kindle homebrew distribution. There is a **different, unrelated**
> project also called KPM at
> [`Gingrspacecadet/KPM`](https://github.com/Gingrspacecadet/KPM). This repository
> has nothing to do with that one.

**KindleTweaks is NOT affiliated with KindleModding.**

## Adding this repository to KPM

Once installed, point KPM at the exact manifest file:

```
https://latif17.github.io/kpm-repo/manifest.json
```

## Packages

| Package | Original author | Description |
|---|---|---|
| `disable_ads` | Marek | Disables ads on ad-enabled Kindles, with full restore support on uninstall (the original scriptlet had no undo path). |

Each package's `sources/<id>/MIGRATION_NOTES.md` documents where it came from and
what, if anything, changed from the original tweak during migration.

## Building locally

```
pip install pytest
pytest tests/ -v
python3 tools/build.py
```

Output lands in `dist/` (a repo index `manifest.json` plus `packages/<id>/artifacts/*.kpkg`)
— this is generated, gitignored, and never committed to `main`. CI builds and
publishes it to GitHub Pages on every push to `main`.

## Migrating a new tweak

Package sources are hand-authored, not auto-generated wholesale. Use the
`/migrate-tweak <source>` Claude Code skill in `.claude/skills/migrate-tweak/` to
scaffold a new `sources/<id>/` from an existing tweak (scriptlet, KUAL extension, or
app repo) — it stops and asks before finalizing anything destructive or irreversible
rather than guessing.

## License

This repository's own tooling and build scripts are MIT licensed (`LICENSE`).
Migrated package sources retain their original author's work; see each package's
`MIGRATION_NOTES.md` for attribution.
