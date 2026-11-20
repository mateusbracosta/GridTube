import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unicodedata
from email.utils import parsedate_to_datetime
from http.cookiejar import Cookie
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen

import dependencies


DEPENDENCY_STARTUP_ERROR = dependencies.activate(os.environ.get("DATA_DIR", "./data"))

from yt_dlp import YoutubeDL
from yt_dlp.networking import Request
from yt_dlp.networking.exceptions import HTTPError, RequestError
from yt_dlp.version import __version__ as YT_DLP_VERSION


VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
YOUTUBE = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def youtube_url(value, kind):
    if not isinstance(value, str):
        raise ValueError("invalid_url")
    try:
        url = urlsplit(value.strip())
        host = url.hostname
        port = url.port
    except ValueError:
        raise ValueError("invalid_url") from None
    if url.scheme not in {"http", "https"} or host not in YOUTUBE or port or url.username:
        raise ValueError("invalid_url")
    parts = url.path.strip("/").split("/")
    if kind == "video":
        if host == "youtu.be" and len(parts) == 1:
            video_id = parts[0]
        elif parts[0] in {"shorts", "live"} and len(parts) == 2:
            video_id = parts[1]
        elif parts == ["watch"]:
            video_id = parse_qs(url.query).get("v", [""])[0]
        else:
            video_id = ""
        if VIDEO_ID.fullmatch(video_id):
            route = "shorts/" if parts[0] == "shorts" else "watch?v="
            return f"https://www.youtube.com/{route}{video_id}", video_id
    elif host != "youtu.be":
        if parts[-1] in {"videos", "shorts", "featured", "streams"}:
            parts.pop()
        if parts and (len(parts) == 1 and re.fullmatch(r"@[^/\s?#]+", parts[0])
                      or len(parts) == 2 and parts[0] in {"channel", "c", "user"}
                      and re.fullmatch(r"[^/\s?#]+", parts[1])):
            return "https://www.youtube.com/" + "/".join(parts), None
    raise ValueError("invalid_url")


def options(**overrides):
    runtimes = {"deno": {}, "node": {}}
    return dict(quiet=True, no_warnings=True, noprogress=True, socket_timeout=20, retries=2,
                extractor_retries=2, js_runtimes=runtimes, **overrides)


CATALOG_LANGUAGE = {"youtube": {"lang": ["pt"]}}
PLAYLIST_ID = re.compile(r"[A-Za-z0-9_-]{10,100}\Z")


def title_key(value):
    return "".join(char for char in unicodedata.normalize("NFKD", (value or "").casefold())
                   if not unicodedata.combining(char))


def catalog_video(entry, tab=None):
    if not entry or not VIDEO_ID.fullmatch(entry.get("id") or ""):
        return None
    if entry.get("live_status") in {"is_live", "is_upcoming"}:
        return None
    video_id = entry["id"]
    if not tab:
        source = entry.get("url") or entry.get("webpage_url") or ""
        tab = ("shorts" if "/shorts/" in source else
               "streams" if entry.get("live_status") in {"was_live", "post_live"} or "/live/" in source else "videos")
    return {
        "id": video_id, "title": entry.get("title") or video_id,
        "duration": entry.get("duration"), "kind": tab,
        "url": f"https://www.youtube.com/{'shorts/' if tab == 'shorts' else 'watch?v='}{video_id}",
    }


def channel_playlists(source):
    with YoutubeDL(options(extract_flat="in_playlist", lazy_playlist=True,
                           extractor_args=CATALOG_LANGUAGE)) as downloader:
        try:
            result = downloader.extract_info(f"{source}/playlists", download=False)
        except Exception as exc:
            if "does not have a" in str(exc).lower() and "tab" in str(exc).lower():
                return
            raise
        for entry in result.get("entries") or []:
            if entry and PLAYLIST_ID.fullmatch(entry.get("id") or ""):
                yield entry["id"], entry.get("title") or entry["id"]


