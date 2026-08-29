# Complete Service Content Architecture 15/65 Implementation Plan

> **For Codex:** Execute this plan inline with test-driven development. Do not publish, import, commit, or push during this task.

**Goal:** Move the production child-service content generator and its evidence registry from the former 37-page release to the authoritative 15-hub / 65-child architecture without weakening content or evidence validation.

**Architecture:** Treat `tools.seo_semantics.complete_service_architecture.build_complete_service_rows()` as the executable source of truth and `processed/complete_service_children.csv` as its checked-in artifact. The generator remains registry-driven: an explicitly supplied architecture can contain any approved inventory, while the no-argument/default path verifies that the checked-in CSV has not drifted from the executable source. Evidence remains a separate JSON registry keyed one-to-one by `destination_id`.

**Tech Stack:** Python 3.10+, standard-library `csv`, `json`, `argparse`, `html`, `hashlib`; `unittest`; JSON Schema documentation.

---

## Task 1: Lock the authoritative default architecture in tests

**Files:**
- Modify: `tools/test_service_page_content.py`
- Modify: `tools/service_page_content.py`

1. Add tests proving the default checked-in architecture contains 65 children, 64 creates, and only `S7-CHILD-HOLIDAY` as reuse.
2. Assert `S5-CHILD-STUMPS` is absent and every `S9`–`S15` destination from the authoritative builder is present.
3. Add a test proving the default loader compares the checked-in CSV with `build_complete_service_rows()` and fails clearly on drift.
4. Run the focused tests and confirm the new assertions fail before implementation.
5. Implement default path constants and a default loader that performs the executable-source/CSV equality check. Preserve the raw explicit-path loader for extensible external registries.
6. Make CLI arguments default to the release pages directory, authoritative architecture, and release evidence registry while retaining explicit overrides.
7. Re-run the focused tests.

## Task 2: Expand and constrain the evidence registry

**Files:**
- Modify: `tools/test_service_page_evidence.py`
- Modify: `seo-content/service-pages/evidence.json`

1. Replace the old fixed-37 assertions with exact one-to-one coverage of the authoritative 65 destinations.
2. Add legacy-specific assertions:
   - no `S5-CHILD-STUMPS` entry;
   - only the S9 stump child may claim exact case WP 8613;
   - only appropriate S10 pond/waterfall children may claim exact case WP 8608;
   - every other S9–S15 item uses audited `service_photo` or `context_photo` and cannot be captioned as completed work;
   - all legacy attachment IDs and source-page IDs belong to the audited allowlists.
3. Run the evidence tests and confirm failure against the 37-entry registry.
4. Remove the obsolete S5 stump entry, preserve the existing S1–S8 entries, and add all 29 S9–S15 entries from the authoritative architecture.
5. Use only the featured media and case/context pools documented in `reviews/legacy_service_scope_audit.md`. Do not add price, duration, brand, warranty, or performance claims.
6. Re-run the evidence tests and content-generator evidence validation.

## Task 3: Document the release contract

**Files:**
- Modify: `seo-content/service-pages/README.md`
- Modify if required by validated shape: `seo-content/service-pages/schema.json`

1. Document the no-argument/default architecture, evidence, pages, and output paths.
2. Document that the current release is 65 child pages but the validator accepts future approved registries without code changes.
3. Document the sole child reuse contract (`S7-CHILD-HOLIDAY`) and that reuse mechanics stay in the importer allowlist, not content JSON.
4. Document evidence caption boundaries: `case_photo` alone may support an exact completed-work claim; `service_photo` and `context_photo` must be described as service/context imagery.
5. Keep the schema registry-driven; change it only if the implementation adds a public source field.

## Task 4: Verify the complete change set

**Files:**
- Test: `tools/test_service_page_content.py`
- Test: `tools/test_service_page_evidence.py`
- Test: `tools/test_complete_service_architecture.py`

1. Run all three focused test modules.
2. Run the generator validation against the checked-in default architecture/evidence and the current pages directory, accepting missing page drafts only where the command is explicitly in registry-validation mode.
3. Check JSON parsing, exact evidence count, exact architecture IDs, reuse count, and obsolete-ID absence with a small read-only script.
4. Inspect `git diff --check` and `git status --short`; do not modify or stage unrelated files.
5. Report changed paths, exact test commands/results, and any remaining content-draft dependency. Do not commit or push.
