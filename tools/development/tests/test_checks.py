"""Test development checks without network access or an installed Go compiler."""

import hashlib
import importlib.util
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SOURCE / "tools/development"))
SPEC = importlib.util.spec_from_file_location("development_check", SOURCE / "tools/development/check.py")
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)
import install_tools


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="vestrelix-development-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "-b", "master")
        self.git("config", "user.name", "Example Contributor")
        self.git("config", "user.email", "contributor@example.com")
        self.git("config", "core.hooksPath", "/dev/null")
        (self.root / "go.mod").write_text("module example.com/tooling-test\n\ngo 1.27.0\n")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.PIPE)

    def write(self, name, content):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def test_no_go_skips_only_application_checks(self):
        with patch.object(checks, "run") as run:
            for mode in ("go", "race", "vuln"):
                checks.go_checks(mode, self.root)
            run.assert_not_called()

    def test_nonignored_untracked_go_is_detected(self):
        self.write("new file.go", "package example\n")
        self.write(".gitignore", "ignored/\n")
        self.write("ignored/example.go", "package example\n")
        self.assertEqual(checks.go_files(self.root), ["new file.go"])

    def test_deleted_go_file_does_not_activate_checks(self):
        self.write("old.go", "package example\n")
        self.git("add", "old.go")
        (self.root / "old.go").unlink()
        self.assertEqual(checks.go_files(self.root), [])

    def stage(self, name, content):
        self.write(name, content)
        self.git("add", "--", name)

    def test_staged_format_reads_index_and_handles_spaces(self):
        staged = b"package example\n"
        self.stage("space name.go", staged.decode())
        self.write("space name.go", "not valid Go")
        with patch.object(checks, "require_go"), patch.object(checks, "run", return_value=subprocess.CompletedProcess([], 0, stdout=staged)) as run:
            checks.staged_format(self.root)
        self.assertEqual(run.call_args.kwargs["input"], staged)
        self.assertEqual((self.root / "space name.go").read_text(), "not valid Go")

    def test_clean_worktree_cannot_hide_bad_index(self):
        self.stage("example.go", "package example;\n")
        self.write("example.go", "package example\n")
        with patch.object(checks, "require_go"), patch.object(checks, "run", return_value=subprocess.CompletedProcess([], 0, stdout=b"package example\n")):
            with self.assertRaisesRegex(ValueError, "Staged Go formatting differs"):
                checks.staged_format(self.root)

    def test_staged_deletion_needs_no_gofmt(self):
        self.stage("example.go", "package example\n")
        self.git("commit", "-m", "test(tooling): synthetic fixture")
        self.git("rm", "example.go")
        with patch.object(checks, "require_go") as require:
            checks.staged_format(self.root)
            require.assert_not_called()

    def test_staged_rename_checks_new_path(self):
        self.stage("old.go", "package example\n")
        self.git("commit", "-m", "test(tooling): synthetic fixture")
        self.git("mv", "old.go", "new name.go")
        with patch.object(checks, "require_go"), patch.object(checks, "run", return_value=subprocess.CompletedProcess([], 0, stdout=b"package example\n")) as run:
            checks.staged_format(self.root)
        run.assert_called_once()

    def test_gofmt_failure_with_empty_stdout_is_not_success(self):
        self.stage("broken.go", "invalid")
        with patch.object(checks, "require_go"), patch.object(checks, "run", side_effect=subprocess.CalledProcessError(2, ["gofmt"], output=b"")):
            with self.assertRaises(subprocess.CalledProcessError):
                checks.staged_format(self.root)

    def test_linter_failure_stops_tests(self):
        self.write("example.go", "package example\n")

        def execute(args, *unused, **kwargs):
            if args[0] == "pinned-linter":
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 0, stdout=b"")

        with patch.object(checks, "require_go"), patch.object(checks, "executable", return_value="pinned-linter"), patch.object(checks, "run", side_effect=execute) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                checks.go_checks("go", self.root)
        self.assertFalse(any(call.args[0][:2] == ["go", "test"] for call in run.call_args_list))

    def test_go_version_must_match_module_release_line(self):
        for version in (b"go1.27.3\n", b"go1.26.10\n", b"go1.28.0\n"):
            with self.subTest(version=version), patch.object(checks, "run", return_value=subprocess.CompletedProcess([], 0, stdout=version)):
                if version.startswith(b"go1.27."):
                    checks.require_go(self.root)
                else:
                    with self.assertRaises(ValueError):
                        checks.require_go(self.root)

    def test_workflow_analyzers_are_deterministic(self):
        with patch.object(checks, "executable", side_effect=lambda name: name), patch.object(checks, "run") as run:
            checks.workflows(self.root)
        self.assertEqual(run.call_args_list[0].args[0], ["actionlint", "-shellcheck=", "-pyflakes="])
        self.assertEqual(run.call_args_list[1].args[0], ["zizmor", "--offline", "--no-progress", "."])

    def test_setup_requires_explicit_policy_on_new_clone(self):
        args = type("Options", (), {"private_policy": None, "public_only": False})()
        with patch.object(checks, "ROOT", self.root):
            with self.assertRaisesRegex(ValueError, "Choose setup"):
                checks.setup(args)

    def test_setup_missing_private_policy_never_falls_back(self):
        self.git("config", "vestrelix.publicationMode", "private")
        policy = self.root.parent / "missing-synthetic-policy.json"
        self.git("config", "vestrelix.privatePolicy", str(policy))
        target = self.root / "tools/publication"
        target.parent.mkdir()
        shutil.copytree(SOURCE / "tools/publication", target, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(SOURCE / ".githooks", self.root / ".githooks")
        args = type("Options", (), {"private_policy": None, "public_only": False})()
        with patch.object(checks, "ROOT", self.root), patch.object(checks, "install") as install:
            with self.assertRaises(subprocess.CalledProcessError):
                checks.setup(args)
            install.assert_not_called()
        self.assertEqual(self.git("config", "--get", "vestrelix.publicationMode").strip(), b"private")

    def test_setup_reuses_public_selection_and_preserves_foreign_hooks(self):
        self.git("config", "vestrelix.publicationMode", "public")
        self.git("config", "core.hooksPath", "/synthetic-hooks")
        target = self.root / "tools/publication"
        target.parent.mkdir()
        shutil.copytree(SOURCE / "tools/publication", target, ignore=shutil.ignore_patterns("__pycache__"))
        args = type("Options", (), {"private_policy": None, "public_only": False})()
        with patch.object(checks, "ROOT", self.root), patch.object(checks, "install") as install:
            with self.assertRaises(subprocess.CalledProcessError):
                checks.setup(args)
            install.assert_not_called()
        self.assertEqual(self.git("config", "--get", "core.hooksPath").strip(), b"/synthetic-hooks")


class InstallerTests(unittest.TestCase):
    def archive(self, kind=tarfile.REGTYPE, duplicate=False):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode="w:gz") as archive:
            for _ in range(2 if duplicate else 1):
                entry = tarfile.TarInfo("tool")
                entry.type = kind
                entry.linkname = "../outside"
                entry.size = 4 if kind == tarfile.REGTYPE else 0
                archive.addfile(entry, io.BytesIO(b"tool") if entry.size else None)
        return data.getvalue()

    def test_only_expected_regular_executable_is_read(self):
        data = self.archive()
        self.assertEqual(install_tools.extract_binary(data, hashlib.sha256(data).hexdigest(), "tool"), b"tool")

    def test_bad_checksum_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "checksum"):
            install_tools.extract_binary(self.archive(), "0" * 64, "tool")

    def test_missing_symlink_and_duplicate_members_are_rejected(self):
        for kind, duplicate, name in ((tarfile.SYMTYPE, False, "tool"), (tarfile.REGTYPE, True, "tool"), (tarfile.REGTYPE, False, "missing")):
            with self.subTest(kind=kind, duplicate=duplicate, name=name):
                data = self.archive(kind, duplicate)
                with self.assertRaises(ValueError):
                    install_tools.extract_binary(data, hashlib.sha256(data).hexdigest(), name)

    def test_oversized_executable_is_rejected(self):
        data = self.archive()
        with patch.object(install_tools, "MAX_BINARY_BYTES", 2):
            with self.assertRaises(ValueError):
                install_tools.extract_binary(data, hashlib.sha256(data).hexdigest(), "tool")

    def test_missing_pinned_tool_does_not_use_path(self):
        with tempfile.TemporaryDirectory(prefix="vestrelix-tools-test-") as directory:
            with patch.dict(os.environ, {"XDG_CACHE_HOME": directory}):
                with self.assertRaisesRegex(ValueError, "make setup"):
                    install_tools.executable("actionlint")

    def test_all_supported_platforms_have_pinned_checksums(self):
        for spec in install_tools.specifications().values():
            self.assertEqual(set(spec["archives"]), {"darwin-arm64", "darwin-amd64", "linux-arm64", "linux-amd64"})
            for asset in spec["archives"].values():
                self.assertRegex(asset["sha256"], r"^[a-f0-9]{64}$")


