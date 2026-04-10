# Jira Workflow

This file defines the authoritative Jira workflow for `Manager`.

## Status Flow

Normal flow:

`Next -> Specifying -> Coding -> Testing -> Finalizing -> Done`

## Rules

1. Normal transitions move only left to right.
2. Once a work item enters `Testing`, do not move it back to `Coding` for testing-driven follow-up work.
3. If testing finds fixable implementation work, keep the work item in `Testing` and continue the implementation and testing loop there.
4. Use `Finalizing` for all post-testing work.
5. Move to `Done` only after finalization is complete.
6. If work is blocked, keep the Jira work item in its current status and apply the blocked flag.
7. When blocked work is unblocked, remove the blocked flag.

## Phase Definitions

- `Next`: backlog intake.
- `Specifying`: specification intake and spec maintenance before implementation.
- `Coding`: implementation before the testing gate.
- `Testing`: testing gate, including testing-driven implementation follow-up.
- `Finalizing`: post-testing work, including promotion, spec finalization, and final reporting.
- `Done`: completed work item.

## Manager Requirements

1. `Manager` owns the workflow. All Jira actions go through `Jira Connector`.
2. `Manager` must follow this file when making workflow decisions.
3. Before each normal phase begins, `Manager` transitions the work item to the matching Jira status.
4. `Manager` posts one detailed report per phase outcome: specification, coding, testing, and final cycle reporting.
5. After a passing testing gate, `Manager` must move the work item to `Finalizing` before promotion and spec finalization.
6. When the user starts the workflow with `.`, that authorizes `Manager` to commit and push the tested changes for the selected app repo to `origin/develop` during `Finalizing` without asking for additional user approval.
7. If a blocker occurs, `Manager` must flag the work item without changing its Jira status.
8. When the blocker is cleared, `Manager` must remove the blocked flag.

## Standard Flow

1. Fetch the next work item in `Next`.
2. Move it to `Specifying`.
3. Complete specification and post the specification report.
4. Move it to `Coding`.
5. Complete implementation and post the coding report.
6. Move it to `Testing`.
7. Run the testing gate and post the testing report.
8. If testing requires follow-up implementation, stay in `Testing` and repeat implementation plus testing.
9. When testing passes, move to `Finalizing`.
10. In `Finalizing`, commit and push the tested changes for the selected app repo to `origin/develop` without pausing for user approval, mark implemented specs `DONE`, and post the final cycle report.
11. Move the work item to `Done`.
12. If work becomes blocked at any phase, keep its current status and apply the blocked flag until it is unblocked.
13. Repeat until no work item remains in `Next`.

## Reporting Order

- Specification report before `Coding`.
- Coding report before or at entry to `Testing`.
- Testing report for every testing gate result.
- Final cycle report during `Finalizing`, before `Done`.
