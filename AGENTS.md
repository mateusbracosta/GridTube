# Working on GridTube

- Keep the interface and user-facing documentation available in English and Brazilian Portuguese. Write commits in English.
- Preserve real `data/` and archive mounts. Run destructive tests only against disposable libraries.
- Read and update the project's Obsidian memory when it is available locally. Never publish vault contents, user data, credentials, or local environment files.

## Delivering application updates

The project owner requested GitHub Releases for application updates, starting with v0.7.16.

1. Update the application image version in `compose.yaml` and relevant documentation.
2. Run checks appropriate to the change and resolve relevant failures before publishing. Identify emulated ARM64 validation explicitly.
3. Commit in English and push the tested update to `main`.
4. Publish a GitHub Release named `GridTube v<version>` with tag `v<version>` targeting the delivered commit. Include English and PT-BR change and validation notes. Verify the published tag and Release.
5. After the new Release is published and verified as Latest, remove older GitHub Release entries so only the latest Release remains on the site. Preserve Git tags and commit history unless the owner explicitly requests otherwise. Never remove the previous Release before the replacement is verified.
6. Update project memory with the version, commit, checks, limitations, and Release link.

Do not generate local source packages or Docker image export archives automatically. GitHub supplies source archives for published tags. Do not attach real media, databases, backups, or environment files to Releases.
