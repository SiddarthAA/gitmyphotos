# GitMyPhotos

> **Work in progress** — first release coming soon. To contribute, open a PR or reach out at [siddartha_ay@protonmail.com](mailto:siddartha_ay@protonmail.com).

Your photos. Your repo. Your rules. Zero lock-in.

GitMyPhotos is a self-hosted, open-source pipeline that commits your photos directly into a private GitHub repository — structured, versioned, and retrievable forever. No subscription. No proprietary cloud. No middleman with a kill switch.

---

## What it is

Most photo platforms run the same playbook: free storage, compressed originals, proprietary lock-in, then a price hike. GitMyPhotos is not a storage provider. It is a pipeline. You run it locally, it pushes your photos at full resolution to a GitHub repository you own entirely. When you stop using this tool, every photo is still exactly where it was — in your repo, yours forever.

---

## How it works

Every upload goes through a four-stage pipeline that produces exactly one atomic Git commit, regardless of how many photos are in the batch.

### Stage 1 — Ingest
A photo lands in the ingest layer. Its MIME type is validated against a known list (JPEG, PNG, WEBP, HEIC, TIFF, GIF, BMP, and RAW formats including CR2, CR3, NEF, ARW, DNG, RAF, ORF, RW2). Size is checked. A collision-proof filename is stamped from the EXIF capture timestamp down to the millisecond.

### Stage 2 — Process
EXIF metadata is extracted. GPS coordinates are resolved. A 400px thumbnail is generated with Pillow. A JSON sidecar is compiled containing all metadata. Three artefacts are staged: original, thumbnail, and sidecar.

### Stage 3 — Commit
The GitHub Git Tree API is used to build one atomic commit containing all staged files. The flow is:

1. `GET` current HEAD commit SHA
2. `GET` tree SHA from that commit
3. Build tree items (text content inline, binary files as blob SHAs)
4. `POST` new tree
5. `POST` new commit object
6. `PATCH` branch ref to new commit SHA

Every batch — whether one photo or ten thousand — produces exactly one commit. The manifest and regenerated README are included in the same operation.

### Stage 4 — Serve
The manifest is cached locally after the first load — one API call per session, regardless of library size. Thumbnails are served from disk cache after first view. Previews are generated on demand and cached immediately. Originals are fetched directly from your repository on request. GitHub API usage at browse time is effectively zero.

---

## Repository structure

Photos are organized into three directories inside your GitHub repo:

```
originals/YYYY/MM/          # Full-resolution files, untouched
thumbs/YYYY/MM/             # 400px thumbnails
meta/YYYY/MM/               # JSON sidecar per photo
manifest.json               # Full index of all photos
README.md                   # Auto-generated, updated on every commit
```

The manifest is date-partitioned, human-readable, and git-native. Every photo is a file. Every change is a commit. The entire history of your library is in `git log`.

---

## Tech stack

### Backend
- **Python 3.12** with **FastAPI** and **Uvicorn**
- **Pillow** for thumbnail generation and image processing
- **exifread** for EXIF metadata extraction
- **httpx** for GitHub API communication
- **pydantic-settings** for configuration management
- **python-dotenv** for `.env` handling
- GitHub OAuth for authentication; GitHub Git Tree API for atomic commits

### Frontend
- **Next.js 16** (App Router) with **React 19** and **TypeScript**
- **Tailwind CSS v4** for styling
- **Framer Motion** for animations
- **Radix UI** primitives for accessible components
- **Lucide React** for icons

### Infrastructure
- **Docker Compose** — two containers, zero external dependencies
  - `backend` on `:8000`
  - `frontend` on `:3000`
- Local disk cache at `data/cache/` — thumbnails, previews, manifest
- Config written to `data/.env` — never committed

No S3. No Redis. No Postgres. Nothing outside Docker.

---

## Getting started

### Prerequisites
- Docker and Docker Compose
- A GitHub account
- A GitHub OAuth App ([create one here](https://github.com/settings/developers)) with callback URL `http://localhost:8000/auth/callback`

### Setup

```bash
git clone https://github.com/SiddarthAA/gitmyphotos
cd gitmyphotos
cp data/.env.example data/.env   # fill in GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET
docker compose up
```

Open [http://localhost:3000](http://localhost:3000). Authenticate via GitHub OAuth. Connect an existing private repository or create a new one from the UI. GitMyPhotos scaffolds the folder structure and commits the initial manifest in one atomic operation.

### Configuration

All configuration lives in `data/.env`. The app writes OAuth tokens and repo settings back to this file after authentication — you only need to supply the OAuth app credentials manually.

| Variable | Description |
|---|---|
| `GITHUB_CLIENT_ID` | Your GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | Your GitHub OAuth App client secret |
| `CACHE_MAX_PREVIEW_GB` | Max disk space for preview cache (default: `2.0`) |

---

## Project structure

```
backend/app/
├── config.py           # Settings via pydantic-settings
├── main.py             # FastAPI entry point, lifespan startup
├── github/             # GitHub API layer (blobs, trees, commits)
├── models/             # Pydantic models (photo, manifest, config)
├── pipeline/           # Ingest → EXIF → thumbnail → metadata → README
├── routes/             # FastAPI route handlers
├── services/           # Auth, cache, manifest, pipeline, repo services
└── utils/              # Filename collision, image helpers, path utils

frontend/
├── app/                # Next.js App Router pages
├── components/         # UI components (photos, repo, sidebar, shell)
├── hooks/              # useAuth, useManifest, useRepo, useUpload
└── lib/                # API client, types, utilities
```

---

## Design decisions

**One commit per batch, not per file.** Batching all staged files into a single atomic Git operation keeps the commit history clean and minimises GitHub API calls per upload session.

**Manifest-first browsing.** The entire library index is one JSON file fetched once per session. Pagination, filtering, and grouping all happen client-side from that single read. Browsing ten thousand photos costs the same API budget as browsing ten.

**No external services.** The architecture is intentionally minimal. The only network dependency is the GitHub API. There is no database, no message queue, no object store. The local cache is a plain directory of files that can be deleted and rebuilt at any time.

**Config as a writable `.env`.** Credentials and repo settings are written back to a mounted `.env` file by the app itself. This avoids the need for a database while keeping config durable across container restarts.

---

## Contributing

This project is a work in progress. Contributions are welcome.

- Open a pull request on [GitHub](https://github.com/SiddarthAA/gitmyphotos)
- Or reach out directly at [siddartha_ay@protonmail.com](mailto:siddartha_ay@protonmail.com)

---

## License

MIT. No telemetry. No analytics. No data leaves your machine. Auditable. Forkable. Yours.
