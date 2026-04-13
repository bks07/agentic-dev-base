# Test Strategy

This file defines the authoritative testing policy for the testing agents. Workflow status handling stays in `/processes/workflow.md`.

## Scope

- Test only inside the selected app repo under `/apps`.
- Derive commands, stack details, and infrastructure from that repo's own files.
- Prefer the smallest reliable test layer for the risk being covered.

## Test Layers

- Unit and component tests: written by `Developing / Unit Tester` during the Coding phase alongside implementation. Run and validated by `Testing / Test Engineer` during the Testing phase.
- Integration tests: added by `Testing / Test Engineer` during the Testing phase to cover seams, services, and edge cases not covered by unit tests.
- E2E tests: browser-level user journeys, preferably with Playwright, written by `Testing / UI Tester` during the Testing phase.
- CI: Ubuntu-based automation of the selected app repo's real test commands.

## Core Rules

1. Keep tests deterministic. Do not use arbitrary sleeps when proper waits or assertions exist.
2. Prefer lower-cost tests before heavier integration or E2E coverage.
3. Use real services or databases only when infrastructure behavior is the thing being validated.
4. Do not implement product features while adding tests.
5. Change production code only for the smallest approved testability improvement.
6. Prefer user-centric selectors for UI tests.
7. Keep CI aligned with the same test contract used locally.
8. Always finish the testing phase with an independent quality review.

## Role Ownership

- `Developing / Unit Tester`: writes unit and component tests during the Coding phase for every implementation task.
- `Testing / Planner`: produces the execution-ready test plan from implementation deliverables before specialists begin work.
- `Testing / Test Engineer`: runs dev-written unit tests, validates coverage, and adds integration or edge-case tests to fill gaps.
- `Testing / UI Tester`: E2E and browser-level journeys.
- `Testing / CI Engineer`: CI workflows, services, caches, and test artifacts.
- `Testing / Test Quality Reviewer`: independent merge-readiness review.
- `Specification / Orchestrator`: required when testing reveals spec maintenance work.
- `Developing / Coder`: fallback file writer only when a testing specialist cannot edit files directly.

## Routing Rules

1. Start the testing phase by sending implementation deliverables to `Testing / Planner` for test plan creation.
2. Send dev-written unit test execution, coverage analysis, and integration test work to `Testing / Test Engineer`.
3. Send browser journeys to `Testing / UI Tester`.
4. Send CI workflow work to `Testing / CI Engineer`.
5. Always send the resulting testing change set to `Testing / Test Quality Reviewer` before approving promotion.
6. Route spec follow-up through `Specification / Orchestrator`, not directly to spec sub-agents.
7. Use `Developing / Coder` only as a fallback writer with exact file content and exact file paths.

## Testing Gate Output

`Testing / Orchestrator` must return:

- `done` when the change is ready to promote,
- `coding` when fixable implementation follow-up is required,
- `blocked` when the workflow cannot continue safely.

Status movement in Jira is governed by `/processes/workflow.md`.
