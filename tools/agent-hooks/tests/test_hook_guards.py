import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = ROOT / "tools" / "agent-hooks"
PYTHON = sys.executable


class HookGuardTests(unittest.TestCase):
    def run_hook(self, script_name: str, payload: dict, transcript: str = "") -> dict:
        with tempfile.TemporaryDirectory() as tmp_dir:
            transcript_path = Path(tmp_dir) / "transcript.log"
            transcript_path.write_text(transcript, encoding="utf-8")
            payload = {**payload, "transcript_path": str(transcript_path)}

            result = subprocess.run(
                [PYTHON, str(HOOKS_DIR / script_name)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(result.stdout.strip(), msg="Expected hook JSON output")
            return json.loads(result.stdout)["hookSpecificOutput"]

    def test_design_system_hook_denies_inline_styles(self) -> None:
        repo = "/tmp/apps/team-availability-matrix"
        payload = {
            "tool_name": "replace_string_in_file",
            "cwd": "/tmp",
            "tool_input": {
                "filePath": f"{repo}/frontend/src/components/ProfileCard.tsx",
                "newString": '<div style={{ color: "#ff0000" }}>Hi</div>',
            },
        }

        output = self.run_hook(
            "enforce_design_system.py",
            payload,
            transcript=f"App Repo: {repo}\n",
        )

        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("design system", output["permissionDecisionReason"].lower())

    def test_design_system_hook_allows_token_based_styling(self) -> None:
        repo = "/tmp/apps/team-availability-matrix"
        payload = {
            "tool_name": "replace_string_in_file",
            "cwd": "/tmp",
            "tool_input": {
                "filePath": f"{repo}/frontend/src/components/ProfileCard.tsx",
                "newString": '<div className="card" data-tone="accent">Hi</div>',
            },
        }

        output = self.run_hook(
            "enforce_design_system.py",
            payload,
            transcript=f"App Repo: {repo}\n",
        )

        self.assertEqual(output["permissionDecision"], "allow")

    def test_quality_gate_denies_commit_without_validation(self) -> None:
        repo = "/tmp/apps/team-availability-matrix"
        payload = {
            "tool_name": "run_in_terminal",
            "cwd": repo,
            "tool_input": {"command": "git commit -m 'ship it'"},
        }
        transcript = "\n".join(
            [
                f"App Repo: {repo}",
                f"replace_string_in_file {{\"filePath\": \"{repo}/frontend/src/App.tsx\"}}",
            ]
        )

        output = self.run_hook("enforce_quality_gates.py", payload, transcript=transcript)

        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("npm run test", output["permissionDecisionReason"])

    def test_quality_gate_denies_commit_without_lint_or_format_checks(self) -> None:
        repo = "/tmp/apps/team-availability-matrix"
        payload = {
            "tool_name": "run_in_terminal",
            "cwd": repo,
            "tool_input": {"command": "git commit -m 'almost verified'"},
        }
        transcript = "\n".join(
            [
                f"App Repo: {repo}",
                f"replace_string_in_file {{\"filePath\": \"{repo}/frontend/src/App.tsx\"}}",
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/frontend && npm run test"}',
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/frontend && npm run typecheck"}',
            ]
        )

        output = self.run_hook("enforce_quality_gates.py", payload, transcript=transcript)

        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("lint", output["permissionDecisionReason"].lower())

    def test_quality_gate_allows_commit_after_required_checks(self) -> None:
        repo = "/tmp/apps/team-availability-matrix"
        payload = {
            "tool_name": "run_in_terminal",
            "cwd": repo,
            "tool_input": {"command": "git commit -m 'verified'"},
        }
        transcript = "\n".join(
            [
                f"App Repo: {repo}",
                f"replace_string_in_file {{\"filePath\": \"{repo}/frontend/src/App.tsx\"}}",
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/frontend && npm run test"}',
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/frontend && npm run typecheck"}',
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/frontend && npm run lint"}',
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/frontend && npx prettier --check src/App.tsx"}',
            ]
        )

        output = self.run_hook("enforce_quality_gates.py", payload, transcript=transcript)

        self.assertEqual(output["permissionDecision"], "allow")

    def test_backend_quality_gate_requires_format_and_lint(self) -> None:
        repo = "/tmp/apps/team-availability-matrix"
        payload = {
            "tool_name": "run_in_terminal",
            "cwd": repo,
            "tool_input": {"command": "git push origin develop"},
        }
        transcript = "\n".join(
            [
                f"App Repo: {repo}",
                f"replace_string_in_file {{\"filePath\": \"{repo}/backend/src/main.rs\"}}",
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/backend && cargo test"}',
            ]
        )

        output = self.run_hook("enforce_quality_gates.py", payload, transcript=transcript)

        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("cargo fmt --check", output["permissionDecisionReason"])

    def test_backend_quality_gate_allows_push_after_format_and_lint(self) -> None:
        repo = "/tmp/apps/team-availability-matrix"
        payload = {
            "tool_name": "run_in_terminal",
            "cwd": repo,
            "tool_input": {"command": "git push origin develop"},
        }
        transcript = "\n".join(
            [
                f"App Repo: {repo}",
                f"replace_string_in_file {{\"filePath\": \"{repo}/backend/src/main.rs\"}}",
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/backend && cargo fmt --check"}',
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/backend && cargo clippy --all-targets --all-features -- -D warnings"}',
                'run_in_terminal {"command": "cd /tmp/apps/team-availability-matrix/backend && cargo test"}',
            ]
        )

        output = self.run_hook("enforce_quality_gates.py", payload, transcript=transcript)

        self.assertEqual(output["permissionDecision"], "allow")


if __name__ == "__main__":
    unittest.main()
