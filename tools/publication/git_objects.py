"""Read publication candidates from Git objects, never from working-tree files."""

from pathlib import Path
import subprocess


def git(root, *args, check=True):
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(root), *args], capture_output=True, timeout=120,
    )
    if check and result.returncode:
        raise ValueError("Git object inspection failed")
    return result


def config(root, name):
    result = git(root, "config", "--local", "--get", name, check=False)
    if result.returncode not in (0, 1):
        raise ValueError("Cannot read repository-local publication settings")
    return result.stdout.decode().strip()


def entries(raw, staged):
    for item in raw.split(b"\0"):
        if not item:
            continue
        header, name = item.split(b"\t", 1)
        parts = header.decode("ascii").split()
        if staged:
            mode, oid, stage = parts
            if stage != "0":
                raise ValueError("Resolve index conflicts before publication")
        else:
            mode, kind, oid = parts
            if kind != "blob":
                raise ValueError("Submodules and non-blob entries are not permitted")
        yield name.decode("utf-8"), mode, oid


def staged_entries(root):
    return entries(git(root, "ls-files", "--stage", "-z").stdout, True)


def history(root, tips=None):
    refs = git(root, "for-each-ref", "--format=%(refname)").stdout
    tags = git(root, "for-each-ref", "--format=%(objecttype) %(objectname)").stdout
    pending = [line.split()[1].decode("ascii") for line in tags.splitlines() if line.split()[0] == b"tag"]
    pending.extend(tips or [])
    inspected = set()
    tag_metadata = b""
    while pending:
        oid = pending.pop()
        if oid in inspected:
            continue
        inspected.add(oid)
        kind = git(root, "cat-file", "-t", oid).stdout.strip()
        if kind == b"tag":
            raw = git(root, "cat-file", "tag", oid).stdout
            tag_metadata += raw + b"\n"
            pending.append(raw.splitlines()[0].split()[1].decode("ascii"))
        elif kind != b"commit":
            raise ValueError("Only commit histories and tags pointing to commits may be published")
    if tips is None:
        commits = git(root, "rev-list", "--all").stdout.splitlines()
    else:
        for tip in tips:
            git(root, "rev-parse", "--verify", f"{tip}^{{commit}}")
        commits = git(root, "rev-list", *tips, "--").stdout.splitlines() if tips else []
    yield None, refs + tag_metadata
    seen_trees = set()
    for commit in commits:
        oid = commit.decode("ascii")
        metadata = git(root, "show", "-s", "--format=%an%n%ae%n%cn%n%ce%n%B", oid).stdout
        yield None, metadata
        tree = git(root, "rev-parse", f"{oid}^{{tree}}").stdout.strip()
        if tree not in seen_trees:
            seen_trees.add(tree)
            yield entries(git(root, "ls-tree", "-r", "-z", oid).stdout, False), None


def blob(root, oid, limit):
    size = int(git(root, "cat-file", "-s", oid).stdout)
    if size > limit:
        raise ValueError("Oversized Git object requires a publication-policy review")
    return git(root, "cat-file", "blob", oid).stdout


def repository(path):
    root = Path(git(path, "rev-parse", "--show-toplevel").stdout.decode().strip())
    if root.resolve() != Path(path).resolve():
        raise ValueError("Run publication checks from the repository root")
    return root
