"""Shared Jira Cloud REST API client used by all connector scripts."""

import os
import re
import sys
from pathlib import Path

import requests
import yaml


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f) or {}

    jira = cfg.get("jira", {})
    project = cfg.get("project", {})
    work_item = cfg.get("work_item", cfg.get("epic", {}))
    workflow = work_item.get("workflow", {})

    base_url = os.environ.get("JIRA_BASE_URL", jira.get("base_url", ""))
    user_email = os.environ.get("JIRA_USER_EMAIL", jira.get("user_email", ""))
    api_token = os.environ.get("JIRA_API_TOKEN", "")
    project_key = os.environ.get("JIRA_PROJECT_KEY", project.get("key", ""))
    next_status = os.environ.get(
        "JIRA_NEXT_STATUS",
        os.environ.get(
            "JIRA_READY_STATUS",
            workflow.get(
                "next",
                workflow.get("ready", work_item.get("next_status", work_item.get("ready_status", "Next"))),
            ),
        ),
    )
    workflow_statuses = {
        "next": next_status,
        "ready": next_status,
        "specifying": os.environ.get(
            "JIRA_SPECIFYING_STATUS",
            workflow.get(
                "specifying",
                work_item.get("specifying_status", work_item.get("in_progress_status", "Specyfying")),
            ),
        ),
        "coding": os.environ.get(
            "JIRA_CODING_STATUS",
            workflow.get("coding", work_item.get("coding_status", "Coding")),
        ),
        "testing": os.environ.get(
            "JIRA_TESTING_STATUS",
            workflow.get("testing", work_item.get("testing_status", "Testing")),
        ),
        "blocked": os.environ.get(
            "JIRA_BLOCKED_STATUS",
            workflow.get("blocked", work_item.get("blocked_status", "Blocked")),
        ),
        "done": os.environ.get(
            "JIRA_DONE_STATUS",
            workflow.get("done", work_item.get("done_status", "Done")),
        ),
    }
    work_item_type = os.environ.get(
        "JIRA_WORK_ITEM_TYPE",
        work_item.get("item_type", work_item.get("issue_type", "Prompt")),
    )

    if not base_url or not user_email or not api_token:
        print(
            "Error: JIRA_BASE_URL, JIRA_USER_EMAIL, and JIRA_API_TOKEN must be set. "
            "JIRA_API_TOKEN is only read from the environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    return {
        "base_url": base_url.rstrip("/"),
        "user_email": user_email,
        "api_token": api_token,
        "project_key": project_key,
        "next_status": workflow_statuses["next"],
        "ready_status": workflow_statuses["ready"],
        "specifying_status": workflow_statuses["specifying"],
        "coding_status": workflow_statuses["coding"],
        "testing_status": workflow_statuses["testing"],
        "blocked_status": workflow_statuses["blocked"],
        "done_status": workflow_statuses["done"],
        "workflow_statuses": workflow_statuses,
        "work_item_type": work_item_type,
    }


def _session(cfg: dict) -> requests.Session:
    session = requests.Session()
    session.auth = (cfg["user_email"], cfg["api_token"])
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    return session


def fetch_work_item(cfg: dict, work_item_key: str) -> dict:
    session = _session(cfg)
    url = f"{cfg['base_url']}/rest/api/3/issue/{work_item_key}"
    params = {"fields": "summary,status,description,issuetype,components"}
    resp = session.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def search_work_items(
    cfg: dict,
    jql: str,
    fields: str = "summary,status,description,issuetype,components",
    max_results: int = 50,
) -> list[dict]:
    session = _session(cfg)
    url = f"{cfg['base_url']}/rest/api/3/search/jql"
    all_work_items: list[dict] = []
    next_page_token: str | None = None

    while True:
        params: dict = {"jql": jql, "fields": fields, "maxResults": max_results}
        if next_page_token:
            params["nextPageToken"] = next_page_token
        resp = session.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        work_items = data.get("issues", [])
        all_work_items.extend(work_items)
        if data.get("isLast", True):
            break
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return all_work_items


def _normalize_comment_body(body: str) -> str:
    normalized = body.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\\r\\n", "\n").replace("\\n", "\n")
    return normalized.strip()


def _parse_inline_marks(text: str) -> list[dict]:
    parts: list[dict] = []
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")
    index = 0

    for match in pattern.finditer(text):
        if match.start() > index:
            parts.append({"type": "text", "text": text[index:match.start()]})

        token = match.group(0)
        if token.startswith("**") and token.endswith("**"):
            parts.append(
                {
                    "type": "text",
                    "text": token[2:-2],
                    "marks": [{"type": "strong"}],
                }
            )
        elif token.startswith("`") and token.endswith("`"):
            parts.append(
                {
                    "type": "text",
                    "text": token[1:-1],
                    "marks": [{"type": "code"}],
                }
            )
        index = match.end()

    if index < len(text):
        parts.append({"type": "text", "text": text[index:]})

    return [part for part in parts if part.get("text")]


