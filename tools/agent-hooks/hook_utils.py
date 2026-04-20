#!/usr/bin/env python3
"""Shared helpers for workspace agent hooks."""

from __future__ import annotations

import difflib
import json
import os
import re
import shlex
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

WRITE_TOOLS = {
    "create_file",
    "replace_string_in_file",
    "insert_edit_into_file",
    "delete_file",
    "create_directory",
    "rename_file",
    "move_file",
    "editFiles",
    "createFile",
    "deleteFile",
    "createFolder",
    "renameFile",
}

TERMINAL_TOOLS = {
    "run_in_terminal",
    "runInTerminal",
    "execute/runInTerminal",
    "execution_subagent",
}

PATH_KEYS = {
    "filePath",
    "dirPath",
    "path",
    "oldPath",
    "newPath",
    "destination",
    "source",
    "uri",
    "files",
}

CONTENT_KEYS = {
    "content",
    "newString",
    "newCode",
    "insert_text",
    "newText",
    "text",
}

PATH_FLAG_TOKENS = {"-C", "--manifest-path", "--file", "-f", "--cwd"}


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def read_transcript(transcript_path: str | None) -> str:
    if not transcript_path:
        return ""
    try:
        return Path(transcript_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def extract_selected_app_repo(transcript_text: str) -> str | None:
    matches = re.findall(r"App Repo:\s*([A-Za-z0-9_./-]+)", transcript_text)
    if not matches:
        return None
    return matches[-1].strip().rstrip("/\\")


def normalize_path(raw_path: str, cwd: Path) -> Path | None:
    if not raw_path:
        return None

    candidate = raw_path.strip()
    if not candidate:
        return None

    if candidate.startswith("file://"):
        parsed = urlparse(candidate)
        candidate = unquote(parsed.path)

    path = Path(os.path.expanduser(candidate))
    if not path.is_absolute():
        path = cwd / path

    try:
        return path.resolve(strict=False)
    except OSError:
        return None


def is_within(path: Path, allowed_root: Path) -> bool:
    try:
        path.relative_to(allowed_root)
        return True
    except ValueError:
        return False


def is_terminal_tool(tool_name: object) -> bool:
    if not isinstance(tool_name, str):
        return False
    return tool_name in TERMINAL_TOOLS or "terminal" in tool_name.lower()


def extract_command(tool_input: object) -> str:
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def collect_paths(value: object, cwd: Path, found: set[Path], path_context: bool = False) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in PATH_KEYS:
                collect_paths(nested, cwd, found, path_context=True)
                continue
            collect_paths(nested, cwd, found, path_context=False)
        return

    if isinstance(value, list):
        for item in value:
            collect_paths(item, cwd, found, path_context=path_context)
        return

    if path_context and isinstance(value, str):
        normalized = normalize_path(value, cwd)
        if normalized is not None:
            found.add(normalized)


def _extract_added_text(old_text: str, new_text: str) -> str:
    if not old_text:
        return new_text

    diff = difflib.ndiff(old_text.splitlines(), new_text.splitlines())
    added_lines = [line[2:] for line in diff if line.startswith("+ ")]
    return "\n".join(added_lines)


def collect_content_strings(value: object, found: list[str], parent_key: str | None = None, sibling_old: str = "") -> None:
    if isinstance(value, dict):
        old_string = value.get("oldString") if isinstance(value.get("oldString"), str) else ""
        for key, nested in value.items():
            collect_content_strings(nested, found, parent_key=key, sibling_old=old_string)
        return

    if isinstance(value, list):
        for item in value:
            collect_content_strings(item, found, parent_key=parent_key, sibling_old=sibling_old)
        return

    if parent_key in CONTENT_KEYS and isinstance(value, str):
        if parent_key == "newString":
            found.append(_extract_added_text(sibling_old, value))
        else:
            found.append(value)


def token_maybe_path(token: str) -> bool:
    if not token or token in {"&&", "||", "|", ";", ">", ">>"}:
        return False
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", token):
        return False
    return token.startswith(("/", "./", "../", "~/")) or "/" in token


def extract_command_paths(command: str, cwd: Path) -> set[Path]:
    found: set[Path] = set()
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    previous: str | None = None
    for token in tokens:
        candidate: str | None = None

        if previous in {"cd", "pushd"}:
            candidate = token
        elif previous in PATH_FLAG_TOKENS:
            candidate = token
        elif token_maybe_path(token):
            candidate = token

        if previous == "git" and token == "-C":
            previous = token
            continue

        if candidate:
            normalized = normalize_path(candidate, cwd)
            if normalized is not None:
                found.add(normalized)

        previous = token

    return found


def allow() -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                }
            }
        )
    )


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
