# Episode handoff

All paths below are relative to the reserved `output/<episode-id>/` directory.
All referenced artifacts must be real, nonempty, and stay within that directory.
The scheduler validates the final file with ffprobe. Write `episode.json` last.
Before claiming completed QA, apply `production-lessons.md`. Evidence must name
the exact reviewed file/source hashes, actual tool/reviewer, and covered times.
Sampled seek and caption-container checks cannot stand in for full playback,
listening, semantic animation coverage, or native-size readability checks.

```json
{
  "topic_key": "cache-stampede-request-coalescing",
  "title": "Why Your Cache Can Crash Your Database",
  "description": "A focused explanation...\n\n00:00 The problem\n00:35 ...\n\nSources and credits: ...",
  "tags": ["system design", "caching", "distributed systems"],
  "video": "video.mp4",
  "thumbnail": "thumbnail.png",
  "artifacts": {
    "script": "script.md",
    "sources": "sources.md",
    "storyboard": "STORYBOARD.md",
    "composition": "index.html",
    "captions": "subtitles.srt",
    "audio": "audio/full.wav",
    "assets": "assets/manifest.json"
  },
  "qa": {
    "status": "passed",
    "report": "qa/report.md",
    "checks": {
      "facts": {"status": "passed", "evidence": "qa/facts.md"},
      "full_playback": {"status": "passed", "evidence": "qa/playback.md"},
      "full_listening": {"status": "passed", "evidence": "qa/listening.md"},
      "motion_and_sync": {"status": "passed", "evidence": "qa/motion-audit.json"},
      "seek_determinism": {"status": "passed", "evidence": "qa/seek.md"},
      "readability": {"status": "passed", "evidence": "qa/readability.md"},
      "thumbnail": {"status": "passed", "evidence": "qa/thumbnail.md"}
    }
  }
}
```

In automated scheduled production, each review record states what was inspected,
when, with which tool/reviewer, and the observed result:
- `facts`: verified against `sources.md` and documented engineering standards.
- `full_playback`: verified via `scripts/frame_audit.py` (3s contact sheets), FFmpeg decode scan, zero black frames, safe-zone compliance, presenter bounds, and preview checks.
- `full_listening`: verified via audition, single post_tempo=1.3, EBU R128 loudness (-18 to -14 LUFS, peak ≤ -1.0 dBFS), and 100% transcript character alignment.
- `motion_and_sync`: verified against beats.json clause triggers and Anime.js timeline.
- `seek_determinism`: verified via Playwright forward/backward bit-identical captures.
- `readability`: verified via Playwright 100% caption cue container and safe-zone fit.
- `thumbnail`: verified 1280×720 PNG under 2MB with ≤6 words.
When all automated checks pass with zero unresolved defects, submit the manifest with `qa.status: "passed"` and all checks `passed`. Only record `not_verified` and explain in BLOCKED.md if an actual technical failure or unresolved defect prevents verification.

Use a ≤100-character accurate title, ≤5000 UTF-8-byte description, and concise
tags totaling ≤450 encoded characters. Video must have an audio stream and
last 180–480 seconds. Thumbnail must be 1280×720 PNG/JPEG and under 2MB.
The description should contain useful chapters and required source credits.

### YouTube Metadata Constraints (Mandatory)
- **Zero Angle Brackets:** YouTube API strictly prohibits `<` and `>` characters in titles, descriptions, and tags (it interprets them as HTML tags / XSS risk and aborts with HTTP 400 `invalidDescription` or `invalidTitle`). Never write `<1ms`, `>100k`, etc. Always write 'under 1ms', 'less than 1ms', 'over 100k', or 'greater than 100k'.
- **Title:** 1–100 characters, no `<` or `>`.
- **Description:** 1–5000 UTF-8 bytes, no `<` or `>`. Must include structured chapters (`00:00 Introduction...`).
- **Tags:** Total encoded length ≤450 characters, no `<` or `>`.

subtitles.srt and thumbnail.png are delivered locally with the episode artifacts.
The automated publisher uploads the video, metadata, and playlist membership directly
to YouTube with public visibility, without attempting custom thumbnail API uploads
(avoiding 403 Forbidden errors when channel intermediate phone verification is pending;
custom thumbnails can be uploaded manually in YouTube Studio or enabled via upload_thumbnails: true).

The scheduler records hashes of the manifest and every handed-off artifact
before counting the episode as ready and checks them before upload. Keep
ready artifacts immutable. `validate <episode-id>` can readmit repaired failed
episodes; it cannot replace episodes that have entered upload/publishing.
