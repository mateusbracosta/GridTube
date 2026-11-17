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

### Choose a drive and folder for your videos

Before starting GridTube, create a `.env` file next to `compose.yaml` and set the archive path on the Docker host. Choose the line for your system and replace the example path.

~~~dotenv
# Windows
GRIDTUBE_ARCHIVE_PATH="D:/Geral/GridTube/Videos"
# Linux or Orange Pi (use this instead on Linux)
# GRIDTUBE_ARCHIVE_PATH=/mnt/hd/GridTube/Videos
~~~

Saved videos go in `library/` inside that folder. Working files and playback cache go in `work/` on the same drive. The default archive folder is `./archive`. To migrate an existing installation, run `docker compose stop`, copy the contents of the current archive to the new folder, then set the path and run `docker compose up -d --wait`.

### ARM64 and small servers

The same Compose command builds GridTube on a 64-bit Docker host, including boards such as the Orange Pi Zero 3 running a 64-bit Linux distribution. `uname -m` should report `aarch64` on the board. Serve the library from the board and play it in a browser on your local network. The browser decodes the video and its codec support determines playback compatibility.

Set `GRIDTUBE_PLAYBACK_CACHE_MIB=512` in `.env` if disk space is tight. The default is 4096 MiB. The cache holds temporary versions for alternate audio and keeps the version being prepared even if it exceeds the target. The original files stay in the library. Keeping the archive on a USB drive leaves space on the system card.

## Use the archive

1. Choose **Add channel** to browse a channel or **Download link** to save an individual video.
2. In the download options, choose the quality mode, preferred audio language, and subtitles. A channel can override global defaults, and a link can override either.
3. Open a saved video from the library. Use the player gear to switch between saved tracks or discover additional tracks while online.

**Downloads** shows the current phase and its percentage. The app uses transferred bytes for video and audio downloads, and the processed media duration reported by FFmpeg when assembling a file. It labels estimates and uses an indeterminate bar when progress cannot be measured.

From **Organize video → Remove video**, choose **Remove from library** to keep the files and restore the entry later from **Removed**, or **Also delete from disk** to erase the saved bundle. Disk deletion requires a writable archive mount.

GridTube puts videos in the archive's `library/` folder, one directory per video, with the MP4 or WebM, a local JSON manifest, and any available sidecars. The `data/` directory holds the database and profile images. Copy `library/` to export just the media. To browse the files in Jellyfin, mount that directory read-only and use a Home Videos and Photos library. Direct playback depends on the Jellyfin client and codecs.

Each playlist also has a UTF-8 `playlist.m3u8` in the archive's `Playlists/` directory. Copy `library/` and `Playlists/` together to retain the relative paths. For a single playlist, use **Export playlist as ZIP** in its header. The archive contains the playlist, videos and available sidecars with paths relative to the extracted folder.

### Access the archive from Nextcloud

Point Nextcloud local external storage at the archive's `library/` directory and name the mount **Videos**. This keeps partial downloads and playback cache outside the Nextcloud mount. You can download copies directly from Nextcloud.

After deleting a video or moving its folder in Nextcloud, open **Settings → System → Check archive files** in GridTube. When moving a video between channel directories already in the archive, move its entire folder, retaining the `[ID]` suffix and the `video.json` manifest. Moving only the MP4 or WebM out of its folder puts the video in **Removed**.

GridTube updates paths and playlists for recognized moves. When the media is missing, it keeps progress and playlist memberships under **Removed**. To recover, return the file to its original folder and check again, or select **Download again**. The check updates the catalog and leaves the files on disk.

### Backup, restore and clear app data

Under **Settings → System**, export a catalog backup as `gridtube-backup.jsonl`. It includes channels, playlists, video records, download jobs, watch progress and preferences. The media files stay in the archive. To move to a new host, copy the archive and preview the backup before applying it. Missing videos appear in **Removed** and can be restored after copying their files.

**Clear app data** resets the catalog, preferences and generated files. The default confirmation is `RESET` and keeps the media in `library/`. With disk deletion selected, type `RESET MEDIA` to also erase that library. Restore and reset apply when the service restarts.

## Update or move the library

Under **Settings → System**, choose **Update yt-dlp** to check the stable PyPI release. GridTube keeps the active version until the new version has passed an import check and the app restarts. Choose **Restart and apply** in Docker when a version is ready. A restart interrupts playback and resumes queued work. The activity log shows recent update results and errors. The installed update is stored in the `data/` volume and survives container recreation.

After updating the source, run the same Docker Compose command. The `data/` directory and the archive folder are bind-mounted and survive container recreation. Stop the service before copying both directories for a full migration. For an offline installation, also bring your Compose file and an image exported with Docker for the target machine's architecture.

See the [architecture and operations notes (PT-BR)](ARQUITETURA.md) for storage, API routes, and recovery. GridTube is an independent project inspired by [UnTube](https://github.com/tomfriart/untube).
