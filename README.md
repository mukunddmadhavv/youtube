# Richard YouTube automation

## Web dashboard

Richard Studio runs at **http://localhost:2021** with a video library, topic-based
creation, revision requests, video/QA/log review, activity queue, topic ideas and
automation settings. Login details are in the local `secrets/dashboard-login.txt`.
The Jev video is imported as a review draft.

Run `scripts/dashboard.py serve` and `scripts/dashboard.py worker` with the
workspace Python environment. Full setup and portable Linux/systemd + Cloudflare
instructions for **u.trypitch.co** are in [deploy/README.md](deploy/README.md).
The tunnel token will be supplied on the destination SSH host; the public URL
is not live until that connector and the Cloudflare hostname route are enabled.

Richard system-design and DevOps videos: **16:9, 1920×1080, 3–8 minutes**.
The agent and local skill adapt the existing Instagram Richard teaching style
to YouTube, including landscape staging, longer explanations and thumbnails.

## Extracted Pitch animation references

Richard's skill now includes `references/launch-video-motion.md` and
`references/launch-video-catalog.json`, extracted from
`/home/mukund/launchVdo/.opencode/skills/launch-video/` and its referenced effects lab.
The curated set covers focus cameras, request-path reveals, record/detail
expansion, precision zooms, pending-to-success transitions, metric traces and
a constrained code-fix treatment. It also carries narration-first timing,
reading windows, semantic object handoffs and 16:9 adaptation rules.

The catalog distinguishes inspected source implementations/frame strips from
additional discovery candidates. This is a recipe/reference extraction, not
a pre-rendered or verified animation package. The agent reads it before choosing
episode motion and ports selected techniques to HyperFrames/Anime.js, with
per-episode seek, readability and export checks. Restart OpenCode to load the
updated agent and skill; scheduled fresh sessions pick them up automatically.

## Connected services

YouTube OAuth has been refreshed and verified for **TryPitch**
(`UCFV3h0SLRPmkmK73Wbs0Evw`). The supplied **This vs That** playlist
(`PLLhVdhaJxBTc`) was verified and is configured for new uploads. Category is
22 as supplied. Credentials live in permission-restricted `secrets/` files;
the existing broad YouTube grant is accepted without re-consent or revocation.

Supabase now has a dedicated **`public.richard_youtube_episodes`** table and
private **`richard-youtube`** storage bucket. The additive SQL migration is in
`migrations/001_richard_youtube.sql`. Existing application/Instagram tables,
their rows, storage objects and bucket settings were not modified by setup.
Only the new table has its own RLS and service-role grants.

For each validated episode, the pipeline uploads the video, thumbnail, manifest
and required delivery/QA artifacts. Remote bytes are SHA-256 checked before
recording success. Object names include the pipeline UUID, episode ID and
content hash, and uploads never overwrite an existing object. Each new episode
inserts a row; later publication/status updates target its pipeline/episode
key. The new table stores file paths, hashes, manifest, topic, status, slot and
YouTube ID. It does not store video binary data directly in PostgreSQL.

SQLite remains the local scheduling authority. Supabase is the durable archive
and metadata mirror; it is not a multi-host queue or automatic local restore.
Archival runs after production, before publication, and on the existing
five-minute publisher cron poll. Failed syncs are retried without regenerating
or reuploading an already-published YouTube video. Private artifacts can be
viewed/downloaded via authenticated Storage access or the Supabase dashboard.
The bucket inherits the project's storage limits; exceeding a limit leaves
the episode local and raises a retryable archive error rather than publishing
without the required archive. Generated supporting assets beyond the manifest's
explicit handoff files stay in the local editable project.

```sh
.venv/bin/python scripts/check_connections.py  # Remote read-only checks; OAuth may refresh
.venv/bin/python scripts/pipeline.py sync      # Retry archival/status sync now
```

The Supabase credentials are in `secrets/supabase.env`. The direct PostgreSQL
connection is used only by explicit setup/inspection commands; recurring workers
use the scoped table endpoint and Storage API. Production sessions are instructed
not to access `secrets/` or manage Supabase. No episode rows have been fabricated
to represent videos that have not yet been made.