def _paragraph_node(text: str, node_type: str = "paragraph", attrs: dict | None = None) -> dict:
    content = _parse_inline_marks(text) or [{"type": "text", "text": text}]
    node: dict = {"type": node_type, "content": content}
    if attrs:
        node["attrs"] = attrs
    return node


def _code_block_node(lines: list[str]) -> dict:
    text = "\n".join(lines)
    return {
        "type": "codeBlock",
        "content": [{"type": "text", "text": text}],
    }


def _list_node(items: list[str], ordered: bool) -> dict:
    list_type = "orderedList" if ordered else "bulletList"
    content = []
    for item in items:
        content.append(
            {
                "type": "listItem",
                "content": [_paragraph_node(item)],
            }
        )
    return {"type": list_type, "content": content}


def _append_paragraphs(content: list[dict], paragraph_lines: list[str]) -> None:
    for line in paragraph_lines:
        stripped = line.strip()
        if stripped:
            content.append(_paragraph_node(stripped))


def build_comment_adf(body: str) -> dict:
    text = _normalize_comment_body(body)
    if not text:
        return {"version": 1, "type": "doc", "content": []}

    lines = text.split("\n")
    content: list[dict] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    list_type: str | None = None
    code_lines: list[str] = []
    in_code_block = False

    def flush_paragraphs() -> None:
        nonlocal paragraph_lines
        _append_paragraphs(content, paragraph_lines)
        paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items, list_type
        if list_items and list_type:
            content.append(_list_node(list_items, ordered=list_type == "ordered"))
        list_items = []
        list_type = None

    def flush_code_block() -> None:
        nonlocal code_lines
        if code_lines:
            content.append(_code_block_node(code_lines))
        code_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraphs()
            flush_list()
            if in_code_block:
                flush_code_block()
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)

        if not stripped:
            flush_paragraphs()
            flush_list()
            continue

        if heading_match:
            flush_paragraphs()
            flush_list()
            level = min(len(heading_match.group(1)), 6)
            content.append(_paragraph_node(heading_match.group(2).strip(), node_type="heading", attrs={"level": level}))
            continue

        if bullet_match:
            flush_paragraphs()
            if list_type not in (None, "bullet"):
                flush_list()
            list_type = "bullet"
            list_items.append(bullet_match.group(1).strip())
            continue

        if ordered_match:
            flush_paragraphs()
            if list_type not in (None, "ordered"):
                flush_list()
            list_type = "ordered"
            list_items.append(ordered_match.group(1).strip())
            continue

        flush_list()
        paragraph_lines.append(line)

    if in_code_block:
        flush_code_block()
    flush_paragraphs()
    flush_list()

    return {"version": 1, "type": "doc", "content": content}


def add_work_item_comment(cfg: dict, work_item_key: str, body: str) -> dict:
    session = _session(cfg)
    url = f"{cfg['base_url']}/rest/api/3/issue/{work_item_key}/comment"
    payload = {"body": build_comment_adf(body)}
    resp = session.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()


def transition_work_item(cfg: dict, work_item_key: str, target_status: str) -> None:
    session = _session(cfg)
    url = f"{cfg['base_url']}/rest/api/3/issue/{work_item_key}/transitions"

    resp = session.get(url)
    resp.raise_for_status()
    transitions = resp.json().get("transitions", [])

    match = next((t for t in transitions if t["name"].lower() == target_status.lower()), None)
    if not match:
        available = ", ".join(t["name"] for t in transitions)
        print(f"Error: No transition to '{target_status}'. Available: {available}", file=sys.stderr)
        sys.exit(1)

    resp = session.post(url, json={"transition": {"id": match["id"]}})
    resp.raise_for_status()


def extract_description_text(description: dict | None) -> str:
    if not description:
        return ""

    parts: list[str] = []

    def walk(node: dict) -> None:
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        for child in node.get("content", []):
            walk(child)

    walk(description)
    return "\n".join(parts)


def extract_component_names(components: list[dict] | None) -> list[str]:
    if not components:
        return []

    names: list[str] = []
    for component in components:
        name = component.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return names


def resolve_workflow_status(cfg: dict, status_or_key: str) -> str:
    workflow_statuses = cfg.get("workflow_statuses", {})
    normalized = status_or_key.strip().lower().replace("-", "_")
    if normalized in workflow_statuses:
        return workflow_statuses[normalized]
    return status_or_key


# Backward-compatible aliases for older callers.
fetch_issue = fetch_work_item
search_issues = search_work_items
add_comment = add_work_item_comment
transition_issue = transition_work_item
