import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path
from urllib.request import urlopen


BUNDLED = version("yt-dlp")
STABLE_VERSION = re.compile(r"\d{4}\.\d{1,2}\.\d{1,2}\Z")
PYPI = "https://pypi.org/pypi/yt-dlp/json"
PROBE = """
import sys
from pathlib import Path
path = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(path))
from yt_dlp import YoutubeDL
from yt_dlp.networking import Request
from yt_dlp.networking.exceptions import HTTPError
from yt_dlp.version import __version__
import yt_dlp
assert Path(yt_dlp.__file__).resolve().is_relative_to(path)
reported_version = tuple(map(int, __version__.split(".")))
selected_version = tuple(map(int, sys.argv[2].split(".")))
assert reported_version == selected_version
with YoutubeDL({'quiet': True}):
    pass
"""


def order(value):
    return tuple(map(int, value.split(".")))


def installed(data):
    root = Path(data) / "dependencies" / "yt-dlp"
    try:
        selected = (root / "installed").read_text(encoding="ascii").strip()
    except FileNotFoundError:
        return None
    if not STABLE_VERSION.fullmatch(selected) or not (root / selected / "yt_dlp").is_dir():
        raise ValueError("Invalid yt-dlp installation in the data volume")
    return selected


def probe(path, selected):
    subprocess.run([sys.executable, "-I", "-c", PROBE, str(path), selected],
                   capture_output=True, text=True, errors="replace", check=True, timeout=30)


def activate(data):
    try:
        selected = installed(data)
        if selected and order(selected) > order(BUNDLED):
            path = Path(data).resolve() / "dependencies" / "yt-dlp" / selected
            probe(path, selected)
            sys.path.insert(0, str(path))
    except (OSError, ValueError, subprocess.SubprocessError):
        logging.exception("Could not load the updated yt-dlp; using the image version")
        return "dependency_load_failed"
    return None


def install_latest(data, active):
    with urlopen(PYPI, timeout=15) as response:
        selected = json.load(response)["info"]["version"]
    if not STABLE_VERSION.fullmatch(selected):
        raise ValueError("PyPI did not return a stable yt-dlp version")
    if order(selected) <= order(active):
        return None

    root = Path(data) / "dependencies" / "yt-dlp"
    root.mkdir(parents=True, exist_ok=True)
    final = root / selected
    if final.exists():
        probe(final, selected)
    else:
        with tempfile.TemporaryDirectory(prefix="install-", dir=root) as temp:
            candidate = Path(temp) / "package"
            env = {key: value for key, value in os.environ.items() if not key.startswith("PIP_")}
            env["PIP_CONFIG_FILE"] = os.devnull
            subprocess.run([sys.executable, "-I", "-m", "pip", "--isolated", "install",
                            "--disable-pip-version-check", "--no-input", "--no-cache-dir",
                            "--only-binary=:all:", "--index-url", "https://pypi.org/simple",
                            "--target", str(candidate), f"yt-dlp[default]=={selected}"],
                           env=env, check=True, capture_output=True, text=True, errors="replace", timeout=180)
            probe(candidate, selected)
            candidate.rename(final)
    pointer = root / "installed.tmp"
    pointer.write_text(selected + "\n", encoding="ascii")
    pointer.replace(root / "installed")
    return selected
