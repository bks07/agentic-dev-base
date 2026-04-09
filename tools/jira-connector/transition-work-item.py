#!/usr/bin/env python3
"""Transition a Jira work item to a target status.

Usage:
    python transition-work-item.py <WORK_ITEM_KEY> <TARGET_STATUS_OR_WORKFLOW_KEY> <SUMMARY_TEXT>

Example:
    python transition-work-item.py ASD-42 coding "Specification is complete and implementation is starting."
"""

import json
import sys

from jira_client import add_work_item_comment, fetch_work_item, load_config, resolve_workflow_status, transition_work_item


def build_transition_comment(from_status: str, to_status: str, summary: str) -> str:
    return f"Workflow transition: {from_status} -> {to_status}\n\nSummary: {summary.strip()}"


def main() -> None:
    if len(sys.argv) < 4:
        print(
            "Usage: python transition-work-item.py <WORK_ITEM_KEY> <TARGET_STATUS_OR_WORKFLOW_KEY> <SUMMARY_TEXT>",
            file=sys.stderr,
        )
        sys.exit(1)

    work_item_key = sys.argv[1].strip().upper()
    target_status_input = sys.argv[2].strip()
    summary = " ".join(sys.argv[3:]).strip()
    cfg = load_config()
    target_status = resolve_workflow_status(cfg, target_status_input)
    current_work_item = fetch_work_item(cfg, work_item_key)
    current_status = current_work_item.get("fields", {}).get("status", {}).get("name", "Unknown")

    transition_work_item(cfg, work_item_key, target_status)
    comment_result = add_work_item_comment(
        cfg,
        work_item_key,
        build_transition_comment(current_status, target_status, summary),
    )
    print(
        json.dumps(
            {
                "work_item_key": work_item_key,
                "from_status": current_status,
                "to_status": target_status,
                "comment_id": comment_result.get("id"),
                "result": "transitioned",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()