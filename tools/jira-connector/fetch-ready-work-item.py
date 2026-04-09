#!/usr/bin/env python3
"""Fetch the single highest-ranked ready work item.

Returns one JSON object with the work item's key, summary, status,
work item type, component names, and description text extracted from
the Jira Atlassian Document Format.
If no matching work item is in the configured ready status, exits with
code 0 and prints null.

Selection is controlled by `work_item.ready_status` and
`work_item.item_type` in config.yml.

Usage:
    python fetch-ready-work-item.py

Example output:
    {
      "key": "ASD-12",
      "summary": "Calendar virtual values",
      "status": "Ready",
      "work_item_type": "Prompt",
      "description": "As an employee I want ...",
      "components": ["Team Availability Matrix"]
    }
"""

import json

from jira_client import extract_component_names, extract_description_text, load_config, search_work_items


def main() -> None:
    cfg = load_config()
    project_key = cfg["project_key"]
    work_item_type = cfg["work_item_type"]
    ready_status = cfg["ready_status"]

    jql = (
        f'project = "{project_key}" AND issuetype = "{work_item_type}" '
        f'AND status = "{ready_status}" ORDER BY Rank ASC'
    )

    work_items = search_work_items(cfg, jql, max_results=1)

    if not work_items:
        print(json.dumps(None))
        return

    work_item = work_items[0]
    fields = work_item.get("fields", {})
    result = {
        "key": work_item.get("key"),
        "summary": fields.get("summary"),
        "status": fields.get("status", {}).get("name"),
        "work_item_type": fields.get("issuetype", {}).get("name"),
        "description": extract_description_text(fields.get("description")),
        "components": extract_component_names(fields.get("components")),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()