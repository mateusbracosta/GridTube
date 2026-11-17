# GridTube

English · [Português do Brasil](README.pt-BR.md)

GridTube is a self-hosted video library for preserving YouTube videos and watching them offline. Download videos while connected, then browse and play your archive over your local network.

- Browse a channel's videos, Shorts, live archives, and playlists before choosing what to download. Set a title rule and optionally follow new uploads.
- Choose **Compact** or **Original quality** globally, by channel, or for a single link. Compact finds a smaller variant within your resolution limit. Original requests the best available resolution and frame rate. The main audio and video streams are copied from YouTube.
- Save preferred audio and subtitle languages. Find and download additional tracks from the player when the source offers them.
- Organize videos into channels and playlists. The interface supports English and Brazilian Portuguese.

## Run with Docker

Run these commands from the repository directory with Docker and Compose installed.

~~~sh
docker compose up -d --build --wait
~~~

Open [GridTube](http://localhost:3987). The default bind address is 127.0.0.1. To use it on a trusted local network, set `GRIDTUBE_BIND` to your host's LAN IP address. `GRIDTUBE_PORT` changes the host port. GridTube currently has no user authentication.

### ARM64 and small servers

The same Compose command builds GridTube on a 64-bit Docker host, including boards such as the Orange Pi Zero 3 running a 64-bit Linux distribution. `uname -m` should report `aarch64` on the board. Serve the library from the board and play it in a browser on your local network. The browser decodes the video and its codec support determines playback compatibility.

Set `GRIDTUBE_PLAYBACK_CACHE_MIB=512` in `.env` if disk space is tight. The default is 4096 MiB. The cache holds temporary versions for alternate audio and keeps the version being prepared even if it exceeds the target. The original files stay in the library. Keeping the archive on a USB drive leaves space on the system card.

## Use the archive

1. Choose **Add channel** to browse a channel or **Download link** to save an individual video.
2. In the download options, choose the quality mode, preferred audio language, and subtitles. A channel can override global defaults, and a link can override either.
3. Open a saved video from the library. Use the player gear to switch between saved tracks or discover additional tracks while online.

**Downloads** shows the current phase and its percentage. The app uses transferred bytes for video and audio downloads, and the processed media duration reported by FFmpeg when assembling a file. It labels estimates and uses an indeterminate bar when progress cannot be measured.

From **Organize video → Remove video**, choose **Remove from library** to keep the files and restore the entry later from **Removed**, or **Also delete from disk** to erase the saved bundle. Disk deletion requires a writable archive mount.

GridTube puts videos in `archive/library`, one directory per video, with the MP4 or WebM, a local JSON manifest, and any available sidecars. The `data/` directory holds the database and profile images. Copy `archive/library` to export just the media. To browse the files in Jellyfin, mount that directory read-only and use a Home Videos and Photos library. Direct playback depends on the Jellyfin client and codecs.

## Update or move the library

Under **Settings → System**, choose **Update yt-dlp** to check the stable PyPI release. GridTube keeps the active version until the new version has passed an import check and the app restarts. Choose **Restart and apply** in Docker when a version is ready. A restart interrupts playback and resumes queued work. The activity log shows recent update results and errors. The installed update is stored in the `data/` volume and survives container recreation.

After updating the source, run the same Docker Compose command. The `data/` and `archive/` directories are bind-mounted and survive container recreation. Stop the service before copying both directories for a full migration. For an offline installation, also bring your Compose file and an image exported with Docker for the target machine's architecture.

See the [architecture and operations notes (PT-BR)](ARQUITETURA.md) for storage, API routes, and recovery. GridTube is an independent project inspired by [UnTube](https://github.com/tomfriart/untube).
