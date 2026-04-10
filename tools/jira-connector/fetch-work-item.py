#!/usr/bin/env python3
"""Fetch a single Jira work item by key and print its details as JSON.

Usage:
    python fetch-work-item.py <WORK_ITEM_KEY>

Example:
    python fetch-work-item.py ASD-42
"""

import json
import sys

from jira_client import extract_component_names, extract_description_text, fetch_work_item, is_work_item_blocked, load_config


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python fetch-work-item.py <WORK_ITEM_KEY>", file=sys.stderr)
        sys.exit(1)

    work_item_key = sys.argv[1].strip().upper()
    cfg = load_config()
    work_item = fetch_work_item(cfg, work_item_key)

    fields = work_item.get("fields", {})
    result = {
        "key": work_item.get("key"),
        "summary": fields.get("summary"),
        "status": fields.get("status", {}).get("name"),
        "is_blocked": is_work_item_blocked(cfg, fields),
        "work_item_type": fields.get("issuetype", {}).get("name"),
        "description": extract_description_text(fields.get("description")),
        "components": extract_component_names(fields.get("components")),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()