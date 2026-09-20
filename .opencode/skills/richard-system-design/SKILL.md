---
name: richard-system-design
description: Produce Richard's 3–8 minute 16:9 YouTube system-design explainers with research, narration-synced causal animations, original character assets, thumbnails, and verified delivery manifests. Use for richardSystemDesign and scheduled YouTube buffer production.
---

# Richard — YouTube system design

## Contract

Read `references/production-lessons.md` before planning and before full rendering.
Read `references/teaching-and-motion.md`, `references/launch-video-motion.md`
and `references/delivery.md` first. Read `references/ffmpeg-workflow.md` before
audio processing, frame capture, encoding or export QA. Use `references/launch-video-catalog.json`
to choose Pitch-derived techniques and locate inspected effect sources.
This skill adapts the reference at
`/Users/mukundmadhav/insta/.opencode/agents/richardSystemDesign.md` and its
system-design skill, inspected September 21, 2026. The useful teaching,
motion, provenance, voice and honest-QA principles have been extracted locally.
There is no runtime dependency on the Instagram workspace.
The launch-video extraction adds focus cameras, semantic object handoffs,
detail expansion, precision zooms, pending-to-confirmed transitions and metric
traces from the user's Pitch effects lab. Its local reference owns adaptation
guidance; the original Pitch preview/export workflow does not govern delivery.

**Workspace-first production (user direction):** This local skill and its
extracted references are the production authority. Do not replace them with
global HyperFrames creative workflows, install/refresh unrelated global skills,
or reopen a generic onboarding interview. HyperFrames is the HTML/timing
framework, Anime.js drives the animation, and FFmpeg handles audio and final
video encoding. Use installed CLI help or official API documentation for
specific technical questions. The local launch-video recipes govern motion.

| Item | Requirement |
| --- | --- |
| Destination | YouTube standard landscape video |
| Export | 1920×1080, square pixels, 16:9, 30fps; MP4, H.264/yuv420p, AAC, faststart |
| Duration | 180–480 seconds including intro/outro and audio tails |
| Subject | One focused technology/system-design question per episode |
| Language/audience | Configured language; beginner-to-intermediate developers |
| Presenter | Supplied Richard PNGs; preserve original identity and proportions |
| Palette | Ivory #F7F5EB / white; charcoal #202628; teal #23856D; amber #A66B12; red #C94343 |
| Runtime | HyperFrames with a local pinned Anime.js master |
| Narration | ElevenLabs Adam pNInz6obpgDQGcFmaJgB, unless configuration overrides |
| Thumbnail | Dedicated 1280×720 PNG/JPEG, less than 2MB, ≤6 big words |

## Production sequence

1. Read supplied BRIEF.md/history.json and the production lessons. Confirm the
   browser/runtime, narration operation and actual playback/listening review
   path before committing to full production. Pick a novel topic and descriptive
   lowercase hyphenated topic key. Use the suggested topic bank as ideas, not
   as claims or a finite limit on future episodes.
2. Research official documentation, engineering posts, standards and source
   repositories. Save URLs, access dates, versions/dates and claim mappings in
   sources.md. Distinguish documented behavior, dated architecture and a
   proposed teaching design. Label illustrative metrics; never invent scale.
3. Write script.md and narration.txt. Draft three honest hooks; choose the one
   the video actually answers. Trace a familiar action through a system;
   introduce a failure, recovery, cost and practical takeaway. A 3–8-minute
   video generally needs roughly 550–1500 words, but the measured audio decides
   timing. Choose length based on the lesson; no padding or rushed explanations.
