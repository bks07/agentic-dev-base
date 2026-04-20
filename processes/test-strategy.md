# Test Strategy

This file defines the authoritative testing policy for the testing agents. Workflow status handling stays in `/processes/workflow.md`.

## Scope

- Test only inside the selected app repo under `/apps`.
- Derive commands, stack details, and infrastructure from that repo's own files.
- Prefer the smallest reliable test layer for the risk being covered.

## Test Layers

- Unit and component tests: written by `Coding / Coder` during the Coding phase alongside implementation. Run and validated by `Testing / Test Engineer` during the Testing phase.
- Integration tests: added by `Testing / Test Engineer` during the Testing phase to cover seams, services, and edge cases not covered by unit tests.
- E2E tests: browser-level user journeys, preferably with Playwright, written by `Testing / UI Tester` during the Testing phase.
- CI: Ubuntu-based automation of the selected app repo's real test commands, maintained by `Testing / Test Engineer` when needed.

## Core Rules

1. Keep tests deterministic. Do not use arbitrary sleeps when proper waits or assertions exist.
2. Prefer lower-cost tests before heavier integration or E2E coverage.
3. Use real services or databases only when infrastructure behavior is the thing being validated.
4. Do not implement product features while adding tests.
5. Change production code only for the smallest approved testability improvement.
6. Prefer user-centric selectors for UI tests.
7. Keep CI aligned with the same test contract used locally.
8. Before commit or push, run the selected app repo's relevant lint and format checks in addition to its test commands.
9. Always finish the testing phase with an independent quality review.

## Role Ownership

- `Coding / Coder`: writes implementation code and the required unit and component tests during the Coding phase for every implementation task.
- `Testing / Planner`: produces the execution-ready test plan from implementation deliverables before specialists begin work.
- `Testing / Test Engineer`: runs coding-phase unit tests, validates coverage, adds integration or edge-case tests to fill gaps, and handles CI workflow updates when the approved plan calls for them.
- `Testing / UI Tester`: E2E and browser-level journeys.
- `Testing / Test Quality Reviewer`: independent merge-readiness review.
- `Specification / Orchestrator`: required when testing reveals spec maintenance work.

## Routing Rules

1. Start the testing phase by sending implementation deliverables to `Testing / Planner` for test plan creation.
2. Send coding-phase unit test execution, coverage analysis, integration test work, and any approved CI workflow updates to `Testing / Test Engineer`.
3. Send browser journeys to `Testing / UI Tester`.
4. Always send the resulting testing change set to `Testing / Test Quality Reviewer` before approving promotion.
5. Route spec follow-up through `Specification / Orchestrator`, not directly to spec sub-agents.
6. If testing finds fixable implementation issues, return the workflow state `coding` so `Manager` can route the follow-up through `Coding / Orchestrator` instead of using ad hoc fallback writers.

## Testing Gate Output

`Testing / Orchestrator` must return:

- `done` when the change is ready to promote,
- `coding` when fixable implementation follow-up is required,
- `blocked` when the workflow cannot continue safely.

Status movement in Jira is governed by `/processes/workflow.md`.