def playlist_videos(playlist_id):
    with YoutubeDL(options(extract_flat="in_playlist", lazy_playlist=True,
                           extractor_args=CATALOG_LANGUAGE)) as downloader:
        result = downloader.extract_info(f"https://www.youtube.com/playlist?list={playlist_id}", download=False)
        for entry in result.get("entries") or []:
            video = catalog_video(entry)
            if video:
                yield video

def channel_entries(source, limit=None, profile=None):
    """Yield metadata and entries as yt-dlp enumerates each YouTube tab."""
    for tab in ("videos", "shorts", "streams"):
        args = options(extract_flat="in_playlist", lazy_playlist=True, extractor_args=CATALOG_LANGUAGE)
        if limit:
            args["playlistend"] = limit
        with YoutubeDL(args) as downloader:
            try:
                info = downloader.extract_info(f"{source}/{tab}", download=False)
            except Exception as exc:
                if "does not have a" in str(exc).lower() and "tab" in str(exc).lower():
                    continue
                raise
            title = info.get("channel") or info.get("uploader") or info.get("title") or source
            if profile:
                profile(channel_profile(info))
                profile = None
            yield title, None
            for entry in info.get("entries") or []:
                video = catalog_video(entry, tab)
                if video:
                    yield title, video


LANGUAGE_TAG = re.compile(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{2,8}){0,4}\Z")
SUBTITLE_ERROR = "track_rate_limited"


def channel_profile(info):
    thumbnails = [pic for pic in info.get("thumbnails") or [] if pic.get("url")]
    avatars = [pic for pic in thumbnails if pic.get("id") == "avatar_uncropped"]
    banners = [pic for pic in thumbnails if pic.get("preference") == -10]
    banner = max(banners, key=lambda pic: pic.get("width") or 0, default={})
    return {
        "name": info.get("channel") or info.get("uploader") or info.get("title"),
        "description": info.get("description") or "",
        "handle": info.get("uploader_id"),
        "channel_id": info.get("channel_id"),
        "avatar": avatars[0]["url"] if avatars else None,
        "banner": banner.get("url"),
    }


def profile_locale(value):
    match = re.fullmatch(r"en(?:-([a-z]{2}))?", str(value or "").strip(), re.I)
    return f"en-{(match[1] or 'US').upper()}" if match else "pt-BR"


def fetch_channel_profile(source, locale="pt-BR"):
    locale = profile_locale(locale)
    region = locale.split("-")[1]
    language = "pt" if locale == "pt-BR" else locale if locale in {"en-GB", "en-IN"} else "en"
    args = options(extract_flat=True, lazy_playlist=True, playlistend=1,
                   extractor_args={"youtube": {"lang": [language]}},
                   http_headers={"Accept-Language": f"{locale},{language};q=0.9"})
    with YoutubeDL(args) as downloader:
        # Session-only regional preferences; no account or browser cookies are used.
        downloader.cookiejar.set_cookie(Cookie(
            version=0, name="PREF", value=urlencode({"hl": language, "gl": region}),
            port=None, port_specified=False, domain=".youtube.com", domain_specified=True,
            domain_initial_dot=True, path="/", path_specified=True, secure=True,
            expires=None, discard=True, comment=None, comment_url=None, rest={}))
        return channel_profile(downloader.extract_info(
            source + "?" + urlencode({"hl": language, "gl": region}), download=False))


def save_channel_image(url, directory, name, timeout=20):
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not host.endswith((".googleusercontent.com", ".ggpht.com", ".ytimg.com")):
        return None
    with YoutubeDL({**options(), "socket_timeout": timeout}) as downloader, downloader.urlopen(url) as response:
        headers = response.headers
        media_type = headers.get("Content-Type", "").split(";")[0]
        suffix = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
                  "image/avif": "avif"}.get(media_type)
        if not suffix:
            return None
        content = response.read(8 * 1024 * 1024 + 1)
    if not content or len(content) > 8 * 1024 * 1024:
        return None
    filename = f"{name}.{suffix}"
    with tempfile.NamedTemporaryFile(dir=directory, delete=False) as staged:
        staged.write(content)
    Path(staged.name).replace(directory / filename)
    return filename