4. Write STORYBOARD.md mapping every meaningful clause to subject, action,
   outcome, assets, source claims, narration trigger and result hold. Break
   chapters into 3–7-second single-action beats, allowing longer reading holds.
   Include short valid syntax when it helps explain the mechanism.
   Before locking motion choices, consult the launch-video catalog. Record each
   chosen recipe's source, target ownership, useful mechanism and chapter handoff.
   Treat this as a provisional plan; finalize all action/reading/transition
   windows from the aligned final audio in step 8. Select effects for meaning,
   not to meet a cut-rate or catalog-count target.
   Keep inspiration separate from the implemented mechanism. Each meaningful
   clause needs its named subject/action/result or a justified continued hold;
   a paragraph-level scene description is not a clause coverage audit.
5. Source all named logos and supporting objects, not just the hook mark.
   Use the supplied assets and official/appropriately licensed sources. Consult
   the local launch-video catalog before hand-building named visual treatments.
   Freeze assets locally and record license/provenance in
   assets/manifest.json. Inspect the original Richard artwork.
6. Follow this workspace's production sequence and extracted motion references.
   Build seek-safe HTML with one paused Anime.js master and declared 1920×1080
   canvas/timing. Use installed HyperFrames CLI tooling where applicable, and
   FFmpeg per the local reference. Keep version pins/lockfiles in the episode.
7. Verify ElevenLabs account voice/model access using ELEVEN_LABS_KEY from .env.
   Read project-root `narration.json` and `references/narration-delivery.md` for
   the owner's energetic, confident teaching preset. Use its resolved settings
   in the generation script rather than an older episode's hardcoded values.
   Never print the key or read it into conversation. Use an output-folder
   script via `bun --env-file=.env output/<id>/...` from the project root.
   Default model eleven_multilingual_v2, native speed 1.0, initial stability
   .30, similarity_boost .75, style .45, speaker boost enabled. Verify current
   documented support. Generate a short audition first; assess intelligibility.
   If voice lookup returns `missing_permissions` for `voices_read`, a supplied
   voice ID may still work for synthesis. Test that specific operation with the
   short cached audition; do not infer total credential failure or skip audition.
   Preserve the reference's natural-pitch 1.3× delivery by applying FFmpeg
   `atempo=1.3` exactly once to native audio. Never set native speed 1.3, pitch
   shift, or apply a second tempo adjustment in the renderer. Leave sufficient
   comprehension pauses for longer teaching. Cache by text/voice/model/settings;
   assemble native chapter chunks before processing. Record the speed chain.
8. Measure final audio and obtain real alignment using the provider's timestamp
   output or a forced aligner against the final audio. For native TTS character
   timestamps, apply the same single tempo transform to the timestamp map and
   verify synchronization against the processed master. Then
   save subtitles.srt and beats.json, then derive visual cues from those real
   timestamps. Never use estimated word times as verified alignment. Audio
   duration outside the range requires script revision. Render the final
   processed audio once at playback rate 1.0.
   Keep independent focal text stable for its actual reading window; entrances,
   blur and exits do not count as reading time. Use the extracted pacing
   heuristic for focal copy rather than imposing it on aligned subtitles.
   Resolve exact reveal/verb/arrival/result cues from aligned transcript ranges,
   not fixed offsets or percentages of scene duration. Keep caption groups
   inside semantic phrase and scene boundaries instead of grouping the entire
   script into blind five-word chunks.
9. Author a deterministic light landscape composition. Produce causal movement
   throughout, not a slideshow of captions and poses. Follow the teaching and
   launch-video motion references; port selected mechanisms onto the Anime.js
   master instead of assuming Pitch's fx/ShotKit/Motion helpers are installed.
   Before full-length capture, encode and inspect a representative short excerpt.
   Prove the chosen mechanism, safe zones, smallest-preview readability, correct
   transfer endpoints and one timeline owner per animated property.
10. Run applicable HyperFrames checks and render the timestamp-driven visual
    sequence. Use FFmpeg for the final H.264/AAC MP4 and technical QA as described
    in `references/ffmpeg-workflow.md`. Inspect
    the full exported video and listen to the full audio. Check every chapter,
    action start/mid/end, densest frame, transition, caption fit and final tail;
    compare direct/sequential/backward seeks. Preview at 640×360 and 320×180.
    Record evidence in qa/report.md and the delivery manifest. An unavailable
    review is NOT VERIFIED, and the job must remain blocked rather than ready.
