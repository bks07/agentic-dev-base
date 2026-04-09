#!/usr/bin/env python3
"""Deny write operations outside the selected app repo for scoped agents."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote


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

MUTATING_COMMAND_PATTERN = re.compile(
    r"""
    (?:^|\b)(
        rm|mv|cp|mkdir|touch|tee|dd|install|ln|truncate|chmod|chown|
        sed\s+-i|perl\s+-i|python\s+.*-m\s+pip\s+install|pip\s+install|
        npm\s+(?:install|i|add|update)|pnpm\s+(?:install|add|update)|
        yarn\s+(?:add|install|up)|bun\s+add|cargo\s+(?:fmt|fix)|
        git\s+(?:add|rm|mv|restore|checkout|switch|commit|merge|rebase|cherry-pick|apply|am|stash|push|tag)
    )\b|>>?|\|\s*tee\b
    """,
    re.VERBOSE,
)

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

    path = Path(candidate)
    if not path.is_absolute():
        path = cwd / path

    try:
        return path.resolve(strict=False)
    except OSError:
        return None


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


def command_is_mutating(command: str) -> bool:
    return bool(MUTATING_COMMAND_PATTERN.search(command))


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

        if previous in {"cd", "pushd", "git"} and previous != "git":
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


def terminal_command_mentions_allowed_repo(command: str, selected_app_repo: str, allowed_root: Path) -> bool:
    return selected_app_repo in command or str(allowed_root) in command


def handle_terminal_tool(payload: dict, cwd: Path, selected_app_repo: str, allowed_root: Path) -> int:
    command = extract_command(payload.get("tool_input"))
    if not command or not command_is_mutating(command):
        allow()
        return 0

    if is_within(cwd, allowed_root):
        allow()
        return 0

    command_paths = extract_command_paths(command, cwd)
    outside_paths = sorted(
        str(path.relative_to(cwd) if is_within(path, cwd) else path)
        for path in command_paths
        if not is_within(path, allowed_root)
    )

    if outside_paths:
        deny(
            "Terminal writes are restricted to the selected app repo "
            f"'{selected_app_repo}'. Blocked path(s): {', '.join(outside_paths)}"
        )
        return 0

    if not terminal_command_mentions_allowed_repo(command, selected_app_repo, allowed_root):
        deny(
            "Terminal write commands must be scoped to the selected app repo "
            f"'{selected_app_repo}', for example via 'cd {selected_app_repo} && ...'"
        )
        return 0

    allow()
    return 0


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


def main() -> int:
    payload = load_payload()
    tool_name = payload.get("tool_name")
    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    transcript_text = read_transcript(payload.get("transcript_path"))
    selected_app_repo = extract_selected_app_repo(transcript_text)

    if tool_name not in WRITE_TOOLS and not is_terminal_tool(tool_name):
        allow()
        return 0

    if not selected_app_repo:
        allow()
        return 0

    allowed_root = normalize_path(selected_app_repo, cwd)
    if allowed_root is None:
        allow()
        return 0

    if is_terminal_tool(tool_name):
        return handle_terminal_tool(payload, cwd, selected_app_repo, allowed_root)

    candidate_paths: set[Path] = set()
    collect_paths(payload.get("tool_input"), cwd, candidate_paths)

    if not candidate_paths:
        allow()
        return 0

    disallowed = sorted(
        str(path.relative_to(cwd) if is_within(path, cwd) else path)
        for path in candidate_paths
        if not is_within(path, allowed_root)
    )

    if disallowed:
        deny(
            "Write access is restricted to the selected app repo "
            f"'{selected_app_repo}'. Blocked path(s): {', '.join(disallowed)}"
        )
        return 0

    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())