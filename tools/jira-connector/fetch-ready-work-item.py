#!/usr/bin/env python3
"""Fetch the single highest-ranked work item in the intake status.

Returns one JSON object with the work item's key, summary, status,
blocked state,
work item type, application value, and description text extracted from
the Jira Atlassian Document Format.
If no matching work item is in the configured intake status, exits with
code 0 and prints null.

Selection is controlled by `work_item.workflow.next` and
`work_item.item_type` in config.yml.

Usage:
    python fetch-ready-work-item.py

Example output:
    {
      "key": "ASD-12",
      "summary": "Calendar virtual values",
    "status": "Next",
            "is_blocked": false,
      "work_item_type": "Prompt",
      "description": "As an employee I want ...",
    "application": "Team Availability Matrix"
    }
"""

import json

from jira_client import (
    extract_application_value,
    extract_description_text,
    is_work_item_blocked,
    load_config,
    resolve_blocked_flag_field,
    search_work_items,
)


def main() -> None:
    cfg = load_config()
    project_key = cfg["project_key"]
    work_item_type = cfg["work_item_type"]
    next_status = cfg.get("next_status", cfg["ready_status"])
    application_field = cfg["application_field"]
    blocked_flag_field = resolve_blocked_flag_field(cfg)
    fields = ["summary", "status", "description", "issuetype", application_field]
    if blocked_flag_field:
        fields.append(blocked_flag_field)

    jql = (
        f'project = "{project_key}" AND issuetype = "{work_item_type}" '
        f'AND status = "{next_status}" ORDER BY Rank ASC'
    )

    work_items = search_work_items(cfg, jql, fields=",".join(fields), max_results=1)

    if not work_items:
        print(json.dumps(None))
        return

    work_item = work_items[0]
    fields = work_item.get("fields", {})
    result = {
        "key": work_item.get("key"),
        "summary": fields.get("summary"),
        "status": fields.get("status", {}).get("name"),
        "is_blocked": is_work_item_blocked(cfg, fields),
        "work_item_type": fields.get("issuetype", {}).get("name"),
        "description": extract_description_text(fields.get("description")),
        "application": extract_application_value(fields.get(application_field)),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()