#!/usr/bin/env python3
"""Durable single-host Richard production queue and YouTube publisher."""

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
CHECKS = ("facts", "full_playback", "full_listening", "motion_and_sync",
          "seek_determinism", "readability", "thumbnail")
ARTIFACTS = ("script", "sources", "storyboard", "composition", "captions", "audio", "assets")


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(path)


def config():
    c = json.loads((ROOT / "pipeline.json").read_text())
    return validate_config(c)


def validate_config(c):
    ZoneInfo(c["timezone"])
    times = c["publish_times"]
    if len(times) != 2 or len(set(times)) != 2:
        raise ValueError("Configure two distinct daily publish_times")
    for value in times:
        datetime.strptime(value, "%H:%M")
        if not re.fullmatch(r"\d{2}:\d{2}", value):
            raise ValueError("publish_times must be HH:MM")
    for key in ("buffer_target", "max_generations_per_run", "generation_timeout_seconds"):
        if not isinstance(c[key], int) or c[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    if not 1 <= c["slot_grace_minutes"] <= 180:
        raise ValueError("slot_grace_minutes must be 1–180")
    for key in ("generation_enabled", "publishing_enabled", "made_for_kids", "contains_synthetic_media"):
        if not isinstance(c[key], bool):
            raise ValueError(f"{key} must be boolean")
    if "auto_admit" in c and not isinstance(c["auto_admit"], bool):
        raise ValueError("auto_admit must be boolean")
    if "upload_thumbnails" in c and not isinstance(c["upload_thumbnails"], bool):
        raise ValueError("upload_thumbnails must be boolean")
    return c


def db():
    (ROOT / "state").mkdir(exist_ok=True)
    conn = sqlite3.connect(ROOT / "state/queue.sqlite3", timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS episodes (
            id TEXT PRIMARY KEY, status TEXT NOT NULL, topic_key TEXT UNIQUE,
            title TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            hashes TEXT, youtube_id TEXT UNIQUE, slot TEXT UNIQUE, error TEXT
        );
        CREATE TABLE IF NOT EXISTS archive_receipts (
            episode_id TEXT PRIMARY KEY, source_updated_at TEXT NOT NULL
        );
    """)
    return conn


@contextlib.contextmanager
def lock(name):
    directory = ROOT / "state"
    directory.mkdir(exist_ok=True)
    with (directory / f"{name}.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def update(conn, episode_id, **fields):
    fields["updated_at"] = utcnow()
    with conn:
        conn.execute("UPDATE episodes SET " + ", ".join(f"{key}=?" for key in fields)
                     + " WHERE id=?", (*fields.values(), episode_id))


def episode_dir(episode_id):
    if not re.fullmatch(r"[a-z0-9-]+", episode_id):
        raise ValueError("Invalid episode ID")
    return ROOT / "output" / episode_id


def local_file(folder, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Artifact must be a relative path")
    path = (folder / relative).resolve()
    if not path.is_relative_to(folder.resolve()) or not path.is_file() or not path.stat().st_size:
        raise ValueError(f"Missing, empty, or out-of-folder artifact: {relative}")
    return path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                             "-of", "json", str(path)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def validate_files(episode_id):
    folder = episode_dir(episode_id)
    manifest = local_file(folder, "episode.json")
    data = json.loads(manifest.read_text())
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", data["topic_key"]):
        raise ValueError("topic_key must be a lowercase hyphenated topic")
    if not isinstance(data["title"], str) or not 1 <= len(data["title"].strip()) <= 100:
        raise ValueError("Title must be 1–100 characters")
    if any(char in data["title"] for char in "<>"):
        raise ValueError("YouTube titles cannot contain angle brackets")
    if not isinstance(data["description"], str) or not 1 <= len(data["description"].encode()) <= 5000:
        raise ValueError("Description must be 1–5000 UTF-8 bytes")
    if any(char in data["description"] for char in "<>"):
        raise ValueError("YouTube descriptions cannot contain angle brackets (< or >); use 'under', 'over', etc.")
    tags = data.get("tags", [])
    if (not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags)
            or sum(len(t) + 3 for t in tags) > 450):
        raise ValueError("Invalid tags or tags too long")
    if any(any(char in t for char in "<>") for t in tags):
        raise ValueError("YouTube tags cannot contain angle brackets (< or >)")
    qa = data["qa"]
    if qa["status"] != "passed":
        raise ValueError("QA has not passed")
    files = [manifest, local_file(folder, data["video"]), local_file(folder, data["thumbnail"]),
             local_file(folder, qa["report"])]
    for name in ARTIFACTS:
        files.append(local_file(folder, data["artifacts"][name]))
    for name in CHECKS:
        check = qa["checks"][name]
        if check["status"] != "passed":
            raise ValueError(f"QA {name} has not passed")
        files.append(local_file(folder, check["evidence"]))
    video = files[1]
    if video.suffix.lower() != ".mp4":
        raise ValueError("Video must be an MP4")
    info = probe(video)
    streams = info["streams"]
    vs = next(s for s in streams if s["codec_type"] == "video")
    audio = next((s for s in streams if s["codec_type"] == "audio"), None)
    duration = float(info["format"]["duration"])
    if not math.isfinite(duration) or not 180 <= duration <= 480:
        raise ValueError(f"Duration {duration}s is outside 180–480s")
    if (vs["width"], vs["height"], vs["codec_name"], vs.get("pix_fmt")) != (1920, 1080, "h264", "yuv420p"):
        raise ValueError("Export must be 1920×1080 H.264/yuv420p")
    if abs(float(Fraction(vs["avg_frame_rate"])) - 30) > 0.02:
        raise ValueError("Export must be 30fps")
    if vs.get("sample_aspect_ratio", "1:1") != "1:1":
        raise ValueError("Export must use square pixels")
    if not audio or audio["codec_name"] != "aac":
        raise ValueError("AAC audio is required")
    thumb = files[2]
    ts = probe(thumb)["streams"][0]
    if ((ts["width"], ts["height"]) != (1280, 720)
            or ts["codec_name"] not in ("png", "mjpeg") or thumb.stat().st_size >= 2_000_000):
        raise ValueError("Thumbnail must be 1280×720 PNG/JPEG under 2MB")
    hashes = {str(p.relative_to(folder.resolve())): digest(p) for p in files}
    return data, hashes


def admit(conn, episode_id):
    row = conn.execute("SELECT * FROM episodes WHERE id=?", (episode_id,)).fetchone()
    if not row or (row["slot"] and row["status"] not in ("uploading", "blocked", "failed")) or row["status"] not in ("generating", "failed", "draft", "ready", "uploading", "blocked"):
        raise ValueError("Only existing, unassigned generating/failed/ready episodes can be validated")
    data, hashes = validate_files(episode_id)
    update(conn, episode_id, status="ready", slot=None, topic_key=data["topic_key"], title=data["title"],
           hashes=json.dumps(hashes), error=None)


def unchanged(row):
    folder = episode_dir(row["id"])
    hashes = json.loads(row["hashes"] or "{}")
    if not hashes:
        raise ValueError("Episode has no validated artifact hashes")
    for relative, expected in hashes.items():
        if digest(local_file(folder, relative)) != expected:
            raise ValueError(f"Validated artifact changed: {relative}")
    return json.loads((folder / "episode.json").read_text())


def sync_archive(c, conn, only_id=None):
    if not c.get("supabase_archive", {}).get("enabled", False):
        return
    import supabase_archive
    # Share the publisher lock at call sites so older snapshots cannot overwrite
    # newer publishing state. Receipts are written only after remote success.
    supabase_archive.sync_queue(ROOT, c["supabase_archive"], conn, unchanged, local_file, only_id)


def generation_preflight(c):
    if not shutil.which(c["opencode_binary"]):
        raise ValueError("OpenCode binary not found")
    for tool in ("ffmpeg", "ffprobe", "bun", "node", "npx"):
        if not shutil.which(tool):
            raise ValueError(f"Required tool missing from PATH: {tool}")
    for asset in c["character_assets"]:
        local_file(ROOT, asset)
    if not c["character_assets"]:
        raise ValueError("No character assets configured")
    from dotenv import dotenv_values
    key = os.environ.get("ELEVEN_LABS_KEY") or dotenv_values(ROOT / ".env").get("ELEVEN_LABS_KEY")
    if not key or not key.strip():
        raise ValueError("Set ELEVEN_LABS_KEY in the project .env")


def generation_command(c, episode_id):
    prompt = (f"Produce ONE complete Richard YouTube episode in output/{episode_id}/. "
              "Read the workspace .opencode/skills/richard-system-design/SKILL.md and its local "
              "animation and FFmpeg references; do not substitute global workflow skills. Read that folder's "
              "BRIEF.md and history.json first. Fulfil the brief, render and review the export, "
              "then write episode.json using the delivery schema. If blocked, write BLOCKED.md "
              "and stop. Do not publish, edit queue state, or launch more sessions.")
    command = [c["opencode_binary"], "run", "--agent", "richardSystemDesign", "--format", "json",
               "--dir", str(ROOT), "--title", f"Richard YouTube {episode_id}"]
    if c["model"]:
        command += ["--model", c["model"]]
    if c.get("variant"):
        command += ["--variant", c["variant"]]
    if (ROOT / "narration.json").exists():
        from voice_selection import snapshot, instruction
        snapshot(ROOT, episode_id)
        prompt += instruction(episode_id)
    return command + [prompt]  # No --continue / --session: new session each time.


def generate(c):
    if not c["generation_enabled"]:
        print("Generation disabled; set generation_enabled after supplying assets and voice access.")
        return
    with lock("generation") as acquired:
        if not acquired:
            print("A buffer worker is already running.")
            return
        generation_preflight(c)
        conn = db()
        # A killed parent can leave its child running. Do not duplicate that job automatically.
        if conn.execute("SELECT 1 FROM episodes WHERE status='generating'").fetchone():
            raise ValueError("Unfinished generating episode: inspect its log/process; validate or fail it before retrying")
        for _ in range(c["max_generations_per_run"]):
            status_filter = "('ready')" if c.get("auto_admit", True) else "('ready', 'draft')"
            count = conn.execute(f"SELECT count(*) FROM episodes WHERE status IN {status_filter}").fetchone()[0]
            if count >= c["buffer_target"]:
                print(f"Buffer full: {count} available.")
                break
            episode_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
            folder = episode_dir(episode_id)
            folder.mkdir(parents=True)
            history = [dict(r) for r in conn.execute(
                "SELECT id, topic_key, title, status FROM episodes ORDER BY created_at")]
            dump(folder / "history.json", history)
            seeds = json.loads((ROOT / "topics.json").read_text())
            brief = ("---\nworkflow: richard-system-design\nflow: automation\nstoryboard: no\nmode: autonomous\n---\n\n"
                     "# Richard YouTube commissioned episode\n\n"
                     "Create one original system-design or DevOps explainer. Choose a distinct focused "
                     "question after checking history.json.\n\n"
                     "First inspect https://www.youtube.com/@Fireship/videos for recent topics, "
                     "then independently search current tech trends and primary sources. Follow "
                     "the workspace references/fireship-topic-research.md, save topic-research.md, "
                     "and choose an original Richard explanation after deduplicating history.\n\n"
                     f"Language: {c['language']}. Audience: beginner-to-intermediate developers.\n"
                     "Destination: YouTube, 1920×1080 landscape 16:9, 30fps, 180–480 seconds.\n"
                     "Use the local richard-system-design skill's light palette, supplied Richard artwork, "
                     "the owner-selected narration preset, causal animations, research and QA contract.\n"
                     "The owner commissions autonomous production and explicitly requests the rendered video, "
                     "not only a preview. Render after checks; no intermediate interview is needed. "
                     "Perform actual checks and stop honestly if a required capability is missing.\n"
                     "Output: editable composition, video.mp4, thumbnail.png, sources, captions, audio, "
                     "QA evidence and episode.json. No YouTube upload from this session.\n\n"
                     f"Character asset paths (project-relative): {json.dumps(c['character_assets'])}\n\n"
                     "Topic ideas (choose unused, or research another focused question):\n"
                     + "\n".join(f"- {s}" for s in seeds) + "\n")
            (folder / "BRIEF.md").write_text(brief)
            with conn:
                conn.execute("INSERT INTO episodes(id,status,created_at,updated_at) VALUES(?,?,?,?)",
                             (episode_id, "generating", utcnow(), utcnow()))
            try:
                with (folder / "session.jsonl").open("w") as log:
                    import session_tracking
                    proc = session_tracking.launch(ROOT, episode_id, generation_command(c, episode_id), log)
                    dump(folder / "worker.json", {"pid": proc.pid, "started_at": utcnow()})
                    try:
                        code = proc.wait(timeout=c["generation_timeout_seconds"])
                        proc.session_monitor.join(timeout=5)
                    except BaseException:
                        os.killpg(proc.pid, signal.SIGTERM)
                        try:
                            proc.wait(timeout=15)
                        except subprocess.TimeoutExpired:
                            os.killpg(proc.pid, signal.SIGKILL)
                            proc.wait()
                        raise
                if code:
                    raise ValueError(f"OpenCode exited {code}; inspect session.jsonl")
                if c.get("auto_admit", True):
                    try:
                        admit(conn, episode_id)
                        print(f"Ready: {episode_id}")
                    except Exception as val_exc:
                        if (folder / "video.mp4").is_file():
                            title, topic_key = None, None
                            try:
                                manifest = json.loads((folder / "episode.json").read_text())
                                title = manifest.get("title")
                                topic_key = manifest.get("topic_key")
                            except Exception:
                                pass
                            update(conn, episode_id, status="draft", title=title, topic_key=topic_key, error=f"Review draft: {val_exc}")
                            print(f"Draft: {episode_id} (review draft pending); ready for review.")
                        else:
                            raise
                else:
                    if (folder / "video.mp4").is_file():
                        title, topic_key = None, None
                        try:
                            manifest = json.loads((folder / "episode.json").read_text())
                            title = manifest.get("title")
                            topic_key = manifest.get("topic_key")
                        except Exception:
                            pass
                        update(conn, episode_id, status="draft", title=title, topic_key=topic_key, error=None)
                        print(f"Draft: {episode_id} generated successfully; waiting for review in dashboard.")
                    else:
                        update(conn, episode_id, status="failed", error="No video produced")
                        raise ValueError("No video produced")
            except Exception as exc:
                update(conn, episode_id, status="failed", error=f"{type(exc).__name__}: production/validation failed; inspect artifacts")
                print(f"Failed: {episode_id} ({type(exc).__name__}); inspect its artifacts.", file=sys.stderr)
                raise
            # Archive failures must not turn a valid episode into a failed render.
            with lock("publisher") as acquired:
                if acquired:
                    sync_archive(c, conn, episode_id)


def credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    path = ROOT / "secrets/youtube-token.json"
    # Preserve an existing token's grants. youtube is a valid broader scope
    # for the metadata/thumbnail operations; do not request new grants on refresh.
    creds = Credentials.from_authorized_user_file(str(path))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(creds)
    broad = "https://www.googleapis.com/auth/youtube"
    if not creds.valid or not (creds.has_scopes(SCOPES) or creds.has_scopes([broad])):
        raise ValueError("Run auth to grant the required YouTube scopes")
    return creds


def save_token(creds):
    directory = ROOT / "secrets"
    directory.mkdir(mode=0o700, exist_ok=True)
    directory.chmod(0o700)
    path = directory / "youtube-token.json"
    # Open with restricted permissions before writing secret contents.
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(creds.to_json())


def youtube(c, creds=None):
    from googleapiclient.discovery import build
    api = build("youtube", "v3", credentials=creds or credentials(), cache_discovery=False)
    channels = api.channels().list(part="id,snippet", mine=True).execute()["items"]
    if not c["channel_id"] or c["channel_id"] not in [ch["id"] for ch in channels]:
        raise ValueError("Authenticated channel does not match pipeline.json channel_id")
    return api


def auth(c):
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    flow = InstalledAppFlow.from_client_secrets_file(str(ROOT / "secrets/client_secret.json"), SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    api = build("youtube", "v3", credentials=creds, cache_discovery=False)
    channels = api.channels().list(part="id,snippet", mine=True).execute()["items"]
    ids = [ch["id"] for ch in channels]
    if c["channel_id"] and c["channel_id"] not in ids:
        raise ValueError("Wrong channel selected; token was not saved")
    save_token(creds)
    print("OAuth saved locally. Set channel_id in pipeline.json to the intended channel:")
    for channel in channels:
        print(f"  {channel['id']} — {channel['snippet']['title']}")


def due_slot(c, now=None):
    now = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(c["timezone"]))
    due = []
    for day in (now.date() - timedelta(days=1), now.date()):
        for clock in c["publish_times"]:
            hour, minute = map(int, clock.split(":"))
            slot = datetime(day.year, day.month, day.day, hour, minute, tzinfo=now.tzinfo)
            elapsed = (now.astimezone(timezone.utc) - slot.astimezone(timezone.utc)).total_seconds()
            if 0 <= elapsed < c["slot_grace_minutes"] * 60:
                due.append(slot)
    return max(due).isoformat() if due else None


def sanitize_youtube_text(text):
    if not text:
        return ""
    # YouTube API returns 400 invalidDescription or invalidTitle if < or > are present.
    text = re.sub(r'<(?=\d)', 'under ', str(text))
    text = re.sub(r'>(?=\d)', 'over ', text)
    text = text.replace('<', '').replace('>', '')
    return text


def format_exception(exc):
    try:
        from googleapiclient.errors import HttpError
        if isinstance(exc, HttpError):
            reason = getattr(exc, "reason", None)
            try:
                content = json.loads(exc.content.decode("utf-8"))
                msg = content.get("error", {}).get("message")
                errors = content.get("error", {}).get("errors", [])
                err_reasons = [f"{e.get('reason')}: {e.get('message')}" for e in errors if e.get("message")]
                detail = "; ".join(err_reasons) if err_reasons else (msg or reason)
                return f"({exc.resp.status}): {detail}"
            except Exception:
                return f"({exc.resp.status}): {reason or 'HTTP error'}"
    except ImportError:
        pass
    if isinstance(exc, (ValueError, FileNotFoundError)):
        return str(exc)
    return "Operation failed; inspect local artifacts or provider dashboard."


def assert_video_owner(api, video_id, c):
    items = api.videos().list(part="snippet,status", id=video_id).execute().get("items", [])
    if not items or items[0]["snippet"]["channelId"] != c["channel_id"]:
        raise ValueError("Video does not belong to the configured channel")
    return items[0]


def finish_publication(api, conn, row, c):
    from googleapiclient.http import MediaFileUpload
    data = unchanged(row)
    video_id = row["youtube_id"]
    info = assert_video_owner(api, video_id, c)
    if info["status"].get("uploadStatus") in ("rejected", "failed", "deleted"):
        update(conn, row["id"], status="blocked", error="YouTube rejected/failed this upload; inspect Studio")
        return
    folder = episode_dir(row["id"])
    if c.get("upload_thumbnails", False):
        try:
            api.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(
                str(local_file(folder, data["thumbnail"])))).execute()
        except Exception as thumb_exc:
            from googleapiclient.errors import HttpError
            if isinstance(thumb_exc, HttpError) and thumb_exc.resp.status == 403:
                print("Warning: Custom thumbnail upload returned 403 (channel requires phone verification in YouTube Studio for custom thumbnails). Continuing publication with default thumbnail.")
            else:
                raise
    if c.get("playlist_id"):
        # Query by videoId to make retries idempotent, including an uncertain
        # playlist insert result. Never create/rename a supplied playlist.
        present = api.playlistItems().list(part="id", playlistId=c["playlist_id"],
                                          videoId=video_id, maxResults=1).execute().get("items", [])
        if not present:
            api.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": c["playlist_id"], "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
    # Retrying updates on a known video ID is idempotent; inserting again is not.
    api.videos().update(part="status", body={"id": video_id, "status": {
        "privacyStatus": "public", "selfDeclaredMadeForKids": c["made_for_kids"],
        "containsSyntheticMedia": c["contains_synthetic_media"]}}).execute()
    info = assert_video_owner(api, video_id, c)
    if info["status"].get("privacyStatus") != "public":
        update(conn, row["id"], status="blocked", error="YouTube did not allow public visibility; inspect API project restrictions")
        return
    update(conn, row["id"], status="published", error=None)
    sync_archive(c, conn, row["id"])
    print(f"Published: https://www.youtube.com/watch?v={video_id}")


def publish(c, episode_id=None, force_now=False):
    # The existing five-minute cron poll also retries archival/status sync,
    # even while new publication is disabled or outside a publishing window.
    with lock("publisher") as acquired:
        if not acquired:
            if force_now: raise ValueError("Publisher already running")
            return
        sync_archive(c, db())
    if not c["publishing_enabled"] and not force_now:
        print("Publishing disabled; complete OAuth and channel setup before enabling.")
        return
    slot = None
    if not force_now:
        slot = due_slot(c)
        if not slot:
            print("Outside publishing window; no catch-up upload.")
            return
    with lock("publisher") as acquired:
        if not acquired:
            if force_now: raise ValueError("Publisher already running")
            print("Publisher already running.")
            return
        conn = db()
        if episode_id:
            row = conn.execute("SELECT * FROM episodes WHERE id=?", (episode_id,)).fetchone()
            if not row: raise ValueError(f"Episode {episode_id} not found")
            if row["status"] == "published":
                print(f"Episode {episode_id} is already published: https://www.youtube.com/watch?v={row['youtube_id']}")
                return
            if row["status"] == "draft":
                admit(conn, episode_id)
                row = conn.execute("SELECT * FROM episodes WHERE id=?", (episode_id,)).fetchone()
            if row["status"] not in ("ready", "uploading", "uploaded", "blocked"):
                raise ValueError(f"Episode {episode_id} cannot be published; status is {row['status']}")
            slot = row["slot"] or f"manual-{utcnow()}"
        elif slot:
            row = conn.execute("SELECT * FROM episodes WHERE slot=?", (slot,)).fetchone()
            if row and row["status"] in ("published", "blocked", "uploading"):
                print(f"Slot already assigned: {row['id']} ({row['status']}).")
                return
            if not row:
                if conn.execute("SELECT 1 FROM episodes WHERE status IN ('uploading','uploaded','blocked')").fetchone():
                    raise ValueError("Resolve the previous upload before assigning another publishing slot")
                row = conn.execute("SELECT * FROM episodes WHERE status='ready' ORDER BY created_at LIMIT 1").fetchone()
        else:
            row = conn.execute("SELECT * FROM episodes WHERE status='ready' ORDER BY created_at LIMIT 1").fetchone()
            if not row:
                print("No ready video to publish now.")
                return
            slot = row["slot"] or f"manual-{utcnow()}"

        if not row:
            print("No ready video; slot remains open until its grace window ends.")
            return

        if conn.execute("SELECT 1 FROM episodes WHERE status IN ('uploading','uploaded','blocked') AND id != ?", (row["id"],)).fetchone():
            raise ValueError("Resolve the previous upload before assigning another publishing slot")

        data = unchanged(row)
        sync_archive(c, conn, row["id"])
        api = youtube(c)  # Authenticate before reserving a slot or attempting an insert.
        if (row["status"] == "uploaded" or (row["status"] == "blocked" and row["youtube_id"])):
            finish_publication(api, conn, row, c)
            return
        update(conn, row["id"], slot=slot, status="uploading", error=None)
        # Persist uploading BEFORE the network call. Any uncertain result stays here.
        from googleapiclient.http import MediaFileUpload
        marker = f"\n\nEpisode reference: {row['id']}"
        description = data["description"]
        if len((description + marker).encode()) <= 5000:
            description += marker
        clean_title = sanitize_youtube_text(data["title"])[:100]
        clean_description = sanitize_youtube_text(description)
        clean_tags = [sanitize_youtube_text(t) for t in data.get("tags", [])]
        request = api.videos().insert(part="snippet,status", body={
            "snippet": {"title": clean_title, "description": clean_description,
                        "tags": clean_tags, "categoryId": c["category_id"],
                        "defaultLanguage": c["language"]},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": c["made_for_kids"],
                       "containsSyntheticMedia": c["contains_synthetic_media"]}},
            media_body=MediaFileUpload(str(local_file(episode_dir(row["id"]), data["video"])),
                                       mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True))
        try:
            response = None
            while response is None:
                _, response = request.next_chunk(num_retries=2)
            video_id = response["id"]
            update(conn, row["id"], status="uploaded", youtube_id=video_id, error=None)
            row = conn.execute("SELECT * FROM episodes WHERE id=?", (row["id"],)).fetchone()
            finish_publication(api, conn, row, c)
        except Exception as exc:
            err_msg = format_exception(exc)
            update(conn, row["id"], error=err_msg)
            raise


def reconcile(c, episode_id, video_id):
    with lock("publisher") as acquired:
        if not acquired:
            raise ValueError("Publisher is running")
        conn = db()
        row = conn.execute("SELECT * FROM episodes WHERE id=?", (episode_id,)).fetchone()
        if not row or row["status"] not in ("uploading", "uploaded", "blocked"):
            raise ValueError("Episode is not awaiting upload reconciliation")
        data = unchanged(row)
        api = youtube(c)
        info = assert_video_owner(api, video_id, c)
        if info["snippet"]["title"] != data["title"]:
            raise ValueError("Reconciliation video title differs from episode title")
        status = "published" if info["status"].get("privacyStatus") == "public" else "uploaded"
        update(conn, episode_id, youtube_id=video_id, status=status, error=None)
        print(f"Reconciled {episode_id} to {video_id} ({status}); no new upload created.")


def retry_finish(c, episode_id):
    if not c["publishing_enabled"]:
        raise ValueError("Publishing is disabled")
    with lock("publisher") as acquired:
        if not acquired:
            raise ValueError("Publisher is running")
        conn = db()
        row = conn.execute("SELECT * FROM episodes WHERE id=?", (episode_id,)).fetchone()
        if not row or row["status"] not in ("uploaded", "blocked") or not row["youtube_id"]:
            raise ValueError("Episode needs a known YouTube ID before retry-finish")
        finish_publication(youtube(c), conn, row, c)


def cron_block():
    python = ROOT / ".venv/bin/python"
    if not python.is_file():
        raise ValueError("Create .venv and install requirements first")
    command = shlex.join([str(python), str(ROOT / "scripts/pipeline.py")])
    logdir = ROOT / "state"
    logdir.mkdir(exist_ok=True)
    path = os.environ.get("PATH", "/usr/bin:/bin")
    prefix = f"env PATH={shlex.quote(path)} "
    # Cron treats percent specially even inside shell quotes.
    gen = (prefix + command + " buffer >> " + shlex.quote(str(logdir / "buffer.log")) + " 2>&1").replace("%", "\\%")
    pub = (prefix + command + " publish >> " + shlex.quote(str(logdir / "publish.log")) + " 2>&1").replace("%", "\\%")
    return "\n".join(["# BEGIN richard-youtube", f"0 * * * * {gen}", f"*/5 * * * * {pub}",
                      "# END richard-youtube"])


def install_cron():
    block = cron_block()
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode and "no crontab" not in result.stderr.lower():
        raise ValueError("Cannot inspect existing crontab; it was not modified")
    old = result.stdout if not result.returncode else ""
    if old.count("# BEGIN richard-youtube") != old.count("# END richard-youtube"):
        raise ValueError("Unbalanced existing cron markers; inspect crontab manually")
    clean = re.sub(r"(?ms)^# BEGIN richard-youtube\n.*?^# END richard-youtube\n?", "", old)
    new = clean.rstrip() + "\n\n" + block + "\n"
    if old:
        (ROOT / "state/crontab-before-install.txt").write_text(old)
    subprocess.run(["crontab", "-"], input=new, text=True, check=True)
    print("Installed hourly buffer and five-minute publisher polling; pipeline.json controls activation and local-time slots.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "doctor", "auth", "buffer", "sync", "cron", "install-cron"):
        commands.add_parser(name)
    pub_parser = commands.add_parser("publish")
    pub_parser.add_argument("episode_id", nargs="?", default=None)
    pub_parser.add_argument("--now", action="store_true", default=False)
    pub_now_parser = commands.add_parser("publish-now")
    pub_now_parser.add_argument("episode_id", nargs="?", default=None)
    for name in ("validate", "fail", "reject", "retry-finish"):
        sub = commands.add_parser(name)
        sub.add_argument("episode_id")
        if name in ("fail", "reject"):
            sub.add_argument("reason", nargs="?", default=None)
    sub = commands.add_parser("reconcile")
    sub.add_argument("episode_id")
    sub.add_argument("video_id")
    args = parser.parse_args()
    c = config()
    if args.command == "status":
        rows = [dict(r) for r in db().execute(
            "SELECT id,status,title,youtube_id,slot,error FROM episodes ORDER BY created_at")]
        print(json.dumps({"generation_enabled": c["generation_enabled"],
                          "publishing_enabled": c["publishing_enabled"], "timezone": c["timezone"],
                          "publish_times": c["publish_times"], "episodes": rows}, indent=2))
    elif args.command == "doctor":
        issues = []
        try:
            generation_preflight(c)
        except Exception as exc:
            issues.append(str(exc))
        for path in ("secrets/client_secret.json", "secrets/youtube-token.json"):
            if not (ROOT / path).is_file():
                issues.append(f"Missing {path}")
        if not c["channel_id"]:
            issues.append("Set channel_id after OAuth")
        print(json.dumps({"ready_for_local_setup": not issues, "issues": issues,
                          "note": "Local checks only; provider access and render QA are verified during production."}, indent=2))
        return 1 if issues else 0
    elif args.command == "auth":
        auth(c)
    elif args.command == "buffer":
        generate(c)
    elif args.command == "publish":
        publish(c, episode_id=args.episode_id, force_now=args.now)
    elif args.command == "publish-now":
        publish(c, episode_id=args.episode_id, force_now=True)
    elif args.command == "sync":
        with lock("publisher") as acquired:
            if not acquired:
                raise ValueError("Publisher/sync already running")
            sync_archive(c, db())
    elif args.command == "cron":
        print(cron_block())
    elif args.command == "install-cron":
        install_cron()
    elif args.command in ("validate", "fail", "reject"):
        with lock("generation") as acquired:
            if not acquired:
                raise ValueError("Generation worker is running")
            with lock("publisher") as pub_acquired:
                if not pub_acquired:
                    raise ValueError("Publisher is running")
                conn = db()
                if args.command == "validate":
                    admit(conn, args.episode_id)
                else:
                    row = conn.execute("SELECT * FROM episodes WHERE id=?", (args.episode_id,)).fetchone()
                    if not row or (row["slot"] and row["status"] not in ("uploading", "blocked", "failed")) or row["status"] not in ("generating", "failed", "draft", "ready", "uploading", "blocked"):
                        raise ValueError("Only unassigned production jobs can be rejected; reconcile uploads instead")
                    default_reason = "Rejected by operator" if args.command == "reject" else "Manually failed by operator"
                    reason = getattr(args, "reason", None) or default_reason
                    update(conn, args.episode_id, status="failed", slot=None, error=reason)
    elif args.command == "reconcile":
        reconcile(c, args.episode_id, args.video_id)
    elif args.command == "retry-finish":
        retry_finish(c, args.episode_id)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Provider exceptions can contain request details; do not dump headers or tokens.
        message = format_exception(exc)
        print(f"{type(exc).__name__}: {message}", file=sys.stderr)
        sys.exit(1)
