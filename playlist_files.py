import os
import tempfile
from zipfile import ZIP_STORED, ZipFile


def m3u(paths):
    return "\n".join(["#EXTM3U", *paths, ""])


def write_m3u(folder, paths):
    folder.mkdir(exist_ok=True)
    content = m3u(paths).encode("utf-8")
    destination = folder / "playlist.m3u8"
    try:
        if destination.read_bytes() == content:
            return
    except FileNotFoundError:
        pass
    with tempfile.NamedTemporaryFile(dir=folder, prefix="playlist-", suffix=".tmp", delete=False) as staged:
        try:
            staged.write(content)
            staged.close()
            os.replace(staged.name, destination)
        finally:
            staged.close()
            if os.path.exists(staged.name):
                os.unlink(staged.name)


class ZipOutput:
    def __init__(self):
        self.blocks = []

    def write(self, data):
        self.blocks.append(data)
        return len(data)

    def flush(self):
        pass

    def drain(self):
        blocks, self.blocks = self.blocks, []
        yield from (block for block in blocks if block)


def export_zip(paths, files):
    output = ZipOutput()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        archive.writestr("playlist.m3u8", m3u(paths).encode("utf-8"))
        yield from output.drain()
        for source, name in files:
            with source.open("rb") as media, archive.open(name, "w", force_zip64=True) as entry:
                for chunk in iter(lambda: media.read(256 * 1024), b""):
                    entry.write(chunk)
                    yield from output.drain()
            yield from output.drain()
    yield from output.drain()
