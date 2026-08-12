# Vendored `kpm-helper.py`

- **Source:** <https://github.com/KindleModding/KPM/blob/main/kpm-helper.py>
- **Pinned commit:** `ffa767fffadd731bd59f2bca8c83231f4fc0ab2d`
- **License:** CC0 (see file header)
- **Author:** Hackerdude (<https://ko-fi.com/hackerdude>)

This is Hackerdude's official KPM build helper, vendored here so this repo's
build doesn't silently break if upstream changes the CLI or manifest format.

## Updating

1. Pick a new commit from `KindleModding/KPM`.
2. `curl -s -o tools/kpm-helper.py https://raw.githubusercontent.com/KindleModding/KPM/<new-commit-sha>/kpm-helper.py`
3. Update the pinned commit hash above.
4. Run `pytest tests/ -v` and `python3 tools/build.py` to confirm nothing broke.
