---
name: app-resolution
description: "Resolve a Jira Application field value to an app folder and load its constitution. Use when: mapping a Jira work item to a target app, resolving application context, looking up application-mapping.yml, reading constitution.md for product context."
---

# Application Resolution

Resolves the Jira `Application` field value to a concrete app folder under `/apps` and loads the app's product context from its `constitution.md`.

Used by `Manager`, `Specification / Orchestrator`, and indirectly by all agents that receive resolved app context.

## When to Use

- A Jira work item has been fetched and its `Application` field needs to be mapped to a workspace app folder.
- An agent needs the product context (purpose, assumptions, key behaviors) for a specific app.

## Procedure

### Step 1 — Read the Mapping File

Read `/apps/application-mapping.yml`. Structure:

```yaml
applications:
  - name: Team Availability Matrix
    app_folder: team-availability-matrix
```

Each entry maps a Jira `Application` field value (`name`) to a workspace folder (`app_folder`) under `/apps`.

### Step 2 — Match the Application Field

Match the Jira `Application` field value **exactly** (case-sensitive) against `applications[].name`.

| Outcome | Action |
|---------|--------|
| Exactly one match | Proceed with the resolved `app_folder` |
| No match | Stop and report a blocker — the Jira Application value is not mapped |
| Multiple matches | Stop and report a blocker — ambiguous mapping |
| Missing Application field | Stop and report a blocker — value not present on the work item |

### Step 3 — Derive Paths

From the resolved `app_folder`:

- **App repo path:** `apps/<app_folder>` (e.g. `apps/team-availability-matrix`)
- **Constitution path:** `apps/<app_folder>/constitution.md`
- **Specs path:** `specs/` (specs are stored at workspace root, not inside the app folder)

### Step 4 — Load Constitution

Read `apps/<app_folder>/constitution.md` to obtain product context: purpose, assumptions, key behaviors, trust model, and scalability notes.

Prepare a short constitution summary (2–4 sentences) to pass to sub-agents so they don't need to re-read the full file.

### Step 5 — Return Resolved Context

Provide the following to downstream agents:

| Field | Example |
|-------|---------|
| `app_folder` | `team-availability-matrix` |
| `app_repo` | `apps/team-availability-matrix` |
| `constitution_summary` | Short summary of constitution.md |

## Scope Boundary Rules

Once an app is resolved:

- All code inspection and edits must be limited to `apps/<app_folder>/`.
- Never inspect or modify sibling app repos.
- Spec files stay under `specs/` (workspace root) but must be explicitly scoped to the resolved app.