def save_video_thumbnail(video_id, directory):
    if not VIDEO_ID.fullmatch(video_id):
        return None
    try:
        return save_channel_image(f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg", directory, "youtube-thumbnail", timeout=5)
    except (OSError, RequestError):
        return None


def track_inventory(info, automatic=True):
    subtitles = {}
    for automated, inventory in ((False, info.get("subtitles")), (True, info.get("automatic_captions") if automatic else {})):
        for code, tracks in (inventory or {}).items():
            base, original = (code[:-5], True) if code.endswith("-orig") else (code, False)
            if not LANGUAGE_TAG.fullmatch(base):
                continue
            vtt = next((track for track in tracks if track.get("ext") == "vtt" and track.get("url")), None)
            if vtt:
                translated = bool(parse_qs(urlsplit(vtt["url"]).query).get("tlang"))
                item = {**vtt, "automatic": automated, "original": original, "translated": translated}
                if base not in subtitles or track_priority(item) > track_priority(subtitles[base]):
                    subtitles[base] = item
    audios = {}
    for fmt in info.get("formats") or []:
        code = fmt.get("language")
        if (not code or not LANGUAGE_TAG.fullmatch(code) or code.endswith("-desc") or fmt.get("has_drm")
                or not fmt.get("format_id") or fmt.get("acodec") in {None, "none"}):
            continue
        score = (fmt.get("vcodec") == "none", is_original(fmt), audio_rank(fmt))
        if code not in audios or score > audios[code][0]:
            audios[code] = (score, fmt)
    return {"audio": {code: value[1] for code, value in audios.items()}, "subtitle": subtitles}


def read_video(url, subtitles=False, automatic=False, catalog_title=False):
    metadata_options = {"extractor_args": CATALOG_LANGUAGE} if catalog_title else {}
    with YoutubeDL(options(noplaylist=True, format="best/bestaudio/bestvideo", writesubtitles=subtitles,
                           writeautomaticsub=automatic, **metadata_options)) as downloader:
        return extract_video(downloader, url)


def read_video_title(video_id):
    if not VIDEO_ID.fullmatch(video_id):
        return None
    query = urlencode({"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"})
    try:
        with urlopen(f"https://www.youtube.com/oembed?{query}", timeout=5) as response:
            metadata = json.loads(response.read(64 * 1024))
    except (OSError, ValueError):
        return None
    title = metadata.get("title") if isinstance(metadata, dict) else None
    return title.strip() if isinstance(title, str) and title.strip() else None


def extract_video(downloader, url):
    info = downloader.extract_info(url, download=False, process=False)
    if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
        raise ValueError("live_unsupported")
    # Duplicate itags get distinct IDs during yt-dlp post-extraction processing.
    return downloader.process_ie_result(info, download=False)


def read_tracks(url, automatic=True):
    return read_video(url, subtitles=True, automatic=automatic)


def available_tracks(info):
    inventory = track_inventory(info)
    return {
        "audio": [{"code": code, "original": is_original(fmt)} for code, fmt in sorted(inventory["audio"].items())],
        "subtitle": [{"code": code, "automatic": fmt["automatic"], "translated": fmt["translated"]}
                     for code, fmt in sorted(inventory["subtitle"].items())],
    }


def choose_track(inventory, kind, code, exact):
    if exact:
        candidate = code
    else:
        candidates = [tag for tag in inventory if language_score(tag, code)]
        candidate = max(candidates, key=lambda tag: track_priority(inventory[tag], language_score(tag, code)), default=code)
    if candidate not in inventory:
        raise ValueError("track_unavailable")
    return candidate, inventory[candidate]


def track_priority(track, language=0):
    return (not track.get("automatic"), not track.get("translated"), language, track.get("original", False))


class TrackRateLimited(ValueError):
    def __init__(self, retry_header=None):
        super().__init__(SUBTITLE_ERROR)
        try:
            self.seconds = max(1, int(retry_header))
        except (TypeError, ValueError):
            try:
                self.seconds = max(1, int(parsedate_to_datetime(retry_header).timestamp() - time.time()))
            except (TypeError, ValueError, OverflowError):
                self.seconds = 120


def fetch_track(url, kind, code, work, automatic=True, exact=True):
    try:
        with YoutubeDL(options(noplaylist=True, format="best/bestaudio/bestvideo", writesubtitles=True,
                               writeautomaticsub=automatic)) as downloader:
            info = extract_video(downloader, url)
            inventory = track_inventory(info, automatic)[kind]
            candidate, fmt = choose_track(inventory, kind, code, exact)
            if kind == "subtitle":
                target = work / "track.vtt"
                headers = {**(info.get("http_headers") or {}), **(fmt.get("http_headers") or {})}
                try:
                    with downloader.urlopen(Request(fmt["url"], headers=headers)) as response:
                        content = response.read(10 * 1024 * 1024 + 1)
                except HTTPError as exc:
                    if exc.status == 429:
                        raise TrackRateLimited(exc.response.headers.get("Retry-After")) from None
                    raise
                if len(content) > 10 * 1024 * 1024 or not content.lstrip(b"\xef\xbb\xbf").startswith(b"WEBVTT"):
                    raise ValueError("track_invalid")
                target.write_bytes(content)
                return candidate, target

        target = work / "track.m4a"
        source = download_input(info, fmt["format_id"], work, "audio")
        ffmpeg("-i", source, "-map", "0:a:0", "-vn", "-c:a",
               "copy" if fmt["acodec"].startswith("mp4a") else "aac", target)
        return candidate, target
    except Exception as exc:
        if not isinstance(exc, TrackRateLimited) and "HTTP Error 429" in str(exc):
            raise TrackRateLimited() from None
        raise


def source_channel_url(channel_id):
    if isinstance(channel_id, str) and re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel_id):
        return f"https://www.youtube.com/channel/{channel_id}"
    return None


