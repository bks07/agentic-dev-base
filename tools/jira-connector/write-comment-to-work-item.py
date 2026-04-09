#!/usr/bin/env python3
"""Add a comment to a Jira work item.

Usage:
    python write-comment-to-work-item.py <WORK_ITEM_KEY> <COMMENT_TEXT>
    python write-comment-to-work-item.py <WORK_ITEM_KEY> --stdin

Example:
    python write-comment-to-work-item.py ASD-42 "Spec work started for this work item."
"""

import json
import sys

from jira_client import add_work_item_comment, load_config


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: python write-comment-to-work-item.py <WORK_ITEM_KEY> <COMMENT_TEXT>\n"
            "   or: python write-comment-to-work-item.py <WORK_ITEM_KEY> --stdin",
            file=sys.stderr,
        )
        sys.exit(1)

    work_item_key = sys.argv[1].strip().upper()
    if sys.argv[2] == "--stdin":
        comment_text = sys.stdin.read().strip()
    else:
        comment_text = " ".join(sys.argv[2:]).strip()

    if not comment_text:
        print("Error: comment text must not be empty.", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()

    result = add_work_item_comment(cfg, work_item_key, comment_text)
    print(
        json.dumps(
            {"id": result.get("id"), "work_item_key": work_item_key, "status": "created"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()