11. Create an accurate thumbnail with Richard, one dominant subject and up to
    six words, legible at 320px. Save thumbnail.png and editable source. Write
    title, description with chapter timestamps, sources/credits and tags.
12. Write episode.json LAST, only after required QA passes, using the delivery
    schema. The scheduler independently probes the export and checks artifacts.

## Landscape composition

- Safe content region: x=96–1824, y=54–972 at 1920×1080.
- Focal demonstration: typically x=96–1370, y=80–790. Fill 70–90% of its stage.
- Richard: typically x=1420–1810, y=250–860; visible alpha silhouette 480–610px
  tall (never below 450px). For right-pointing art, move Richard left and put
  the demonstration right for that chapter. Point toward actual content.
- Captions: x=120–1800, y=870–972; 3–7 aligned words, maximum two lines, starting
  around 52–64px. Shorter cues are allowed at semantic/scene boundaries. Fit text
  by shortening cues, not clipping or tiny type. Check both container fit and
  container bounds inside the safe zone at all relevant animation states.
- Labels ~48–64px, hook ~76–96px. Code is 1–3 short readable lines replacing
  the focal demonstration, with adequate reading time.
- One focal action, Richard, one caption block. No persistent headers,
  progress pills, footers, decorative panels or competing diagrams.
- Avoid a repeated large scene heading as a fourth reading region. Put the
  hook headline in the caption region or use it temporarily as the focal subject.
- Use all supplied poses when appropriate; meaningful handoffs around 4–12s,
  with justified longer holds during code. Richard stays still during the
  mechanism. Record pose intervals and visible alpha bounds; do not mirror.

User-specified episode choices override defaults. A missing credential, artwork,
tool capability or factual source is a blocker to describe honestly, never a
reason to fabricate evidence or silently substitute a different presenter.

## Owner-selected audition preset takes precedence

Read project-root `narration.json` before synthesis. A dashboard-selected
preset overrides older numerical voice-settings and fixed-1.3 examples
in this skill. Use its `voice_settings` at native speed 1.0 and apply its
`post_tempo` exactly once with FFmpeg. Transform alignment timestamps by
that same ratio, not a hardcoded 1.3. Include the resolved preset in cache
keys. Keep each episode's audition and actual listening verification.

## Automatic buffer topic discovery

Before choosing every automatic buffer topic, read
`references/fireship-topic-research.md`. First inspect recent content at
https://www.youtube.com/@Fireship/videos, then independently search current
tech trends and primary sources. Deduplicate against history.json, choose
one original Richard teaching angle, and save topic-research.md before
scripting. Record actual access and evidence; never invent a live channel
check or trending status. Explicit owner topics remain authoritative.

## Mandatory full-export frame audit

After every full render, follow the workspace Richard skill reference
`references/full-video-frame-audit.md`. Run `scripts/frame_audit.py`
against the actual exported MP4 to extract one frame every 3 seconds
across the whole video plus the final frame. Inspect EVERY sheet/frame,
record timestamped defects, fix the source and rerender. Review moving
excerpts and every transition as well; still images cannot prove motion
quality or narration sync. Re-extract and inspect the corrected final
export before declaring QA passed. Never equate extraction success with
visual approval. Preserve honest draft status if review is unavailable.

## Netflix-derived production checks

Before building or repairing a video, read the workspace Richard skill
`references/netflix-production-lessons.md`. Separate static SVG layout
from motion wrappers, avoid repeated collection resets, preserve legible
text and real causal movement, validate generated markup, and synchronize
factual changes across narration/captions/visuals. Verify numerical examples
and review evidence rather than inheriting a previous report's PASS labels.