## What runs

- **Hourly buffer check:** if fewer than 10 validated videos are ready, create
  up to two new episodes sequentially. Recheck the count after each. Subsequent
  hourly runs continue filling the buffer. Only one production worker runs at
  once; a long render can outlast the hourly interval.
- **Two publishing slots daily:** defaults **09:00 and 18:00 Asia/Kolkata**.
  A lightweight cron poll checks every five minutes; Python applies the named
  timezone, independent of the Mac's timezone. Edit these defaults in pipeline.json.
- Each episode gets a **new `opencode run --agent richardSystemDesign` session**,
  an output directory, a commissioned brief, and the topic history.
- SQLite holds queue state. File locks prevent overlapping workers. The agent
  chooses fresh topics; a unique topic key rejects exact duplicates. Topic
  history helps avoid semantic duplicates but cannot guarantee novelty by itself.
- Ready means a valid manifest, required QA evidence, 1080p/30fps H.264 video,
  AAC audio, 180–480-second duration and a valid thumbnail. Files are hashed
  and rechecked before upload. Semantic QA is performed by the production
  workflow; artifact checks alone do not prove a video is good.
- Upload privately, save the YouTube ID, set the thumbnail, then make it public.
  Publication is reported only after confirming public visibility.

## Files

| Path | Purpose |
| --- | --- |
| `.opencode/agents/richardSystemDesign.md` | OpenCode Richard agent |
| `.opencode/skills/richard-system-design/` | Teaching, motion, landscape and delivery contract |
| `pipeline.json` | Activation, slots, timezone, buffer, channel and model settings |
| `scripts/pipeline.py` | Production queue, OAuth, upload and cron management |
| `topics.json` | Initial topic ideas; agent can research beyond this list |
| `assets/characters/richard/` | Your original character PNGs |
| `output/<id>/` | Editable episode, render, manifest, QA and session log |
| `state/queue.sqlite3` | Durable episode/topic/publishing history |
| `state/buffer.log`, `state/publish.log` | Cron logs |
| `secrets/` | Local Google client JSON and OAuth refresh token; ignored by Git |

## Setup and activation

Run commands from `/home/mukund/youtube`. The Python environment has been
installed here; to recreate it:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

1. Put transparent `char_intro.png`, `char_point_left.png` and
   `char_point_right.png` into `assets/characters/richard/`. Update configured
   paths if your names differ. The original Instagram workspace is not needed
   by this pipeline.
2. Save a project `.env` based on `.env.example` with `ELEVEN_LABS_KEY`.
   Adam is the reference voice; authenticated access and a delivery audition
   are verified during production. Keep secrets out of chat.
3. Ensure OpenCode is signed into a provider that can produce these episodes.
   Set `model` in pipeline.json to an available `provider/model-id` for a fixed
   production model; an empty string uses OpenCode's configured default.
   HyperFrames/FFmpeg and the production skills must be available to that session.
4. YouTube is already connected. For a future replacement connection, in Google Cloud, enable **YouTube Data API v3**, configure the OAuth consent
   screen, and create an OAuth **Desktop app** client. Save its downloaded JSON
   as `secrets/client_secret.json` (create the directory locally). If the consent
   app is in Testing, add your account as a test user.
5. Authorize the intended YouTube/Brand channel:

   ```sh
   .venv/bin/python scripts/pipeline.py auth
   ```

   This opens Google's consent page and saves a local refresh token. Set the
   printed channel ID as `channel_id` in pipeline.json. Every publisher run
   checks that the authorized channel matches. No YouTube password is needed.
6. Set your timezone, two times, language and YouTube audience/disclosure fields
   in pipeline.json. Current defaults are English, developer audience (not
   made for kids), and no realistic synthetic-media disclosure. Set the latter
   according to the actual content; a cartoon presenter alone is not a realistic
   impersonation. These are channel/video decisions, not model guesses.
7. Check setup:

   ```sh
   .venv/bin/python scripts/pipeline.py doctor
   ```

