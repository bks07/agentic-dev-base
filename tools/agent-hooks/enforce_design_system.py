#!/usr/bin/env python3
"""Block frontend edits that bypass the selected app's design system."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from hook_utils import allow, collect_content_strings, collect_paths, deny, extract_selected_app_repo, load_payload, normalize_path, read_transcript, WRITE_TOOLS


FRONTEND_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".css", ".scss"}
INLINE_STYLE_PATTERN = re.compile(r"style\s*=\s*\{\s*\{", re.IGNORECASE)
TAILWIND_COLOR_UTILITY_PATTERN = re.compile(
    r"\b(?:bg|text|border|ring|stroke|fill|from|to|via)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b",
    re.IGNORECASE,
)
HEX_COLOR_PATTERN = re.compile(r"(?<![\w-])#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
FUNCTION_COLOR_PATTERN = re.compile(r"\b(?:rgb|rgba|hsl|hsla)\s*\(", re.IGNORECASE)
CSS_VARIABLE_COLOR_DECLARATION_PATTERN = re.compile(
    r"--[a-z0-9-]+\s*:\s*(?:#(?:[0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})|(?:rgb|rgba|hsl|hsla)\s*\([^;]+\))\s*;",
    re.IGNORECASE,
)


def is_frontend_ui_path(path: Path, allowed_root: Path) -> bool:
    try:
        relative = path.relative_to(allowed_root)
    except ValueError:
        return False

    return relative.parts[:1] == ("frontend",) and path.suffix.lower() in FRONTEND_SUFFIXES


def detect_violation(content: str) -> str | None:
    if not content.strip():
        return None

    if INLINE_STYLE_PATTERN.search(content):
        return "This edit introduces inline React styles, which bypass the app design system. Reuse app classes, tokens, or shared components instead."

    if TAILWIND_COLOR_UTILITY_PATTERN.search(content):
        return "This edit introduces Tailwind-style color utilities, but this workspace uses app-local design tokens and reusable classes instead."

    normalized = CSS_VARIABLE_COLOR_DECLARATION_PATTERN.sub("", content)
    if HEX_COLOR_PATTERN.search(normalized) or FUNCTION_COLOR_PATTERN.search(normalized):
        return "This edit introduces hardcoded colors. Use semantic tokens such as var(--text-primary), var(--bg-card), or existing reusable UI primitives instead."

    return None


def main() -> int:
    payload = load_payload()
    if payload.get("tool_name") not in WRITE_TOOLS:
        allow()
        return 0

    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    transcript_text = read_transcript(payload.get("transcript_path"))
    selected_app_repo = extract_selected_app_repo(transcript_text)
    if not selected_app_repo:
        allow()
        return 0

    allowed_root = normalize_path(selected_app_repo, cwd)
    if allowed_root is None:
        allow()
        return 0

    candidate_paths: set[Path] = set()
    collect_paths(payload.get("tool_input"), cwd, candidate_paths)
    if not any(is_frontend_ui_path(path, allowed_root) for path in candidate_paths):
        allow()
        return 0

    content_strings: list[str] = []
    collect_content_strings(payload.get("tool_input"), content_strings)

    for content in content_strings:
        violation = detect_violation(content)
        if violation:
            deny(f"Design system check failed: {violation}")
            return 0

    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
