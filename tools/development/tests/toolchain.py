"""Exercise the actual Go toolchain and pinned linter in disposable modules."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_checks import checks, SOURCE


class ToolchainTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="vestrelix-toolchain-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-b", "master"], cwd=self.root, check=True, capture_output=True)
        shutil.copyfile(SOURCE / ".golangci.yml", self.root / ".golangci.yml")
        module = (SOURCE / "go.mod").read_text().split("\n", 1)[1]
        (self.root / "go.mod").write_text("module example.com/tooling-test\n" + module)
        (self.root / "sample.go").write_text("package sample\n\nfunc Value() int { return 1 }\n")
        (self.root / "sample_test.go").write_text('package sample\n\nimport "testing"\n\nfunc TestValue(t *testing.T) {\n\tif Value() != 1 {\n\t\tt.Fatal("unexpected value")\n\t}\n}\n')

    def test_valid_library_and_commands_pass_real_checks(self):
        checks.go_checks("go", self.root)
        for name in ("first", "second"):
            command = self.root / "cmd" / name
            command.mkdir(parents=True)
            (command / "main.go").write_text("package main\n\nfunc main() {}\n")
        checks.go_checks("go", self.root)
        checks.go_checks("race", self.root)
        checks.go_checks("vuln", self.root)
        self.assertFalse((self.root / "go.sum").exists())
        self.assertFalse((self.root / "first").exists())
        self.assertFalse((self.root / "second").exists())

    def test_unchecked_error_is_rejected_by_real_linter(self):
        (self.root / "sample.go").write_text('package sample\n\nimport "os"\n\nfunc Value() int {\n\tos.Chdir(".")\n\treturn 1\n}\n')
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            checks.go_checks("go", self.root)
        self.assertEqual(Path(caught.exception.cmd[0]).name, "golangci-lint")

    def test_failing_test_is_not_green(self):
        (self.root / "sample_test.go").write_text('package sample\n\nimport "testing"\n\nfunc TestValue(t *testing.T) {\n\tt.Fatal("synthetic failure")\n}\n')
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            checks.go_checks("go", self.root)
        self.assertEqual(caught.exception.cmd[:2], ["go", "test"])

    def test_real_gofmt_checks_staged_not_worktree_bytes(self):
        subprocess.run(["git", "add", "sample.go"], cwd=self.root, check=True)
        original = (self.root / "sample.go").read_bytes()
        (self.root / "sample.go").write_text("not valid Go")
        checks.staged_format(self.root)
        (self.root / "sample.go").write_text("package sample;func Value() int{return 1}\n")
        subprocess.run(["git", "add", "sample.go"], cwd=self.root, check=True)
        (self.root / "sample.go").write_bytes(original)
        with self.assertRaises(ValueError):
            checks.staged_format(self.root)


if __name__ == "__main__":
    unittest.main()
