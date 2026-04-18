#!/usr/bin/env python3
"""Initialize a new application repository inside /apps.

Expected usage:
    python3 tools/init_app.py --name "Application Name" git@github.com:owner/repo.git
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = WORKSPACE_ROOT / "apps"
APPLICATION_MAPPING_FILE = APPS_DIR / "application-mapping.yml"
CONSTITUTION_TEMPLATE = WORKSPACE_ROOT / "templates" / "constitution.template.md"
DEVELOP_BRANCH = "develop"
SCAFFOLD_DIRECTORIES = [
    Path("specs/bugfixing"),
    Path("specs/product-areas"),
    Path("specs/rebrushes"),
    Path("specs/technical-initiatives"),
    Path("docs/architecture"),
]


class InitAppError(Exception):
    """Raised when app initialization cannot continue."""


def parse_repo_name(repo_url: str) -> str:
    candidate = repo_url.rstrip("/").split(":")[-1].split("/")[-1]
    if candidate.endswith(".git"):
        candidate = candidate[:-4]

    if not candidate:
        raise InitAppError(
            "Could not determine the repository name from the provided URL. "
            "Pass a valid GitHub SSH URL, for example: git@github.com:owner/repo.git"
        )

    return candidate


def run_git_command(args: list[str], cwd: Path) -> None:
    try:
        subprocess.run(args, cwd=cwd, check=True)
    except FileNotFoundError as exc:
        raise InitAppError("Git is not installed or is not available on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        command = " ".join(args)
        raise InitAppError(f"Command failed: {command}") from exc


def validate_environment() -> None:
    if not APPS_DIR.exists():
        raise InitAppError(f"Apps directory not found: {APPS_DIR}")

    if not CONSTITUTION_TEMPLATE.exists():
        raise InitAppError(
            f"Constitution template not found: {CONSTITUTION_TEMPLATE}"
        )

    if shutil.which("git") is None:
        raise InitAppError("Git is not installed or is not available on PATH.")


def get_current_branch(target_repo: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=target_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def normalize_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        quote = value[0]
        value = value[1:-1]
        if quote == "'":
            value = value.replace("''", "'")
    return value


def quote_yaml_scalar(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def validate_application_name(application_name: str) -> str:
    normalized = application_name.strip()
    if not normalized:
        raise InitAppError("Application name must not be empty.")
    return normalized


def read_application_mapping() -> str:
    if not APPLICATION_MAPPING_FILE.exists():
        return "applications:\n"

    mapping_text = APPLICATION_MAPPING_FILE.read_text(encoding="utf-8")
    if mapping_text.strip() and "applications:" not in mapping_text:
        raise InitAppError(
            f"Invalid application mapping file format: {APPLICATION_MAPPING_FILE}"
        )
    return mapping_text or "applications:\n"


def validate_application_mapping_entry(application_name: str, app_folder: str) -> None:
    mapping_text = read_application_mapping()
    existing_names: set[str] = set()
    existing_folders: set[str] = set()

    for raw_line in mapping_text.splitlines():
        line = raw_line.strip()
        if line.startswith("- name:"):
            existing_names.add(
                normalize_yaml_scalar(line.split(":", 1)[1]).casefold()
            )
        elif line.startswith("app_folder:"):
            existing_folders.add(
                normalize_yaml_scalar(line.split(":", 1)[1]).casefold()
            )

    if application_name.casefold() in existing_names:
        raise InitAppError(
            "The application name already exists in apps/application-mapping.yml. "
            "Pass the exact Jira Application value only once per app."
        )

    if app_folder.casefold() in existing_folders:
        raise InitAppError(
            f"The app folder '{app_folder}' is already mapped in apps/application-mapping.yml."
        )


def update_application_mapping(application_name: str, app_folder: str) -> Path:
    mapping_text = read_application_mapping()
    if not mapping_text.endswith("\n"):
        mapping_text += "\n"

    mapping_text += (
        f"  - name: {quote_yaml_scalar(application_name)}\n"
        f"    app_folder: {quote_yaml_scalar(app_folder)}\n"
    )
    APPLICATION_MAPPING_FILE.write_text(mapping_text, encoding="utf-8")
    return APPLICATION_MAPPING_FILE


def ensure_develop_branch(target_repo: Path) -> None:
    branch_check = subprocess.run(
        ["git", "branch", "--list", DEVELOP_BRANCH],
        cwd=target_repo,
        check=True,
        capture_output=True,
        text=True,
    )

    if branch_check.stdout.strip():
        run_git_command(["git", "checkout", DEVELOP_BRANCH], cwd=target_repo)
    else:
        run_git_command(["git", "checkout", "-b", DEVELOP_BRANCH], cwd=target_repo)

    current_branch = get_current_branch(target_repo)
    if current_branch != DEVELOP_BRANCH:
        raise InitAppError(
            f"Expected active branch '{DEVELOP_BRANCH}', but found '{current_branch or 'none'}'."
        )


def create_constitution_file(target_repo: Path) -> Path:
    constitution_path = target_repo / "constitution.md"

    if constitution_path.exists():
        raise InitAppError(
            f"The cloned repository already contains a constitution file: {constitution_path}"
        )

    shutil.copyfile(CONSTITUTION_TEMPLATE, constitution_path)
    return constitution_path


def create_scaffold_structure(target_repo: Path) -> list[Path]:
    created_directories: list[Path] = []

    for relative_path in SCAFFOLD_DIRECTORIES:
        directory_path = target_repo / relative_path
        directory_path.mkdir(parents=True, exist_ok=True)
        keep_file = directory_path / ".gitkeep"
        keep_file.touch(exist_ok=True)
        created_directories.append(directory_path)

    return created_directories


def init_app(repo_url: str, application_name: str) -> Path:
    validate_environment()

    application_name = validate_application_name(application_name)
    repo_name = parse_repo_name(repo_url)
    validate_application_mapping_entry(application_name, repo_name)
    target_repo = APPS_DIR / repo_name

    if target_repo.exists():
        raise InitAppError(
            f"Repository already exists inside the apps folder: {target_repo}"
        )

    run_git_command(["git", "clone", repo_url, str(target_repo)], cwd=APPS_DIR)
    ensure_develop_branch(target_repo)
    constitution_path = create_constitution_file(target_repo)
    scaffold_directories = create_scaffold_structure(target_repo)
    mapping_path = update_application_mapping(application_name, repo_name)

    print("Application repository initialized successfully.")
    print(f"- Application name: {application_name}")
    print(f"- Repository: {target_repo}")
    print(f"- Active branch: {DEVELOP_BRANCH}")
    print(f"- Constitution file created: {constitution_path}")
    print(f"- Application mapping updated: {mapping_path}")
    print("- Scaffold directories created:")
    for directory_path in scaffold_directories:
        print(f"  - {directory_path.relative_to(target_repo)}")
    print("\nNext steps for the new app repo:")
    print(f"  cd {target_repo}")
    print("  git add constitution.md specs docs")
    print('  git commit -m "Add constitution and app scaffolding"')
    print(f"  git push -u origin {DEVELOP_BRANCH}")
    print("\nNext steps for this workspace repo:")
    print(f"  cd {WORKSPACE_ROOT}")
    print("  git add apps/application-mapping.yml")

    return target_repo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Clone a new application repository into /apps, switch to the develop "
            "branch, seed constitution.md from the workspace template, create "
            "the default specs and docs scaffolding, and register the app in "
            "apps/application-mapping.yml for Jira Application resolution."
        )
    )
    parser.add_argument(
        "--name",
        dest="application_name",
        required=True,
        help=(
            "Human-readable application name. This must exactly match the Jira "
            "Application field value used for this app."
        ),
    )
    parser.add_argument(
        "repo_url",
        help="GitHub SSH URL for the repository, for example git@github.com:owner/repo.git",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        init_app(args.repo_url, args.application_name)
    except InitAppError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
