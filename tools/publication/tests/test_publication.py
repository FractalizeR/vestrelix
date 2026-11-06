"""Exercise publication guards in disposable repositories with synthetic data."""

import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[3]
CHECK = SOURCE / "tools/publication/check.py"


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="vestrelix-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "repository"
        self.root.mkdir()
        self.git("init", "-b", "master")
        self.git("config", "user.name", "Example Contributor")
        self.git("config", "user.email", "contributor@example.com")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", "/dev/null")
        (self.root / ".gitleaks.toml").write_text("[extend]\nuseDefault = true\n")
        self.git("config", "--unset", "core.hooksPath")
        self.policy = self.base / "policy.json"
        self.marker = "synthetic-private-marker.example"
        self.policy.write_text(json.dumps({"forbidden_terms": [self.marker]}))
        self.policy.chmod(0o600)
        self.git("config", "vestrelix.publicationMode", "private")
        self.git("config", "vestrelix.privatePolicy", str(self.policy))

    def git(self, *args, check=True):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True)
        if check and result.returncode:
            self.fail("Temporary Git operation failed")
        return result

    def stage(self, name="note.txt", content="Public synthetic example.\n"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self.git("add", "--", name)

    def run_check(self, action="staged", *args, env=None, input_data=None):
        return subprocess.run(
            [sys.executable, str(CHECK), action, "--repo", str(self.root), *args],
            capture_output=True, env=env, input=input_data,
        )

    def assertBlocked(self, result, confidential=None):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"Publication blocked", result.stderr)
        if confidential:
            self.assertNotIn(confidential.encode(), result.stdout + result.stderr)

    def test_clean_staged_and_history(self):
        self.stage()
        self.assertEqual(self.run_check().returncode, 0)
        self.git("commit", "-m", "test(publication): synthetic public content")
        self.assertEqual(self.run_check("history").returncode, 0)

    def test_index_is_checked_instead_of_clean_worktree(self):
        self.stage(content=self.marker)
        (self.root / "note.txt").write_text("Clean working copy")
        self.assertBlocked(self.run_check(), self.marker)

    def test_secret_scanner_and_redaction(self):
        token = "gh" + "p_" + secrets.token_hex(18)
        self.stage(content=f"credential = {token}\n")
        self.assertBlocked(self.run_check(), token)

    def test_force_added_environment_file(self):
        self.stage(".gitignore", ".env\n")
        (self.root / ".env").write_text("SYNTHETIC=example\n")
        self.git("add", "-f", ".env")
        self.assertBlocked(self.run_check())

    def test_symlink_escape_is_not_followed(self):
        external = self.base / "external.txt"
        external.write_text(self.marker)
        (self.root / "external-link").symlink_to(external)
        self.git("add", "external-link")
        self.assertBlocked(self.run_check(), self.marker)

    def test_instruction_alias_is_allowed(self):
        self.stage("AGENTS.md", "# Public instructions\n")
        (self.root / "CLAUDE.md").symlink_to("AGENTS.md")
        self.git("add", "CLAUDE.md")
        self.assertEqual(self.run_check().returncode, 0)

    def test_alias_cannot_point_to_another_symlink(self):
        (self.root / "AGENTS.md").symlink_to(self.base / "outside")
        (self.root / "CLAUDE.md").symlink_to("AGENTS.md")
        self.git("add", "AGENTS.md", "CLAUDE.md")
        self.assertBlocked(self.run_check())

    def test_deleted_historical_content_is_checked(self):
        self.stage(content=self.marker)
        self.git("commit", "-m", "test: first synthetic revision")
        self.stage(content="Clean replacement")
        self.git("commit", "-m", "test: clean replacement")
        self.assertBlocked(self.run_check("history"), self.marker)

    def test_commit_metadata_is_checked(self):
        self.stage()
        self.git("commit", "-m", self.marker)
        self.assertBlocked(self.run_check("history"), self.marker)

    def test_tag_metadata_is_checked(self):
        self.stage()
        self.git("commit", "-m", "test: public content")
        self.git("-c", "tag.gpgsign=false", "tag", "-a", "test-tag", "-m", self.marker)
        self.assertBlocked(self.run_check("history"), self.marker)

    def test_tagger_identity_is_checked(self):
        self.stage()
        self.git("commit", "-m", "test: public content")
        self.git("-c", f"user.name={self.marker}", "-c", "tag.gpgsign=false", "tag", "-a", "test-tag", "-m", "Public tag")
        self.assertBlocked(self.run_check("history"), self.marker)

    def test_nested_tag_metadata_is_checked(self):
        self.stage()
        self.git("commit", "-m", "test: public content")
        self.git("-c", f"user.name={self.marker}", "-c", "tag.gpgsign=false", "tag", "-a", "inner", "-m", "Public inner tag")
        self.git("-c", "tag.gpgsign=false", "tag", "-a", "outer", "inner", "-m", "Public outer tag")
        self.git("tag", "-d", "inner")
        self.assertBlocked(self.run_check("history"), self.marker)

    def test_outgoing_tag_by_object_id_is_checked(self):
        self.stage()
        self.git("commit", "-m", "test: public content")
        self.git("-c", f"user.name={self.marker}", "-c", "tag.gpgsign=false", "tag", "-a", "temporary", "-m", "Public tag")
        tip = self.git("rev-parse", "temporary").stdout.decode().strip()
        self.git("tag", "-d", "temporary")
        refs = f"{tip} {tip} refs/tags/release {'0' * 40}\n"
        self.assertBlocked(self.run_check("push", input_data=refs.encode()), self.marker)

    def test_unstaged_scanner_configuration_cannot_hide_secret(self):
        self.git("add", ".gitleaks.toml")
        token = "gh" + "p_" + secrets.token_hex(18)
        self.stage(content=f"credential = {token}\n")
        with (self.root / ".gitleaks.toml").open("a") as output:
            output.write("\n[[allowlists]]\ndescription = 'synthetic bypass'\nregexes = ['.*']\n")
        self.assertBlocked(self.run_check(), token)

    def test_replace_objects_cannot_hide_historical_content(self):
        self.stage(content=self.marker)
        self.git("commit", "-m", "test: first synthetic revision")
        original = self.git("rev-parse", "HEAD").stdout.decode().strip()
        self.stage(content="Clean replacement")
        self.git("commit", "-m", "test: clean replacement")
        tree = self.git("rev-parse", "HEAD^{tree}").stdout.decode().strip()
        replacement = self.git("commit-tree", tree, "-m", "Public replacement root").stdout.decode().strip()
        self.git("replace", original, replacement)
        self.assertBlocked(self.run_check("history"), self.marker)

    def test_outgoing_remote_ref_is_checked(self):
        self.stage()
        self.git("commit", "-m", "test: public content")
        tip = self.git("rev-parse", "HEAD").stdout.decode().strip()
        refs = f"refs/heads/master {tip} refs/heads/{self.marker} {'0' * 40}\n"
        self.assertBlocked(self.run_check("push", input_data=refs.encode()), self.marker)

    def test_secret_in_filename_is_checked(self):
        token = "gh" + "p_" + secrets.token_hex(18)
        self.stage(name=f"{token}.txt")
        self.assertBlocked(self.run_check(), token)

    def test_missing_policy_fails_closed(self):
        self.stage()
        self.policy.unlink()
        self.assertBlocked(self.run_check())

    def test_missing_scanner_fails_closed(self):
        self.stage()
        env = dict(os.environ, XDG_CACHE_HOME=str(self.base / "empty-cache"))
        self.assertBlocked(self.run_check(env=env))

    def test_unconfigured_policy_fails_closed(self):
        self.stage()
        self.git("config", "--unset", "vestrelix.publicationMode")
        self.assertBlocked(self.run_check())

    def test_public_ci_explicitly_omits_private_policy(self):
        self.stage(content=self.marker)
        self.policy.unlink()
        self.assertEqual(self.run_check("staged", "--public-only").returncode, 0)

    def test_binary_content_is_rejected(self):
        (self.root / "note.txt").write_bytes(b"public\0example")
        self.git("add", "note.txt")
        self.assertBlocked(self.run_check())

    def test_hook_blocks_actual_push_to_local_bare_repository(self):
        remote = self.base / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote)], capture_output=True, check=True)
        self.git("remote", "add", "origin", str(remote))
        shutil.copytree(SOURCE / "tools/publication", self.root / "tools/publication", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(SOURCE / ".githooks", self.root / ".githooks")
        development = self.root / "tools/development"
        development.mkdir(parents=True)
        (development / "check.py").write_text("# Development checks are exercised by their own integration tests.\n")
        installed = self.run_check("install", "--private-policy", str(self.policy))
        self.assertEqual(installed.returncode, 0)
        self.stage()
        self.git("commit", "-m", "test: public content")
        self.assertEqual(self.git("push", "origin", "master", check=False).returncode, 0)
        self.git("config", "core.hooksPath", "/dev/null")
        self.stage(content=self.marker)
        self.git("commit", "-m", "test: synthetic forbidden content")
        self.git("config", "core.hooksPath", ".githooks")
        self.assertBlocked(self.git("push", "origin", "master", check=False), self.marker)


if __name__ == "__main__":
    unittest.main()
