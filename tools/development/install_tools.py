"""Install checksummed development binaries in a versioned external cache."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import tarfile
import tempfile
import urllib.request


MANIFEST = Path(__file__).with_name("tools.json")
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_BINARY_BYTES = 128 * 1024 * 1024


def specifications():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def host():
    system = platform.system().lower()
    arch = {"aarch64": "arm64", "arm64": "arm64", "x86_64": "amd64"}.get(platform.machine())
    if system not in {"darwin", "linux"} or arch is None:
        raise ValueError("Development tools support macOS/Linux on amd64/arm64")
    return f"{system}-{arch}"


def destination(name):
    spec = specifications()[name]
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache / "vestrelix" / "development" / name / spec["version"] / host() / name


def executable(name):
    target = destination(name)
    if not target.is_file():
        raise ValueError(f"Pinned {name} is missing; run make setup")
    return str(target)


def extract_binary(data, checksum, member_name):
    if len(data) > MAX_ARCHIVE_BYTES or hashlib.sha256(data).hexdigest() != checksum:
        raise ValueError("Development tool archive checksum/size mismatch")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = [member for member in archive.getmembers() if member.name == member_name]
        if len(members) != 1 or not members[0].isfile() or not 0 < members[0].size <= MAX_BINARY_BYTES:
            raise ValueError("Unexpected development tool executable")
        return archive.extractfile(members[0]).read(MAX_BINARY_BYTES + 1)


def install(name):
    spec = specifications()[name]
    asset = spec["archives"][host()]
    target = destination(name)
    if target.is_file():
        print(f"Pinned {name} {spec['version']} is already installed.")
        return
    url = f"https://github.com/{spec['repository']}/releases/download/v{spec['version']}/{asset['file']}"
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    binary = extract_binary(data, asset["sha256"], asset["member"])
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(binary)
        temporary.chmod(0o755)
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Installed pinned {name} {spec['version']} outside the repository.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tools", nargs="*", choices=tuple(specifications()))
    args = parser.parse_args()
    for tool in args.tools or specifications():
        install(tool)
