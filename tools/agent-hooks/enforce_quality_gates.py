#!/usr/bin/env python3
"""Require deterministic validation before shipping code changes."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from hook_utils import allow, deny, extract_command, extract_selected_app_repo, is_terminal_tool, load_payload, normalize_path, read_transcript


PROTECTED_GIT_COMMAND_PATTERN = re.compile(r"\bgit\s+(?:commit|push)\b", re.IGNORECASE)
WRITE_TOOL_MARKERS = (
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
)
FRONTEND_CHECKS = (
    (
        "frontend unit tests",
        re.compile(r"\b(?:npm\s+run\s+test|npm\s+test|pnpm\s+test|yarn\s+test|vitest(?:\s+run)?|playwright\s+test)\b", re.IGNORECASE),
        "npm run test",
    ),
    (
        "frontend typecheck/build",
        re.compile(r"\b(?:npm\s+run\s+typecheck|pnpm\s+typecheck|yarn\s+typecheck|tsc\s+--noEmit|npm\s+run\s+build|vite\s+build)\b", re.IGNORECASE),
        "npm run typecheck",
    ),
    (
        "frontend lint",
        re.compile(r"\b(?:npm\s+run\s+lint|pnpm\s+lint|yarn\s+lint|npx\s+eslint\b|eslint\b|biome\s+check\b|oxlint\b)\b", re.IGNORECASE),
        "npm run lint",
    ),
    (
        "frontend format check",
        re.compile(r"\b(?:npm\s+run\s+format(?::check)?|pnpm\s+format(?::check)?|yarn\s+format(?::check)?|npx\s+prettier\s+--check\b|prettier\s+--check\b|biome\s+format\b)\b", re.IGNORECASE),
        "npx prettier --check .",
    ),
)
BACKEND_CHECKS = (
    (
        "backend format check",
        re.compile(r"\b(?:cargo\s+fmt\s+--check|rustfmt\b)\b", re.IGNORECASE),
        "cargo fmt --check",
    ),
    (
        "backend lint",
        re.compile(r"\bcargo\s+clippy\b", re.IGNORECASE),
        "cargo clippy --all-targets --all-features -- -D warnings",
    ),
    (
        "backend tests",
        re.compile(r"\bcargo\s+test\b", re.IGNORECASE),
        "cargo test",
    ),
)
PYTHON_CHECKS = (
    (
        "python format check",
        re.compile(r"\b(?:ruff\s+format\s+--check|python\s+-m\s+black\s+--check|black\s+--check)\b", re.IGNORECASE),
        "ruff format --check .",
    ),
    (
        "python lint",
        re.compile(r"\b(?:ruff\s+check|python\s+-m\s+ruff\s+check|flake8\b|pylint\b)\b", re.IGNORECASE),
        "ruff check .",
    ),
)


def last_write_index(transcript_text: str, path_pattern: str) -> int:
    marker_group = "|".join(re.escape(marker) for marker in WRITE_TOOL_MARKERS)
    pattern = re.compile(rf"(?:{marker_group}).{{0,1600}}?{path_pattern}", re.IGNORECASE | re.DOTALL)
    indices = [match.start() for match in pattern.finditer(transcript_text)]
    return max(indices) if indices else -1


def has_validation_after(transcript_text: str, pattern: re.Pattern[str], write_index: int) -> bool:
    return any(match.start() > write_index for match in pattern.finditer(transcript_text))


def gather_missing_checks(transcript_text: str, repo_root: Path) -> list[str]:
    repo = re.escape(str(repo_root))
    frontend_write = last_write_index(
        transcript_text,
        rf"{repo}/frontend/[^\"'\s]+(?:tsx?|jsx?|css|scss|html|json)",
    )
    backend_write = last_write_index(
        transcript_text,
        rf"{repo}/backend/[^\"'\s]+(?:rs|toml|sql)",
    )
    python_write = last_write_index(
        transcript_text,
        rf"{repo}/[^\"'\s]+\.py",
    )

    missing: list[str] = []
    if frontend_write >= 0:
        for _label, pattern, suggested_command in FRONTEND_CHECKS:
            if not has_validation_after(transcript_text, pattern, frontend_write):
                missing.append(f"cd {repo_root}/frontend && {suggested_command}")

    if backend_write >= 0:
        for _label, pattern, suggested_command in BACKEND_CHECKS:
            if not has_validation_after(transcript_text, pattern, backend_write):
                missing.append(f"cd {repo_root}/backend && {suggested_command}")

    if python_write >= 0:
        for _label, pattern, suggested_command in PYTHON_CHECKS:
            if not has_validation_after(transcript_text, pattern, python_write):
                missing.append(f"cd {repo_root} && {suggested_command}")

    deduped: list[str] = []
    for command in missing:
        if command not in deduped:
            deduped.append(command)

    return deduped


def main() -> int:
    payload = load_payload()
    tool_name = payload.get("tool_name")
    if not is_terminal_tool(tool_name):
        allow()
        return 0

    command = extract_command(payload.get("tool_input"))
    if not PROTECTED_GIT_COMMAND_PATTERN.search(command):
        allow()
        return 0

    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    transcript_text = read_transcript(payload.get("transcript_path"))
    selected_app_repo = extract_selected_app_repo(transcript_text)
    if not selected_app_repo:
        allow()
        return 0

    repo_root = normalize_path(selected_app_repo, cwd)
    if repo_root is None:
        allow()
        return 0

    missing_checks = gather_missing_checks(transcript_text, repo_root)
    if missing_checks:
        commands = "; ".join(missing_checks)
        deny(
            "Quality gate failed: recent code changes in the selected app repo still need fresh verification before git commit/push. "
            "Commits and pushes require tests plus lint and format checks relevant to the touched stack. "
            f"Run: {commands}"
        )
        return 0

    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