def audio_label(path, reported, prefer_reported=False):
    ffprobe = shutil.which("ffprobe")
    tag = None
    if ffprobe:
        try:
            result = subprocess.run(
                [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries",
                 "stream_tags=language", "-of", "json", str(path)],
                check=True, capture_output=True, timeout=12,
            )
            streams = json.loads(result.stdout).get("streams") or []
            tag = (streams[0].get("tags", {}).get("language") or "").lower() if streams else None
        except (subprocess.SubprocessError, OSError, ValueError):
            pass
    aliases = {"eng": "en", "por": "pt", "rus": "ru", "spa": "es", "ara": "ar",
               "deu": "de", "ger": "de", "fra": "fr", "fre": "fr", "jpn": "ja"}
    tag = aliases.get(tag, tag)
    if not tag or tag in {"und", "mul", "zxx"} or not LANGUAGE_TAG.fullmatch(tag):
        tag = None
    same_language = tag and reported and language_score(tag, reported)
    if tag and (not prefer_reported or same_language):
        display = reported if same_language else tag
        source = "file"
    else:
        display = reported
        source = "youtube" if reported else "unknown"
    return {"audio": display, "audio_reported": reported, "audio_file_language": tag, "audio_label_source": source}

def video_metadata(info):
    return {
        "title": info.get("title") or info["id"],
        "description": info.get("description") or "",
        "upload_date": info.get("upload_date") or info.get("release_date"),
        "source_channel": info.get("channel") or info.get("uploader"),
        "source_channel_id": info.get("channel_id") if source_channel_url(info.get("channel_id")) else None,
        "source_channel_url": source_channel_url(info.get("channel_id")),
    }


def media_output(result, work, stem):
    requested = result.get("requested_downloads") or []
    source = Path(requested[0]["filepath"]) if requested and requested[0].get("filepath") else None
    if source and source.is_file():
        return source
    sources = [path for path in work.glob(f"{stem}.*")
               if path.suffix in {".mp4", ".mkv", ".webm", ".mov", ".m4a", ".aac", ".opus"}
               and path.name.count(".") == 1]
    if len(sources) != 1:
        raise RuntimeError("Media file was not produced")
    return sources[0]


