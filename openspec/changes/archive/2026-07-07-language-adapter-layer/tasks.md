## 1. Adapter package scaffold

- [x] 1.1 Create the `work/adapters/` package structure for `java` and `generic`, plus any shared registry or base contract modules needed to select adapters consistently.
- [x] 1.2 Define the adapter interface, selection result shape, and shared output contract so every adapter emits canonical implementation artifacts, provenance, and evidence.
- [x] 1.3 Add concise package documentation describing the adapter-neutral boundary, default Java selection, and Generic fallback expectations.

## 2. Java adapter implementation

- [x] 2.1 Implement Java project detection using declared repository signals and return auditable selection evidence for both success and rejection cases.
- [x] 2.2 Implement Java scans for project structure, HTTP entrypoints, data shapes, configuration surfaces, dependencies, and test artifacts under the canonical implementation model.
- [x] 2.3 Attach Java-specific metadata only through optional extension fields and verify the required implementation objects remain Core-compatible.

## 3. Generic fallback implementation

- [x] 3.1 Implement Generic adapter detection and fallback plumbing so non-Java or unsupported Java repositories still proceed through implementation extraction.
- [x] 3.2 Implement Generic scans for files, symbols, configuration artifacts, and tests that emit canonical implementation objects with source evidence.
- [x] 3.3 Mark approximate or partial Generic classifications with explicit confidence or partial-status metadata instead of silently omitting uncertain findings.

## 4. Contract alignment and verification

- [x] 4.1 Update the default Java profile, stage definitions, and any runtime-facing adapter registration points so `dic-02` records adapter selection and `dic-04` consumes the shared adapter output contract.
- [x] 4.2 Add focused fixtures, tests, or validation scripts that cover Java selection, Generic fallback, canonical output shape compatibility, and evidence completeness.
- [x] 4.3 Verify that both adapters can feed the downstream traceability contract without adapter-specific field branching and that analyze-only constraints remain unchanged.
