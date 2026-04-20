# Agent Hook Quality Gates

This workspace uses command-based agent hooks to enforce deterministic quality checks before code is shipped.

## Implemented use cases

1. **App scope isolation**
   - Script: `enforce_app_scope.py`
   - Prevents agents from writing outside the selected app repo under `/apps`.

2. **Frontend design-system protection**
   - Script: `enforce_design_system.py`
   - Blocks inline React styles, Tailwind-style color utilities, and hardcoded colors in frontend edits so agents keep using app-local tokens and reusable primitives.

3. **Validation-before-commit gate**
   - Script: `enforce_quality_gates.py`
   - Blocks `git commit` and `git push` until fresh, relevant checks have been run after the latest code edits.
   - Frontend changes require tests, type/build verification, linting, and a formatting check.
   - Backend changes require `cargo fmt --check`, `cargo clippy`, and `cargo test`.
   - Python changes require lint and formatting checks such as Ruff or Black.

## Agents covered by the commit/push gate

The quality gate is attached to the agents that can write code or promote changes:

- Manager
- Coding / Coder
- Coding / Designer
- Testing / Test Engineer
- Testing / UI Tester
- Testing / Test Quality Reviewer

## Why these hooks help

These checks are deterministic and fast, which makes them a strong fit for hooks:

- app boundary control,
- unit/integration verification before shipping,
- design-system consistency on frontend work.

## Running the hook tests

From the workspace root:

```bash
/home/bks707/Projects/agentic-dev-base/.venv/bin/python -m unittest discover -s tools/agent-hooks/tests -v
```
