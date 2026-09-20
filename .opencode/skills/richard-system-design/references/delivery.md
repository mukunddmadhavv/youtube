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

This is a schema example, not pre-approved evidence. Each review record states
what was inspected, when, with which tool/reviewer, and the observed result.
Record unsupported reviews as `not_verified` and explain in BLOCKED.md instead
of submitting this manifest as passed. Machine validation verifies technical
properties and evidence presence; it cannot establish the truth of a review.

Use a ≤100-character accurate title, ≤5000 UTF-8-byte description, and concise
tags totaling ≤450 encoded characters. Video must have an audio stream and
last 180–480 seconds. Thumbnail must be 1280×720 PNG/JPEG and <2MB.
The description should contain useful chapters and required source credits.
subtitles.srt is delivered locally; the publisher currently uploads the video
and thumbnail, while YouTube can generate its own platform captions.

The scheduler records hashes of the manifest and every handed-off artifact
before counting the episode as ready and checks them before upload. Keep
ready artifacts immutable. `validate <episode-id>` can readmit repaired failed
episodes; it cannot replace episodes that have entered upload/publishing.