def language_score(actual, desired):
    actual = (actual or "").lower().replace("_", "-")
    desired = desired.lower()
    if actual == desired:
        return 3
    if actual == desired.split("-")[0]:
        return 2
    if actual.split("-")[0] == desired.split("-")[0]:
        return 1
    return 0


def is_original(fmt):
    return ("original" in (fmt.get("format_note") or "").lower()
            or (fmt.get("language_preference") or 0) >= 10)


def audio_rank(fmt):
    return (not fmt.get("format_id", "").endswith("-drc"),
            (fmt.get("acodec") or "").startswith(("mp4a", "aac")), fmt.get("abr") or fmt.get("tbr") or 0)


def choose_audio(formats, desired):
    plain = [fmt for fmt in formats if not (fmt.get("language") or "").endswith("-desc")]
    formats = plain or formats
    if desired != "original":
        matching = [fmt for fmt in formats if language_score(fmt.get("language"), desired)]
        if matching:
            return max(reversed(matching), key=lambda fmt: (language_score(fmt.get("language"), desired), audio_rank(fmt)))
    original = [fmt for fmt in formats if is_original(fmt)]
    return max(reversed(original or formats),
               key=lambda fmt: (fmt.get("language_preference") or 0, audio_rank(fmt)), default=None)


WEBM_VIDEO = ("av01", "av1", "vp9", "vp09", "vp8", "vp08")
WEBM_AUDIO = ("opus", "vorbis")


def resolution(fmt):
    height = fmt["height"]
    width = fmt.get("width") or height
    return min(width, height), max(width, height)


def format_size(fmt, duration):
    if (size := fmt.get("filesize") or fmt.get("filesize_approx")) and size > 0:
        return size
    if duration and (bitrate := fmt.get("tbr")) and bitrate > 0:
        return bitrate * 125 * duration
    return None


def download_size(picture, audio, duration):
    sizes = [format_size(picture, duration)]
    if picture is not audio:
        sizes.append(format_size(audio, duration))
    return sum(sizes) if all(size is not None for size in sizes) else float("inf")


def format_choice(formats, quality, language, mode, duration=None):
    usable = [fmt for fmt in formats if fmt.get("format_id") and not fmt.get("has_drm")]
    audio_only = [fmt for fmt in usable if fmt.get("vcodec") == "none" and fmt.get("acodec") not in {None, "none"}]
    video = [fmt for fmt in usable if fmt.get("vcodec") not in {None, "none"} and fmt.get("height")]
    if quality != "best":
        video = [fmt for fmt in video if resolution(fmt)[0] <= int(quality)]
    muxed = [fmt for fmt in video if fmt.get("acodec") not in {None, "none"}]
    separate = [fmt for fmt in video if fmt.get("acodec") == "none"]
    audio_candidates = muxed + audio_only if separate else muxed
    audio = choose_audio(audio_candidates, language)
    if not audio:
        raise ValueError("no_audio_at_quality")
    chosen_tag = (audio.get("language") or "").lower()
    original = is_original(audio)

    def same_track(fmt):
        return (fmt.get("language") or "").lower() == chosen_tag and (not original or is_original(fmt))

    matching_audio = [fmt for fmt in reversed(audio_only) if same_track(fmt)]
    mp4_sound = max(matching_audio, key=audio_rank, default=None)

    def webm_audio_rank(fmt):
        ordinary, _, bitrate = audio_rank(fmt)
        return ordinary, fmt["acodec"].startswith(WEBM_AUDIO), bitrate

    webm_sound = max(matching_audio, key=webm_audio_rank, default=None)
    candidates = []
    # yt-dlp provides the formats in order from least to most preferred.
    for picture in reversed(video):
        if picture["acodec"] == "none":
            sound = webm_sound if picture["vcodec"].startswith(WEBM_VIDEO) else mp4_sound
        else:
            sound = picture if same_track(picture) else None
        if sound:
            candidates.append((picture, sound))

    def picture_rank(picture):
        return resolution(picture), picture.get("fps") or 0

    best = max(candidates, key=lambda pair: picture_rank(pair[0]))
    if mode == "original":
        return best

    def tier(picture):
        return picture_rank(picture), picture.get("dynamic_range") or "SDR"

    comparable = [pair for pair in candidates if tier(pair[0]) == tier(best[0])]
    return min(comparable, key=lambda pair: (download_size(*pair, duration),
                                             not pair[0]["vcodec"].startswith(WEBM_VIDEO)))


