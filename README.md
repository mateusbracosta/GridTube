# GridTube

English · [Português do Brasil](README.pt-BR.md)

GridTube is a self-hosted video library for preserving YouTube videos and watching them offline. Download videos while connected, then browse and play your archive over your local network.

- Browse a channel's videos, Shorts, live archives, and playlists before choosing what to download. Set a title rule and optionally follow new uploads.
- Choose **Compact** or **Original quality** globally, by channel, or for a single link. Compact finds a smaller variant within your resolution limit. Original requests the best available resolution and frame rate. The main audio and video streams are copied from YouTube.
- Save preferred audio and subtitle languages. Find and download additional tracks from the player when the source offers them.
- Organize videos into channels and playlists. The interface supports English and Brazilian Portuguese.

## Run with Docker

With Git, Docker and Compose installed, clone the repository and start GridTube.

~~~sh
git clone https://github.com/mateusbracosta/GridTube.git
cd GridTube
docker compose up -d --build --wait
~~~

Open [GridTube](http://localhost:3987). The default bind address is 127.0.0.1. To use it on a trusted local network, set `GRIDTUBE_BIND` to your host's LAN IP address. `GRIDTUBE_PORT` changes the host port. GridTube currently has no user authentication.

Click the GridTube logo to return to the library from another screen. Clicking it while already in the library reloads the page. The red grid-and-play symbol is used in the app and its browser favicon.

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

**Downloads** shows the title of a queued video as soon as it is available, with the video ID while the title is unavailable. Progress shows the current phase and its percentage. The app uses transferred bytes for video and audio downloads, and the processed media duration reported by FFmpeg when assembling a file. It labels estimates and uses an indeterminate bar when progress cannot be measured.

Choose **Icon and color** when creating or editing a local channel. For playlists created in the app, use **Customize** in the playlist header. The choices appear in the sidebar and headers and are included in the catalog backup.

Right-click a video and choose **Select video**, or use the video's three-dot menu, to start selecting items. The selection bar and checkboxes appear after the first item is selected and disappear when the last item is deselected or the selection is cleared. **Select this page** marks the visible page; selections are kept as you move between pages. Shift-click selects a range on the current page. Changing the collection or search clears the selection. **Delete selected** lets you keep the files or erase them from disk.

Use **Edit channel → Delete channel and videos** to remove a channel. Playlists offer **Delete playlist and videos** in their header. The confirmation includes all collection items, across all pages, and warns about videos shared with other playlists. Deleting a playlist's videos affects those same videos throughout the library. Keeping files moves videos to **Removed**; deleting a channel leaves restored videos in **Unfiled**. Downloads are stopped before deleting their files. The deleted collection itself is not retained.

Channel profiles prefer the app's selected language and the browser's regional preference. On the first visit, the interface uses a supported browser language; an explicitly saved PT-BR/EN choice takes priority. Opening a channel fetches its profile in the selected locale when that version is missing. Saved versions remain available offline and switching languages keeps each version separate. YouTube may return the original text when no translation is available. Custom channel names and descriptions are kept as entered.

Under **Organize video**, the channel and playlist selectors include **Create a new channel…** and **Create a new playlist…**. Saving the creation form moves or adds the current video automatically. Deletion actions have red styling and trash icons; disk-erasure confirmations use solid red buttons.

Use **Cancel** to remove a queued item or interrupt a download and its muxing process. An active item shows **Cancelling…** until the process stops and its temporary files are cleared. An in-flight network request may need to finish first. **Remove attempt** clears a failed task from the list. You can add the video again later.

In the player settings, use the trash button next to a selected extra track to delete its file from disk. The trash button next to a failed attempt clears the attempt. Video cards use the saved YouTube thumbnail when available and keep the watch position for the progress bar and playback resume.

The player centers subtitles at the bottom. **Open on YouTube** is available on the watch page and in the video card's three-dot menu.

From **Organize video → Remove video**, choose **Remove from library** to keep the files and restore the entry later from **Removed**, or **Also delete from disk** to erase the saved bundle. Disk deletion requires a writable archive mount.

GridTube puts videos in the archive's `library/` folder, one directory per video, with the MP4 or WebM, a local JSON manifest, and any available sidecars. The `data/` directory holds the database and profile images. Copy `library/` to export just the media. To browse the files in Jellyfin, mount that directory read-only and use a Home Videos and Photos library. Direct playback depends on the Jellyfin client and codecs.

Each playlist also has a UTF-8 `playlist.m3u8` in the archive's `Playlists/` directory. Copy `library/` and `Playlists/` together to retain the relative paths. For a single playlist, use **Export playlist as ZIP** in its header. The archive contains the playlist, videos and available sidecars with paths relative to the extracted folder.

### Access the archive from Nextcloud

Point Nextcloud local external storage at the archive's `library/` directory and name the mount **Videos**. This keeps partial downloads and playback cache outside the Nextcloud mount. You can download copies directly from Nextcloud.

After deleting a video or moving its folder in Nextcloud, open **Settings → System → Check archive files** in GridTube. When moving a video between channel directories already in the archive, move its entire folder, retaining the `[ID]` suffix and the `video.json` manifest. Moving only the MP4 or WebM out of its folder puts the video in **Removed**.

GridTube updates paths and playlists for recognized moves. When the media is missing, it keeps progress and playlist memberships under **Removed**. To recover, return the file to its original folder and check again, or select **Download again**. The check updates the catalog and leaves the files on disk.

### Backup, restore and clear app data

Under **Settings → System**, export a catalog backup as `gridtube-backup.jsonl`. It includes channels, playlists, video records, download jobs, watch progress and preferences. **Restore backup** opens a file picker. GridTube validates the selected file, applies its data when it restarts and verifies the database integrity and restored records. The screen confirms **Backup restored and verified** when the checks finish.

The media files stay in the archive. To move to a new host, copy the archive before restoring its catalog. Missing videos appear in **Removed** and can be restored after copying their files.

**Clear app data** resets the catalog, preferences and generated files. The default confirmation is `RESET` and keeps the media in `library/`. With disk deletion selected, type `RESET MEDIA` to also erase that library. Restore and reset apply when the service restarts.

## Update or move the library

Under **Settings → System**, choose **Update yt-dlp** to check the stable PyPI release. GridTube keeps the active version until the new version has passed an import check and the app restarts. Choose **Restart and apply** in Docker when a version is ready. A restart interrupts playback and resumes queued work. The activity log shows recent update results and errors. The installed update is stored in the `data/` volume and survives container recreation.

After updating the source, run the same Docker Compose command. The `data/` directory and the archive folder are bind-mounted and survive container recreation. Stop the service before copying both directories for a full migration. For an offline installation, also bring your Compose file and an image exported with Docker for the target machine's architecture.

See the [architecture and operations notes (PT-BR)](ARQUITETURA.md) for storage, API routes, and recovery.
