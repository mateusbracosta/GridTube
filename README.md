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

## Use the archive

1. Choose **Add channel** to browse a channel or **Download link** to save an individual video.
2. In the download options, choose the quality mode, preferred audio language, and subtitles. A channel can override global defaults, and a link can override either.
3. Open a saved video from the library. Use the player gear to switch between saved tracks or discover additional tracks while online.

From **Organize video → Remove video**, choose **Remove from library** to keep the files and restore the entry later from **Removed**, or **Also delete from disk** to erase the saved bundle. Disk deletion requires a writable archive mount.

GridTube puts videos in `archive/library`, one directory per video, with the MP4 or WebM, a local JSON manifest, and any available sidecars. The `data/` directory holds the database and profile images. Copy `archive/library` to export just the media. To browse the files in Jellyfin, mount that directory read-only and use a Home Videos and Photos library. Direct playback depends on the Jellyfin client and codecs.

## Update or move the library

Under **Settings → System**, choose **Update yt-dlp** to check the stable PyPI release. GridTube keeps the active version until the new version has passed an import check and the app restarts. Choose **Restart and apply** in Docker when a version is ready. A restart interrupts playback and resumes queued work. The activity log shows recent update results and errors. The installed update is stored in the `data/` volume and survives container recreation.

After updating the source, run the same Docker Compose command. The `data/` and `archive/` directories are bind-mounted and survive container recreation. Stop the service before copying both directories for a full migration. For an offline installation, also bring your Compose file and an image exported with Docker for the target machine's architecture.

See the [architecture and operations notes (PT-BR)](ARQUITETURA.md) for storage, API routes, and recovery. GridTube is an independent project inspired by [UnTube](https://github.com/tomfriart/untube).
