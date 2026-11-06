"""Install the pinned scanner outside the repository, without package dependencies."""

import hashlib
import io
import os
from pathlib import Path
import platform
import tarfile
import tempfile
import urllib.request


VERSION = "8.30.1"
ARCHIVES = {
    ("Darwin", "arm64"): ("darwin_arm64", "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5"),
    ("Darwin", "x86_64"): ("darwin_x64", "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709"),
    ("Linux", "aarch64"): ("linux_arm64", "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080"),
    ("Linux", "x86_64"): ("linux_x64", "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"),
}


def destination():
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache / "vestrelix" / "gitleaks" / VERSION / "gitleaks"


def install():
    archive, checksum = ARCHIVES[(platform.system(), platform.machine())]
    url = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/gitleaks_{VERSION}_{archive}.tar.gz"
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(40 * 1024 * 1024 + 1)
    if hashlib.sha256(data).hexdigest() != checksum:
        raise ValueError("Gitleaks archive checksum mismatch")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as bundle:
        member = bundle.getmember("gitleaks")
        if not member.isfile() or member.size > 100 * 1024 * 1024:
            raise ValueError("Unexpected Gitleaks executable")
        executable = bundle.extractfile(member).read()
    target = destination()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
        temporary = Path(output.name)
        output.write(executable)
    temporary.chmod(0o755)
    temporary.replace(target)
    print(f"Installed pinned Gitleaks {VERSION} outside the repository.")


if __name__ == "__main__":
    install()
