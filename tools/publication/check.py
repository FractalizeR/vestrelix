"""Fail closed before publishing staged objects or outgoing Git history."""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

from git_objects import blob, config, git, history, repository, staged_entries
from install_gitleaks import VERSION, destination


MAX_OBJECT_BYTES = 1024 * 1024
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".db", ".sql", ".dump", ".log", ".zip", ".gz", ".tgz", ".bundle"}
BLOCKED_DIRECTORIES = {".git", ".venv", "secrets", "private", "state", "tmp"}


def private_terms(root, public_only=False):
    if public_only:
        return []
    mode = config(root, "vestrelix.publicationMode")
    if mode == "public":
        print("Public-only checks: no private confidentiality policy is applied.")
        return []
    if mode != "private":
        raise ValueError("Install publication hooks and explicitly select a policy first")
    name = config(root, "vestrelix.privatePolicy")
    if not name:
        raise ValueError("The required private publication policy is unavailable")
    path = Path(name)
    if not path.is_absolute() or path.resolve().is_relative_to(root.resolve()):
        raise ValueError("The private publication policy must be outside the repository")
    if path.stat().st_mode & 0o077:
        raise ValueError("Private publication policy permissions must be owner-only")
    document = json.loads(path.read_text(encoding="utf-8"))
    terms = document.get("forbidden_terms")
    if not isinstance(terms, list) or not terms:
        raise ValueError("The required private policy has no forbidden terms")
    if any(not isinstance(term, str) or len(term.strip()) < 3 for term in terms):
        raise ValueError("The private publication policy is invalid")
    return [term.casefold() for term in terms]


def inspect_text(data, terms):
    if len(data) > MAX_OBJECT_BYTES or b"\0" in data:
        raise ValueError("Binary or oversized publication candidate is not permitted")
    text = data.decode("utf-8").casefold()
    if any(term in text for term in terms):
        raise ValueError("Private publication policy matched; inspect candidates locally without publishing excerpts")


def inspect_path(name, mode, data):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError("Unsafe tracked path")
    lower = path.name.casefold()
    if any(part.casefold() in BLOCKED_DIRECTORIES for part in path.parts):
        raise ValueError("Private/runtime directory must not be published")
    if (lower == ".env" or lower.startswith(".env.")) and lower != ".env.example":
        raise ValueError("Environment files must not be published")
    if path.suffix.casefold() in BLOCKED_SUFFIXES or ".sqlite" in lower or ".db-" in lower or ".local." in lower:
        raise ValueError("Sensitive/runtime file type must not be published")
    if lower in {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".publication-policy.json", ".netrc", ".pypirc", "credentials.json"}:
        raise ValueError("Potential private key file must not be published")
    if mode == "120000":
        if name != "CLAUDE.md" or data != b"AGENTS.md":
            raise ValueError("Only CLAUDE.md -> AGENTS.md is permitted as a tracked symlink")
    elif mode not in {"100644", "100755"}:
        raise ValueError("Unsupported Git entry mode")


def scanner(root, directory):
    executable = destination()
    version = subprocess.run([str(executable), "version"], capture_output=True, timeout=10)
    if version.returncode or version.stdout.decode().strip() != VERSION:
        raise ValueError("Install the pinned Gitleaks version before publishing")
    ignore = directory / "scanner-ignore"
    ignore.write_text("")
    baseline = directory / "gitleaks-defaults.toml"
    baseline.write_text("[extend]\nuseDefault = true\n")
    result = subprocess.run([
        str(executable), "dir", "--no-banner", "--no-color", "--redact=100",
        "--ignore-gitleaks-allow", "--gitleaks-ignore-path", str(ignore),
        "--config", str(baseline), "--max-decode-depth", "3",
        "--timeout", "90", str(directory),
    ], capture_output=True, timeout=100)
    if result.returncode:
        raise ValueError("Secret scan failed or detected sensitive content; raw scanner output is withheld")


def scan(root, action, terms, tips=None, outgoing_refs=b""):
    seen = set()
    with tempfile.TemporaryDirectory(prefix="vestrelix-publication-") as temporary:
        directory = Path(temporary)
        inspect_text(outgoing_refs, terms)
        (directory / "outgoing-refs.txt").write_bytes(outgoing_refs)
        batches = [(staged_entries(root), None)] if action == "staged" else history(root, tips)
        for index, (items, metadata) in enumerate(batches):
            if metadata is not None:
                inspect_text(metadata, terms)
                (directory / f"metadata-{index}.txt").write_bytes(metadata)
                continue
            items = list(items)
            modes = {name: mode for name, mode, _ in items}
            if modes.get("CLAUDE.md") == "120000" and modes.get("AGENTS.md") not in {"100644", "100755"}:
                raise ValueError("The instruction alias requires a tracked regular AGENTS.md")
            (directory / f"paths-{index}.txt").write_text("\n".join(modes), encoding="utf-8")
            for name, mode, oid in items:
                inspect_text(name.encode("utf-8"), terms)
                data = blob(root, oid, MAX_OBJECT_BYTES)
                inspect_path(name, mode, data)
                if oid not in seen:
                    inspect_text(data, terms)
                    (directory / f"object-{oid}.txt").write_bytes(data)
                    seen.add(oid)
        scanner(root, directory)
    print("Publication checks passed; independently review provenance and confidentiality.")


def install(root, args):
    current = git(root, "config", "--get", "core.hooksPath", check=False).stdout.decode().strip()
    if current and current not in {".githooks", str(root / ".githooks")}:
        raise ValueError("Existing Git hooks require an explicit integration decision")
    if args.private_policy:
        policy = Path(args.private_policy).resolve()
        git(root, "config", "--local", "vestrelix.publicationMode", "private")
        git(root, "config", "--local", "vestrelix.privatePolicy", str(policy))
        private_terms(root)
    elif args.public_only:
        git(root, "config", "--local", "vestrelix.publicationMode", "public")
        git(root, "config", "--local", "--unset-all", "vestrelix.privatePolicy", check=False)
    else:
        raise ValueError("Choose --private-policy or explicitly choose --public-only")
    for name in ("pre-commit", "pre-push"):
        hook = root / ".githooks" / name
        if not hook.is_file():
            raise ValueError("Publication hooks are missing")
        hook.chmod(0o755)
    git(root, "config", "--local", "core.hooksPath", ".githooks")
    print("Repository-local publication hooks installed.")


def outgoing_tips():
    tips = []
    refs = []
    for line in sys.stdin:
        fields = line.split()
        if len(fields) != 4 or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", fields[1]):
            raise ValueError("Invalid pre-push input")
        if set(fields[1]) != {"0"}:
            tips.append(fields[1])
        refs.append(line)
    return tips, "".join(refs).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "staged", "history", "push"))
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--public-only", action="store_true")
    parser.add_argument("--private-policy")
    args = parser.parse_args()
    if args.public_only and args.private_policy:
        parser.error("Select exactly one policy mode")
    try:
        root = repository(args.repo)
        if args.action == "install":
            install(root, args)
        else:
            terms = private_terms(root, args.public_only)
            tips, refs = outgoing_tips() if args.action == "push" else (None, b"")
            scan(root, args.action, terms, tips, refs)
    except (ValueError, OSError, UnicodeError, subprocess.SubprocessError, json.JSONDecodeError):
        # Paths, Git errors, and scanner output can themselves contain private information.
        print("Publication blocked: policy, candidate, or scanner validation failed. Inspect locally; do not publish raw output.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
