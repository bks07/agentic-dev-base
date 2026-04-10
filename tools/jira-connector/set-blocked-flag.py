#!/usr/bin/env python3
"""Set or clear the Jira blocked flag for a work item.

Usage:
    python set-blocked-flag.py <WORK_ITEM_KEY> <blocked|unblocked> <SUMMARY_TEXT>
"""

import json
import sys

from jira_client import add_work_item_comment, fetch_work_item, load_config, set_blocked_flag


def build_flag_comment(current_status: str, blocked: bool, summary: str) -> str:
    state = "ON" if blocked else "OFF"
    return f"Blocked flag: {state} (status unchanged: {current_status})\n\nSummary: {summary.strip()}"


def main() -> None:
    if len(sys.argv) < 4:
        print(
            "Usage: python set-blocked-flag.py <WORK_ITEM_KEY> <blocked|unblocked> <SUMMARY_TEXT>",
            file=sys.stderr,
        )
        sys.exit(1)

    work_item_key = sys.argv[1].strip().upper()
    state = sys.argv[2].strip().lower()
    summary = " ".join(sys.argv[3:]).strip()

    if state not in {"blocked", "unblocked"}:
        print("Error: state must be 'blocked' or 'unblocked'.", file=sys.stderr)
        sys.exit(1)

    blocked = state == "blocked"
    cfg = load_config()
    current_work_item = fetch_work_item(cfg, work_item_key)
    current_status = current_work_item.get("fields", {}).get("status", {}).get("name", "Unknown")

    set_blocked_flag(cfg, work_item_key, blocked)
    comment_result = add_work_item_comment(cfg, work_item_key, build_flag_comment(current_status, blocked, summary))

    print(
        json.dumps(
            {
                "work_item_key": work_item_key,
                "status": current_status,
                "is_blocked": blocked,
                "comment_id": comment_result.get("id"),
                "result": "flag-updated",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()