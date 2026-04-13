---
name: jira
description: "Jira work item operations: fetch next or specific work items, transition workflow status, set or clear blocked flag, post comments. Use when: fetching Jira issues, moving a work item to another status, changing Jira workflow state, blocking or unblocking an issue, adding a comment to a Jira issue, posting updates to a work item."
---

# Jira Work Item Operations

Five capabilities for interacting with Jira work items. All use the scripts in `tools/jira-connector/`.

## Prerequisites

- `JIRA_API_TOKEN` must be set in the environment.
- `tools/jira-connector/config.yml` must contain valid Jira connection settings (`base_url`, `user_email`, `project.key`).

## Workflow Status Keys

The following keys are resolved to the actual Jira status names configured in `tools/jira-connector/config.yml`:

| Key | Default Status |
|-----|---------------|
| `next` | Next |
| `specifying` | Specifying |
| `coding` | Coding |
| `testing` | Testing |
| `finalizing` | Finalizing |
| `done` | Done |

You can also pass the exact Jira status name instead of a key.

## Capability 1 — Fetch Next Work Item

Fetch the single highest-ranked work item in the configured intake status (`Next` by default) matching the configured work item type.

### Procedure

```bash
python tools/jira-connector/fetch-ready-work-item.py
```

**Output:** JSON object with `key`, `summary`, `status`, `is_blocked`, `work_item_type`, `description`, and `application`. Prints `null` if no work item is available.

## Capability 2 — Fetch a Work Item by Key

Fetch a single work item's details by its Jira key.

### Procedure

```bash
python tools/jira-connector/fetch-work-item.py <WORK_ITEM_KEY>
```

**Parameters:**
- `WORK_ITEM_KEY` — The Jira issue key (e.g. `ASD-42`).

**Output:** JSON object with `key`, `summary`, `status`, `is_blocked`, `work_item_type`, `description`, and `application`.

## Capability 3 — Transition a Work Item

Move a Jira work item from its current status to a target workflow status. A summary comment describing the reason for the transition is automatically added.

### Procedure

```bash
python tools/jira-connector/transition-work-item.py <WORK_ITEM_KEY> <TARGET_STATUS_OR_WORKFLOW_KEY> "<SUMMARY>"
```

**Parameters:**
- `WORK_ITEM_KEY` — The Jira issue key (e.g. `ASD-42`).
- `TARGET_STATUS_OR_WORKFLOW_KEY` — One of the workflow status keys above or an exact Jira status name.
- `SUMMARY` — A short explanation of why the transition is happening.

**Example:**

```bash
python tools/jira-connector/transition-work-item.py ASD-42 coding "Specification is complete and implementation is starting."
```

**Output:** JSON with `work_item_key`, `from_status`, `to_status`, `comment_id`, and `result`.

## Capability 4 — Set or Clear Blocked Flag

Update the blocked flag on a work item without changing its workflow status. A summary comment is automatically added.

### Procedure

```bash
python tools/jira-connector/set-blocked-flag.py <WORK_ITEM_KEY> <blocked|unblocked> "<SUMMARY>"
```

**Parameters:**
- `WORK_ITEM_KEY` — The Jira issue key (e.g. `ASD-42`).
- `blocked` or `unblocked` — Whether to set or clear the flag.
- `SUMMARY` — A short explanation of why the flag is being changed.

**Example:**

```bash
python tools/jira-connector/set-blocked-flag.py ASD-42 blocked "Waiting on API contract from external team."
```

**Output:** JSON with `work_item_key`, `status`, `is_blocked`, `comment_id`, and `result`.

## Capability 5 — Post a Comment to a Work Item

Add a comment to a Jira work item. Supports inline text or multiline text via stdin.

### Procedure

**Option A — Inline comment:**

```bash
python tools/jira-connector/write-comment-to-work-item.py <WORK_ITEM_KEY> "<COMMENT_TEXT>"
```

**Option B — Multiline comment via stdin (preferred for long or formatted text):**

```bash
python tools/jira-connector/write-comment-to-work-item.py <WORK_ITEM_KEY> --stdin <<'EOF'
<COMMENT_TEXT>
EOF
```

**Parameters:**
- `WORK_ITEM_KEY` — The Jira issue key (e.g. `ASD-42`).
- `COMMENT_TEXT` — The comment body. Supports Markdown-like formatting: headings (`#`), bold (`**text**`), inline code (`` `code` ``), bullet lists (`- item`), ordered lists (`1. item`), and code blocks (`` ``` ``).

**Example:**

```bash
python tools/jira-connector/write-comment-to-work-item.py ASD-42 "Spec work started for this work item."
```

**Output:** JSON with `id`, `work_item_key`, and `status`.

## Error Handling

- If the target status is not a valid transition from the current status, the transition script prints available transitions to stderr and exits with code 1.
- If the comment text is empty, the comment script exits with code 1.
- If `blocked`/`unblocked` state is not one of the two allowed values, the script exits with code 1.
- If Jira credentials are missing or invalid, all scripts exit with code 1 and print an error to stderr.
- If Jira credentials are missing or invalid, both scripts exit with code 1 and print an error to stderr.
