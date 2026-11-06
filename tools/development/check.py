"""Shared local and CI checks; commands never reformat or stage source files."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from install_tools import executable, install, specifications


ROOT = Path(__file__).resolve().parents[2]
GOVULNCHECK = "golang.org/x/vuln/cmd/govulncheck@v1.9.0"


def run(args, root=ROOT, **kwargs):
    started = time.monotonic()
    print(f"Running: {' '.join(map(str, args))}", flush=True)
    try:
        return subprocess.run(args, cwd=root, check=True, timeout=600, **kwargs)
    finally:
        print(f"Finished in {time.monotonic() - started:.1f}s", flush=True)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, timeout=30)


def go_files(root):
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0")
    return sorted({os.fsdecode(name) for name in names if name.endswith(b".go") and (root / os.fsdecode(name)).is_file()})


def require_go(root):
    version = re.search(r"^go (\d+)\.(\d+)(?:\.(\d+))?$", (root / "go.mod").read_text(), re.MULTILINE)
    actual = run(["go", "env", "GOVERSION"], root, capture_output=True).stdout.decode().strip()
    current = re.fullmatch(r"go(\d+)\.(\d+)(?:\.(\d+))?", actual)
    minimum = tuple(int(part or 0) for part in version.groups()) if version else None
    selected = tuple(int(part or 0) for part in current.groups()) if current else None
    if minimum is None or selected is None or selected[:2] != minimum[:2] or selected < minimum:
        raise ValueError("Install the Go release line declared in go.mod (latest security patch recommended)")


def staged_format(root=ROOT):
    names = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split(b"\0")
    names = [os.fsdecode(name) for name in names if name.endswith(b".go")]
    if not names:
        print("No staged Go files; formatting is not applicable.")
        return
    require_go(root)
    for name in names:
        original = git(root, "show", f":{name}")
        formatted = run(["gofmt"], root, input=original, stdout=subprocess.PIPE).stdout
        if formatted != original:
            raise ValueError(f"Staged Go formatting differs: {name!r}; format and stage it explicitly")


def go_checks(mode, root=ROOT):
    files = go_files(root)
    if not files:
        print(f"No Go source yet; {mode} checks are not applicable.")
        return
    require_go(root)
    if mode == "go":
        for offset in range(0, len(files), 100):
            result = run(["gofmt", "-l", *files[offset:offset + 100]], root, stdout=subprocess.PIPE)
            if result.stdout:
                raise ValueError("Go formatting differs; run gofmt and stage changes explicitly")
        run(["go", "mod", "tidy", "-diff"], root)
        run([executable("golangci-lint"), "run"], root)
        run(["go", "vet", "./..."], root)
        run(["go", "test", "-timeout=2m", "./..."], root)
        run(["go", "build", "-o", os.devnull, "./..."], root)
    elif mode == "race":
        run(["go", "test", "-race", "-timeout=5m", "./..."], root)
    elif mode == "vuln":
        run(["go", "mod", "verify"], root)
        run(["go", "run", GOVULNCHECK, "./..."], root)
    else:
        raise ValueError("Unknown Go check mode")


def workflows(root=ROOT):
    # Disable optional PATH-discovered analyzers to keep local and CI scope identical.
    run([executable("actionlint"), "-shellcheck=", "-pyflakes="], root)
    run([executable("zizmor"), "--offline", "--no-progress", "."], root)


def tooling(root=ROOT):
    for directory in ("tools/development/tests", "tools/publication/tests"):
        run([sys.executable, "-m", "unittest", "discover", "-s", directory, "-v"], root)


def toolchain(root=ROOT):
    run([sys.executable, "-m", "unittest", "discover", "-s", "tools/development/tests", "-p", "toolchain.py", "-v"], root)


def setup(args):
    publication = ROOT / "tools/publication/check.py"
    options = []
    if args.private_policy:
        options = ["--private-policy", args.private_policy]
    elif args.public_only:
        options = ["--public-only"]
    else:
        result = subprocess.run(["git", "config", "--local", "--get", "vestrelix.publicationMode"], cwd=ROOT, capture_output=True, check=False, timeout=30)
        if result.returncode not in (0, 1):
            result.check_returncode()
        mode = result.stdout.decode().strip()
        if mode == "private":
            policy = git(ROOT, "config", "--local", "--get", "vestrelix.privatePolicy").decode().strip()
            options = ["--private-policy", policy]
        elif mode == "public":
            options = ["--public-only"]
        else:
            raise ValueError("Choose setup --private-policy PATH or --public-only explicitly")
    run([sys.executable, str(publication), "install", *options], ROOT)
    scanner = ROOT / "tools/publication/install_gitleaks.py"
    run([sys.executable, str(scanner)], ROOT)
    for name in specifications():
        install(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("setup", "check", "ci", "go", "race", "vuln", "workflows", "tooling", "toolchain", "staged-format"))
    policy = parser.add_mutually_exclusive_group()
    policy.add_argument("--private-policy")
    policy.add_argument("--public-only", action="store_true")
    args = parser.parse_args()
    if args.private_policy and args.action != "setup":
        parser.error("--private-policy is only supported by setup")
    if args.public_only and args.action not in {"setup", "ci"}:
        parser.error("--public-only is only supported by setup and ci")
    try:
        if args.action == "setup":
            setup(args)
        elif args.action == "staged-format":
            staged_format()
        elif args.action in {"go", "race", "vuln"}:
            go_checks(args.action)
        elif args.action == "workflows":
            workflows()
        elif args.action == "tooling":
            tooling()
        elif args.action == "toolchain":
            toolchain()
        else:
            tooling()
            workflows()
            go_checks("go")
            if args.action == "ci":
                toolchain()
                go_checks("race")
                go_checks("vuln")
                options = ["--public-only"] if args.public_only else []
                run([sys.executable, "tools/publication/check.py", "history", *options])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Development check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