class HookTests(unittest.TestCase):
    def test_publication_failure_stops_development_checks(self):
        for name in ("pre-commit", "pre-push"):
            with self.subTest(hook=name), tempfile.TemporaryDirectory(prefix="vestrelix-hook-test-") as directory:
                root = Path(directory)
                (root / "tools/publication").mkdir(parents=True)
                (root / "tools/publication/check.py").write_text("raise SystemExit(9)\n")
                (root / "tools/development").mkdir(parents=True)
                (root / "tools/development/check.py").write_text("from pathlib import Path\nPath('ran-development').touch()\n")
                result = subprocess.run(["sh", str(SOURCE / ".githooks" / name)], cwd=root, input=b"synthetic input\n", capture_output=True)
                self.assertEqual(result.returncode, 9)
                self.assertFalse((root / "ran-development").exists())

    def test_pre_push_preserves_publication_stdin(self):
        with tempfile.TemporaryDirectory(prefix="vestrelix-hook-test-") as directory:
            root = Path(directory)
            for name in ("publication", "development"):
                (root / "tools" / name).mkdir(parents=True)
            (root / "tools/publication/check.py").write_text("import sys\nfrom pathlib import Path\nPath('received').write_bytes(sys.stdin.buffer.read())\n")
            (root / "tools/development/check.py").write_text("raise SystemExit(0)\n")
            data = b"refs/heads/example " + b"a" * 40 + b" refs/heads/example " + b"0" * 40 + b"\n"
            result = subprocess.run(["sh", str(SOURCE / ".githooks/pre-push")], cwd=root, input=data, capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual((root / "received").read_bytes(), data)


class GoWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = (SOURCE / ".github/workflows/go.yml").read_text()
        blocks = workflow.split("python3 - <<'PY'\n")[1:]
        cls.detect, cls.gate = [textwrap.dedent(re.split(r"(?m)^\s*PY\s*$", block, maxsplit=1)[0]) for block in blocks]

    def gate_result(self, source="success", present="true", checks_result="success", codeql="success"):
        env = dict(os.environ, SOURCE_RESULT=source, SOURCE_PRESENT=present, CHECKS_RESULT=checks_result, CODEQL_RESULT=codeql)
        return subprocess.run([sys.executable, "-c", self.gate], env=env, capture_output=True).returncode

    def test_no_source_requires_successful_detection(self):
        self.assertEqual(self.gate_result(present="false", checks_result="skipped", codeql="skipped"), 0)
        for source in ("failure", "cancelled", "skipped"):
            self.assertNotEqual(self.gate_result(source=source, present="false"), 0)
        self.assertNotEqual(self.gate_result(present=""), 0)

    def test_go_source_requires_all_applicable_jobs(self):
        self.assertEqual(self.gate_result(), 0)
        for result in ("failure", "cancelled", "skipped"):
            with self.subTest(result=result):
                self.assertNotEqual(self.gate_result(checks_result=result), 0)
                self.assertNotEqual(self.gate_result(codeql=result), 0)

    def test_actual_detection_switches_when_tracked_go_appears(self):
        with tempfile.TemporaryDirectory(prefix="vestrelix-detection-test-") as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-b", "master"], cwd=root, check=True, capture_output=True)
            env = dict(os.environ, GITHUB_OUTPUT=str(root / "output"))
            for expected in ("false", "true"):
                result = subprocess.run([sys.executable, "-c", self.detect], cwd=root, env=env, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((root / "output").read_text().endswith(f"present={expected}\n"))
                (root / "example.go").write_text("package example\n")
                subprocess.run(["git", "add", "example.go"], cwd=root, check=True)

    def test_both_workflows_cover_the_same_native_targets(self):
        expected = [("linux/amd64", "ubuntu-24.04"), ("linux/arm64", "ubuntu-24.04-arm"), ("darwin/arm64", "macos-15")]
        for name in ("go.yml", "security.yml"):
            workflow = (SOURCE / ".github/workflows" / name).read_text()
            actual = re.findall(r"- target: (\S+)\n\s+runner: (\S+)", workflow)
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