class DownloadCancelled(Exception):
    pass


def ffmpeg(*args, progress=None, cancel=None):
    executable = shutil.which("ffmpeg")
    if not executable:
        raise RuntimeError("FFmpeg is required")
    command = [executable, "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
    arguments = list(map(str, args))
    if progress is None and cancel is None:
        subprocess.run(command + arguments, check=True, capture_output=True, timeout=10800)
        return

    failures = []
    command += (["-progress", "pipe:1", "-stats_period", "0.5"] if progress else []) + arguments
    with tempfile.TemporaryFile() as errors, subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors) as process:
        def read_progress():
            for line in process.stdout:
                key, _, value = line.strip().partition(b"=")
                if key == b"out_time_us" and value.lstrip(b"-").isdigit() and not failures:
                    try:
                        progress(int(value))
                    except Exception as exc:
                        failures.append(exc)

        observer = threading.Thread(target=read_progress, name="ffmpeg-progress") if progress else None
        if observer:
            observer.start()
        deadline = time.monotonic() + 10800
        try:
            while True:
                if cancel:
                    cancel()
                if failures:
                    raise failures[0]
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(command, 10800)
                try:
                    process.wait(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    continue
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if observer:
                observer.join()
        if failures:
            raise failures[0]
        if process.returncode:
            errors.seek(0)
            raise subprocess.CalledProcessError(process.returncode, command, stderr=errors.read())


def media_duration(path):
    try:
        value = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                                "-of", "default=nw=1:nk=1", str(path)], timeout=12))
        return value if 0 < value < float("inf") else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def download_input(info, format_id, work, kind, update=None):
    stem = f"{kind}-{hashlib.sha256(format_id.encode()).hexdigest()[:12]}"
    hooks = [update] if update else []
    with YoutubeDL(options(noplaylist=True, format=format_id, fixup="never",
                           outtmpl=str(work / f"{stem}.%(ext)s"), progress_hooks=hooks)) as downloader:
        result = downloader.process_ie_result(copy.deepcopy(info), download=True)
    return media_output(result, work, stem)


def mux_video(source, target, language, audio_source=None, audio_codec="copy", progress=None, cancel=None):
    common = ["-fflags", "+genpts", "-i", source]
    if audio_source:
        common += ["-fflags", "+genpts", "-i", audio_source]
    common += ["-map", "0:v:0", "-map", "1:a:0" if audio_source else "0:a:0"]
    if target.suffix == ".mp4":
        common += ["-movflags", "+faststart"]
    language = (language or "").split("-")[0].lower()
    if language in {"pt", "en"}:
        iso_code = {"pt": "por", "en": "eng"}[language]
        common += ["-metadata:s:a:0", f"language={iso_code}"]
    try:
        ffmpeg(*common, "-c:v", "copy", "-c:a", audio_codec, target, progress=progress, cancel=cancel)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"FFmpeg: {exc.stderr.decode(errors='replace')[-650:]}") from exc


def transfer_progress(event):
    if event.get("status") != "downloading":
        return None
    total = event.get("total_bytes") or event.get("total_bytes_estimate")
    if total and total > 0 and event.get("downloaded_bytes") is not None:
        percent = max(0, min(99, int(100 * event["downloaded_bytes"] / total)))
        return percent, bool(event.get("fragment_count") or not event.get("total_bytes"))
    if event.get("fragment_count") and event.get("fragment_index") is not None:
        return max(0, min(99, int(100 * event["fragment_index"] / event["fragment_count"]))), True
    return None


