---
name: reviewing-imported-packages
description: Use when importing a third-party package, codebase, or tweak into the project (e.g., migrating packages between environments) to verify safety and compatibility before integration.
---

# Reviewing Imported Packages

## Overview
Importing third-party code into embedded systems carries risks of bricking, file system conflicts, and framework crashes. This skill enforces a strict, multi-point audit before integration.

## When to Use
- Importing a tweak, script, or binary from another project.
- Migrating packages between platforms (e.g., KUAL to kpm).
- Integrating an external repository into the workspace.

## The Audit Protocol
When reviewing an imported package, you MUST audit all of the following areas. Create a todo list.

### 1. Build System & Installation
- **Risk:** Overwriting read-only rootfs or system binaries.
- **Action:** Check `Makefile`, `CMakeLists.txt`, and install scripts. Ensure installation targets are strictly confined to the package directory.

### 2. File System & Hardcoded Paths
- **Risk:** Broken functionality or rogue file creation.
- **Action:** Search for hardcoded absolute paths (`/mnt/`, `/var/`, `/usr/`). Ensure paths are resolved dynamically relative to the execution directory.

### 3. IPC, DBus & Framework Calls
- **Risk:** Using deprecated/changed system calls on new firmware (e.g., `com.lab126.*`).
- **Action:** Find all `lipc-set-prop`, `dbus-send`, or native IPC calls. Verify they are safe for the target OS version.

### 4. Boot & Lifecycle Hooks
- **Risk:** Bricking via bootloop.
- **Action:** Check for `upstart`, `init.d`, or `udev` rules. If a script runs at boot, ensure it cannot block the main framework from starting.

### 5. Dependency Linking
- **Risk:** Missing libraries or ABI conflicts.
- **Action:** Verify required system libraries (GTK, GLib, etc.) exist on the target or are bundled correctly.

## Red Flags - STOP and Audit Further
| Excuse | Reality |
|--------|---------|
| "The C code looks harmless" | A hardcoded `/mnt/` path in a wrapper script breaks the app. |
| "It's just an app, it won't brick" | If an app hooks into init/upstart and hangs, the device bootloops. |
| "I'll fix the paths later" | Audit and patch BEFORE committing the import. |
| "The dbus calls look standard" | Standard calls change between firmware versions. Verify them. |

## Implementation Tips
- Use `grep_search` aggressively for `/mnt`, `/etc`, `/usr`, `lipc`, and `dbus`.
- Review all `.sh` wrapper scripts for dangerous operations (e.g., unchecked `rm -rf`, empty variables in `if` statements).