8. Set `generation_enabled` to `true`. The hourly worker will start filling the
   buffer, or start a run now:

   ```sh
   .venv/bin/python scripts/pipeline.py buffer
   ```

9. After YouTube authorization is complete, set `publishing_enabled` to `true`.
   Only ready episodes can publish. You can fill the buffer before enabling it.

Cron installation is idempotent and preserves unrelated entries:

```sh
.venv/bin/python scripts/pipeline.py install-cron
.venv/bin/python scripts/pipeline.py status
```

Both activation flags are **false** while artwork and voice credentials are
still to be supplied. YouTube OAuth and Supabase are connected. Cron is installed in this state;
the jobs simply report that they are disabled. Switching a flag is picked up
on the next run. After editing OpenCode agent/config/skill definitions, **quit
and restart OpenCode**; every scheduled CLI run already starts fresh.

## Schedule behavior and operational limits

- The publisher attempts within 30 minutes of each slot. Upload and YouTube
  processing take time, so visibility is not guaranteed at the exact minute.
  An empty queue can be retried during that window. Old missed slots are not
  replayed, preventing a burst of backdated publications.
- The Mac must be awake, online and able to run cron. Sleeping/offline hosts
  miss jobs. For uninterrupted daily delivery, run this workspace on an
  always-on host and update absolute paths in the config/agent before installing
  cron there. There is no cloud service deployed by this setup.
- Failed generations stay failed and do not count toward the buffer. The
  next hourly run creates a fresh session. Session logs and BLOCKED.md explain
  missing capabilities; a process exit code alone never admits a video.
- A killed parent may leave an unfinished `generating` job. Production pauses
  to avoid launching a duplicate costly job. Inspect `worker.json` and the
  process/session log before recovery.
- YouTube may restrict uploads from unverified API projects to private videos;
  resolve the API project's upload/publication restrictions before expecting
  public automation. Enable custom thumbnails on the channel. Consent apps in
  Testing can issue short-lived refresh tokens, requiring authorization again;
  configure the OAuth app appropriately for unattended long-term use.
- This is one host, one queue, and one authorized channel. Generation consumes
  model/TTS/render resources; available capacity must sustain two episodes/day.
  There are no automatic monitoring alerts or log/artifact retention policy.
- SRT captions are delivered locally; this version uploads the video and
  thumbnail, not a separate YouTube caption track.

## Recovery and inspection

```sh
.venv/bin/python scripts/pipeline.py status
.venv/bin/python scripts/pipeline.py validate EPISODE_ID
.venv/bin/python scripts/pipeline.py fail EPISODE_ID
```

`validate` rechecks a repaired production folder and admits it if valid.
`fail` abandons an unassigned production job after you have stopped any orphan
worker. Neither command can reset an upload or reuse a reserved publishing slot.

If the network drops during insert, the server might have accepted the video
without returning its ID. The job stays `uploading`, and **inserts are never
automatically repeated**. Inspect YouTube Studio using the title/episode
reference, then associate the existing upload:

```sh
.venv/bin/python scripts/pipeline.py reconcile EPISODE_ID YOUTUBE_VIDEO_ID
.venv/bin/python scripts/pipeline.py retry-finish EPISODE_ID
```

Reconciliation checks channel ownership and title; verify the actual content
in Studio as well. `retry-finish` explicitly retries thumbnail/public visibility
on the known ID, even outside the original slot; it never creates a new upload.
Pending uncertain uploads block new slots until resolved. If Studio confirms
no upload exists, investigate the database record before manually repairing it;
there is deliberately no automatic reset that could duplicate public content.

## Verification

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests cover timezone/grace handling, duplicate slots, concurrency locks, queue
admission, changed artifacts, duration/audio/QA rejection, duplicate topic keys,
fresh-session invocation, upload uncertainty, known-ID retries, private-only
responses, disabled behavior and non-destructive cron installation. API calls
are mocked: live OAuth, narration, rendering and channel publication still need
the supplied assets and credentials and a real first episode.
