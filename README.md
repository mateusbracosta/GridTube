# GridTube

English · [Português do Brasil](README.pt-BR.md)

[Latest release](https://github.com/mateusbracosta/GridTube/releases/latest)

GridTube is a self-hosted video library for preserving YouTube videos and watching them offline. Download videos while connected, then browse and play your archive over your local network.

- Browse a channel's videos, Shorts, live archives, and playlists before choosing what to download. Set a title rule and optionally follow new uploads.
- Set **Maximum resolution** globally, by channel, or for a single link. This limit applies to both **Compact** and **Original quality**. Compact finds a smaller variant at the best resolution and frame rate within the limit; Original follows the source's quality preference within the same limit. **Best available (no limit)** removes the resolution cap. The main audio and video streams are copied from YouTube.
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

The library, channels, Unfiled, playlists, Watched and Ignored have **Videos**, **Shorts** and **Live streams** tabs. Videos is the default. Returning from the player preserves the tab, page and filters. **Newest first / Oldest first** uses the publication date, falling back to capture date; the order is saved in this browser. Tabs filter the display without changing playlist memberships or files.

Each content tab offers **All, New, Today, This week, Unwatched and In progress**. Filters can be combined to narrow results; All clears them. Today and This week use publication dates and the browser's local day, with the week starting on Monday. In progress includes waiting/active downloads and partially watched videos. All is the default and keeps watched videos visible.

Channel actions, content tabs, filters and sorting share compact rounded 28-pixel controls, consistent corners and small outline icons, with subdued selection colors.

Selected downloads appear immediately as cards in the channel and library, with their title, thumbnail preview, queue state and measured progress. Errors appear on the card and in Downloads, with retry and trash controls. Pending thumbnail previews come from YouTube while online; completed videos use saved local thumbnails. No percentage is invented when progress cannot be measured.

Use **Mark as watched / Mark as unwatched** in the video menu. Finishing playback also marks it watched. **Watched** in the sidebar lists these videos. The former Continue watching menu is now **Ignored**: **Ignore video** hides a saved video from ordinary lists and suggestions while preserving its files, progress, channel and playlist memberships. Use **Return to library** under Ignored to show it again. Direct playback links and exports remain available.

When channel monitoring downloads a newly discovered video automatically, its card shows **New** until you open it. Manual downloads and existing videos do not receive this badge. Opening clears it persistently for this shared library, even without starting playback. **New badge duration (days)** defaults to **Until the video is opened** (empty or 0); a custom number expires it earlier when that time elapses. Marking it watched also clears New.

In **Settings → Downloads**, **Shorts** and **Live streams** control all new captures: manual selections, links, retries and channel monitoring. Each channel can override the global choice. **Do not download** blocks that type without deleting existing videos, subtitles, audio tracks or progress. **Shorts only** also blocks regular videos and live recordings. Waiting jobs are checked again against current preferences before capture; blocked jobs show a reason and can be retried after changing the preference. Already running transfers are not forcibly cancelled. These download rules are separate from Interface visibility settings.

Both selectors offer **Allow / Do not download / Only**, with explicit type names. **Live streams only** downloads just live recordings. If both types are set to Only, their union is allowed: Shorts and live recordings, without regular videos.

**Maximum video duration (minutes)** defaults to **No limit** (empty or 0) and accepts a custom whole number. Channels can inherit the global limit or use 0 for no limit. **Automatically delete from disk after (days)** defaults to **Never** (empty or 0). A custom value permanently removes expired video bundles, sidecars and their catalog records, including ignored videos. Age starts at download completion; older archives without that timestamp use their capture date. Checks run periodically in batches and respect files being exported or prepared for playback. This setting is global; its activity and errors appear in System.

The duration ceiling also filters the channel selection catalog, its counts and Select all results. With a ceiling active, candidates with unknown duration are omitted until it can be confirmed. Saved videos remain accessible. Download fields share aligned controls; optional explanatory text can be expanded under Download preferences help.

In **Settings → Interface**, **Never show Shorts** and **Never show live streams** hide their tabs and content across the library, channels, playlists, Unfiled, Watched, Ignored and suggestions. These choices are saved in the current browser and do not affect downloads or files. Download and removal queues remain visible for management.

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
