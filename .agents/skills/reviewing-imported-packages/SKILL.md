---
name: reviewing-imported-packages
description: Use when importing a third-party package, codebase, or tweak into the project (e.g., migrating packages between environments) to verify safety and compatibility before integration.
---

# Reviewing Imported Packages

## Overview

Importing third-party code into embedded systems carries risks of bricking, file system conflicts, and framework crashes. This skill enforces a strict, multi-point audit and rigorous verification before integration.

**Core principle:** Audit before committing. Verify compatibility dynamically. Technical correctness and system stability over rapid imports.

## The Review Pattern

```
WHEN importing or reviewing a third-party package:

1. UNDERSTAND: Determine the original environment (e.g., KUAL) and the target environment (e.g., kpm).
2. MANIFEST: Check the package metadata and build structure for correctness (e.g. valid `manifest.json`).
3. AUDIT: Review the source for dangerous or hardcoded behaviors.
4. PATCH: Fix identified issues incrementally.
5. IMPROVE: Add improvements where necessary (e.g., robust explicit error logging, handling edge cases gracefully). Do not blindly port bad code.
6. TEST: Write a package-specific integration test in `tests/` verifying core behavior and payload structure.
7. VERIFY: Build the package locally and run all tests to ensure they pass.
```

## The Audit Protocol

You MUST audit all of the following areas explicitly. Check your findings against this list.

### 1. Build System & Packaging
- **Risk:** Missing metadata, invalid manifests, or overwriting read-only rootfs.
- **Action:** Check `manifest.json`, `Makefile`, and install scripts. Ensure `name`, `version`, `author`, `description` are correctly mapped and present. Ensure installation targets are strictly confined to the package directory.

### 2. File System & Hardcoded Paths
- **Risk:** Broken functionality or rogue file creation on new environments.
- **Action:** Search for hardcoded absolute paths (`/mnt/us/extensions/...`, `/var/`, `/usr/`). Ensure paths are resolved dynamically relative to the execution directory (e.g. `$PKG_DIR` or `dirname "$0"`). Standard paths like `/mnt/us/documents` for user files are acceptable.

### 3. IPC, DBus & Framework Calls
- **Risk:** Using deprecated/changed system calls on new firmware (e.g., `com.lab126.*`).
- **Action:** Find all `lipc-set-prop`, `dbus-send`, or native IPC calls. Verify they are safe for the target OS version.

### 4. Boot & Lifecycle Hooks
- **Risk:** Bricking via bootloop.
- **Action:** Check for `upstart`, `init.d`, or `udev` rules. If a script runs at boot, ensure it cannot block the main framework from starting.

### 5. Dependency Linking
- **Risk:** Missing libraries or ABI conflicts.
- **Action:** Verify required system libraries (GTK, GLib, etc.) exist on the target or are declared as dependencies in the manifest.

### 6. Robustness & Error Handling
- **Risk:** Silent failures or generic system errors that make debugging impossible.
- **Action:** Add explicit error logging (e.g., `echo "ERROR: failed to do X" >&2; exit 1`) to installation scripts and wrappers. Ensure scripts fail gracefully and communicate what went wrong. Do not just rely on `set -e`.

## Forbidden Practices

**NEVER:**
- Commit an imported package before running the build suite.
- Leave hardcoded `/mnt/us/extensions/` paths assuming "it will just work".
- Approve a review with missing required manifest fields (e.g., using `id` instead of `name` for kpm).

**INSTEAD:**
- Use dynamic paths.
- Run `pytest` or `tools/kpm-helper.py package pack <pkg>` to verify packaging.
- Patch wrapper scripts to be portable.

## Verification & Testing

```
AFTER patching the package:
  1. ALWAYS create a package-specific test file in `tests/` (e.g. `test_pkgname.py`) to validate its expected structure or behaviors.
  2. ALWAYS test the package manifest by running the build/pack script.
  3. ALWAYS run the entire integration test suite (e.g., `.venv/bin/pytest tests/ -v`) to validate common tests and your new tests pass.
  4. DO NOT claim the import is successful until tests pass.
```

## Red Flags - STOP and Audit Further
| Excuse | Reality |
|--------|---------|
| "The C code looks harmless" | A hardcoded `/mnt/` path in a wrapper script breaks the app. |
| "It's just an app, it won't brick" | If an app hooks into init/upstart and hangs, the device bootloops. |
| "I'll fix the paths later" | Audit and patch BEFORE committing the import. |
| "The dbus calls look standard" | Standard calls change between firmware versions. Verify them. |
| "The manifest has an 'id' field" | Specific ecosystems (like kpm) strictly require 'name', leading to build failures. |

## Implementation Tips
- Use `grep_search` aggressively for `/mnt`, `/etc`, `/usr`, `lipc`, and `dbus`.
- Review all `.sh` wrapper scripts for dangerous operations (e.g., unchecked `rm -rf`, empty variables in `if` statements).
- Use `kpm-helper.py` or equivalent tools to manually pack and verify the bundle format if tests fail.
