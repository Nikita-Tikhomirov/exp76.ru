# WordPress Deployer Threat Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close threat re-review findings C1, C2, I1, and I2 without touching production, release ZIPs, or frozen expectations.

**Architecture:** Keep the existing state/journal design. Exact writer requests acquire and retain the same early exclusive lock used by their handler; mutation primitives receive last-moment invariant gates and pinned directory-namespace chains; rollback metadata is restricted to its two producer-owned names. Pure PHP cannot perform descriptor-relative rename/unlink, so POSIX directory handles and `(dev, ino)` continuity narrow the supported threat model to exclude an actively hostile same-UID filesystem process.

**Tech Stack:** PHP 8.3, WordPress hooks, `flock`, `lstat`/`fstat`, `fsync`, dependency-free PHP integration harness, Python `unittest` for the Git byte contract.

**Spec:** `.superpowers/sdd/2026-08-28-exp76-service-hubs-production/deployer-threat-rereview.md`

## Global Constraints

- Use `apply_patch` for every source/test/document edit.
- Strict RED→GREEN for each behavior.
- Do not build a ZIP, commit, browse, or access production.
- Preserve frozen 79-path release expectations and exact registry/importer hashes.

---

### Task 1: Early exclusive writer ownership (C1)

**Files:**
- Modify: `tools/wp_release_deployer/land76-release-deployer/land76-release-deployer.php`
- Test: `tools/wp_release_deployer/tests/state-journal-integration-red.php`

**Interfaces:**
- Produces: `acquire_request_exclusive_lock(): void`; `with_lock(callable): mixed` reuses retained EX ownership.
- Retains: `release_request_lock(): void` as shutdown owner release.

- [x] Add tests where an exact authorized writer sees a partial journal and must reconcile it before a theme sentinel, and where a competing writer cannot acquire EX.
- [x] Run integration harness and record expected RED.
- [x] Make `early_recovery()` acquire retained EX for exact authorized writer POSTs, reconcile immediately, and register shutdown release.
- [x] Make handlers reuse retained EX rather than opening/releasing another lock.
- [x] Run integration harness and record GREEN.

### Task 2: Final Phase-B mutation gates (I1)

**Files:**
- Modify: `tools/wp_release_deployer/land76-release-deployer/land76-release-deployer.php`
- Test: `tools/wp_release_deployer/tests/state-journal-integration-red.php`

**Interfaces:**
- Changes: `atomic_write(..., ?callable $last_gate = null): void` invokes the gate immediately before destination `rename`.
- Changes: `durable_write(..., ?callable $last_gate = null): void` invokes the gate immediately before state `rename`.
- Changes: `clear_journal(?callable $last_gate = null): void` invokes the gate immediately before journal unlink.

- [x] Add adversarial callbacks that drift B at final destination-rename, state-rename, and journal-clear boundaries and count forbidden mutations.
- [x] Run integration harness and record expected RED.
- [x] Thread `assert_phase_invariant('B')` callbacks into apply destination writes, final state save, and journal clear.
- [x] Run integration harness and record GREEN.

### Task 3: Exact rollback artifact names (I2)

**Files:**
- Modify: `tools/wp_release_deployer/land76-release-deployer/land76-release-deployer.php`
- Test: `tools/wp_release_deployer/tests/state-journal-integration-red.php`

**Interfaces:**
- Changes: `validate_backup_metadata(array): void` accepts only `rollback.zip` and `rollback-manifest.json` in their respective fields.

- [x] Add table-driven negatives for `state.json`, `journal.json`, `operation.lock`, swapped artifact names, and an arbitrary safe basename.
- [x] Run integration harness and record expected RED.
- [x] Add the two literal-name checks and distinct-name requirement.
- [x] Run integration harness and record GREEN.

### Task 4: Namespace continuity hardening (C2)

**Files:**
- Modify: `tools/wp_release_deployer/land76-release-deployer/land76-release-deployer.php`
- Test: `tools/wp_release_deployer/tests/state-journal-integration-red.php`

**Interfaces:**
- Produces: directory-chain pin/open, verify, and close helpers retaining directory handles plus `(dev, ino)`.
- Consumes: pinned chains in lock acquisition, destination rename, storage unlink, journal unlink, rollback unlink, and recovery `rmdir` paths.

- [x] Add failpoints that replace a checked destination ancestor and storage-root namespace before the last path operation; assert no out-of-tree write/unlink and no split lock.
- [x] Run integration harness and record expected RED.
- [x] Pin every existing ancestor with a directory handle, revalidate path-to-handle identity immediately before and after namespace mutation, and fail closed on mismatch.
- [x] Document that PHP lacks `openat`/`renameat`/`unlinkat`, so an active same-UID namespace attacker between the final check and pathname syscall is outside the supported model.
- [x] Run integration harness and record GREEN.

### Task 5: Final verification

**Files:**
- Verify all files above plus `.gitattributes` and `tests/test_vendor_git_contract.py`.

- [x] Run PHP lint on all PHP source/tests.
- [x] Run unit, full state/journal integration, all bridge lifecycle scenarios, and Python Git-contract tests.
- [x] Run `git diff --check` plus no-index checks for untracked files.
- [x] Verify registry and importer SHA-256 gates and confirm no ZIP exists in the tool tree.
- [x] Report exact changed files, RED/GREEN evidence, commands, results, and residual POSIX/PHP threat-model limits; do not commit.