def download(url, prefs, work, bundle, progress, *, on_title, cancel=None):
    def check_cancelled():
        if cancel:
            cancel()

    check_cancelled()
    title_filter = prefs.get("title_filter", "")
    info = read_video(url, catalog_title=bool(title_filter))
    check_cancelled()
    title = info.get("title") or info["id"]
    if title != info["id"]:
        on_title(title)
    if title_filter and title_key(title_filter) not in title_key(info.get("title")):
        raise ValueError("title_filter_mismatch")
    formats = info.get("formats") or []
    mode = prefs.get("download_mode", "compact")
    picture, audio = format_choice(formats, prefs["quality"], prefs["audio"], mode, info.get("duration"))
    separate = picture is not audio
    video_codec, audio_codec = picture["vcodec"], audio["acodec"]

    def transfer(fmt, stem, phase):
        def update(event):
            check_cancelled()
            if values := transfer_progress(event):
                progress(phase, *values)

        progress(phase)
        check_cancelled()
        path = download_input(info, fmt["format_id"], work, stem, update)
        check_cancelled()
        progress(phase, 100)
        return path

    source = transfer(picture, "picture", "video")
    audio_source = transfer(audio, "sound", "audio") if separate else None
    progress("mux")
    duration = media_duration(source)
    sound_duration = media_duration(audio_source) if audio_source else duration
    estimated = not duration or not sound_duration
    expected = max(duration or 0, sound_duration or 0, (info.get("duration") or 0) if estimated else 0)

    def remuxed(microseconds):
        progress("mux", max(0, min(99, int(100 * microseconds / (expected * 1_000_000)))), estimated)

    stem = safe_name(title)
    extension = "webm" if video_codec.startswith(WEBM_VIDEO) and audio_codec.startswith(WEBM_AUDIO) else "mp4"
    target = bundle / f"{stem}.{extension}"
    reported = audio.get("language")
    label = audio_label(audio_source or source, reported, prefs["audio"] != "original" and
                        bool(language_score(reported, prefs["audio"])))
    mux_video(source, target, label["audio"], audio_source, progress=remuxed if expected else None, cancel=cancel)
    progress("mux", 100)
    progress("thumbnail")
    thumbnail = save_video_thumbnail(info["id"], bundle)
    check_cancelled()
    thumbnail_source = "youtube" if thumbnail else "frame"
    if not thumbnail:
        fallback = bundle / f"{stem}-thumb.jpg"
        try:
            ffmpeg("-filter_threads", "1", "-threads", "1", "-ss", min(5, (info.get("duration") or 0) / 3),
                   "-i", target, "-frames:v", "1", "-vf", "scale=720:-2", "-threads", "1", fallback, cancel=cancel)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        thumbnail = fallback.name if fallback.is_file() else None
    return {
        **video_metadata(info), "id": info["id"], "filename": target.name,
        "thumbnail": thumbnail, "thumbnail_source": thumbnail_source,
        "duration": info.get("duration"), "source": url, "chapters": info.get("chapters") or [],
        "download_mode": mode, "video_codec": video_codec, "audio_codec": audio_codec,
        "width": picture.get("width"), "height": picture["height"], "fps": picture.get("fps"),
        **label, "audio_tracks": {}, "subtitles": {},
        "audio_fallback": prefs["audio"] != "original" and not language_score(label["audio"], prefs["audio"]),
        "subtitles_missing": False,
    }


def safe_name(title):
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", title)
    clean = " ".join(clean.split())[:70].strip(" .")
    if not clean or re.fullmatch(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", clean):
        return "Video"
    return clean


def write_manifest(bundle, metadata):
    staged = bundle / "video.json.tmp"
    staged.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    staged.replace(bundle / "video.json")
