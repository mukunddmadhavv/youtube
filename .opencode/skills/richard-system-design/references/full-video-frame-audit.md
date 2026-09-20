# Full-video frame audit and repair — mandatory

Owner direction after observing issues throughout the Netflix video: extract
**one frame every three seconds** from every completed export and inspect the
entire video, fixing defects before delivery. This is in addition to the
existing production-lessons, motion and listening checks.

## 1. Extract the actual exported video

From the workspace root:

```sh
.venv/bin/python scripts/frame_audit.py output/<id>/video.mp4
```

The tool uses FFmpeg to decode frames at 0, 3, 6, 9… seconds through the entire
video and an additional sample at the final frame. It creates full-resolution
PNGs, numbered contact sheets with timestamp labels, and manifest.json under:

`output/<id>/qa/frames-every-3s/<video-sha256>/`

Install the workspace requirements, including Pillow, if missing. Use the final
MP4, not HTML snapshots or only the first chapter. Each audit is bound to the
actual export hash. Tool success means EXTRACTED, never PASS.

## 2. Inspect every sampled frame

Read every contact sheet, then open full-resolution frames wherever something
is unclear. Inspect dense code, longest captions and crowded states at 640×360
and 320×180 without zoom as well. No skipping the middle or ending.

For each frame, record reviewed/pass or issue with actual observations:

- Correct scene, subject, logo and label for the spoken concept.
- Text legibility, intact lines/letters, no clipping, overflow or overlap.
- All text and captions within the workspace safe zones; no redundant heading
  competing with the demonstration and captions.
- Richard's full silhouette, adequate visible size, appropriate pose and pointing
  direction; no ghosted duplicate poses or unintended cropping.
- Correct source/destination, packet arrival and state; no wrong success checks,
  stale labels, impossible data flows or mixed states.
- Correct charts/units, illustrative-data labels, geometry matching numbers.
- No blank/black frame, missing asset, loading placeholder or reset flash.

Update each manifest frame's review_status and findings. Also write
`qa/frame-audit.md` summarizing which sheets were actually inspected and by what
tool/reviewer. If an image-viewing capability is unavailable, record NOT VERIFIED.
Never mark a frame reviewed from the fact that its PNG exists.

## 3. Review motion between the samples

Three-second stills can miss a broken 300ms transition. They cannot establish
that animations are smooth, correctly timed or comprehensible.

- For every distinct mechanism, inspect an exported short clip with audio at
  normal speed: initial state → action → arrival → result hold.
- Inspect every scene boundary at one frame before, on, and after the cut, plus
  transition midpoints. Look for gaps, duplicate scenes, flashes and pose ghosts.
- Compare direct/sequential/backward browser seeks at key event times, and
  verify that the actual encoded video shows the same intended states.
- Listen through the full video and check actions against the spoken trigger.
  Provider-aligned subtitles alone do not prove animation/voice synchronization.
- Record evidence in `qa/motion-audit.json` and `qa/report.md`. Use observed
  correctness criteria, not an unsupported claim that animations are “perfect.”

## 4. Fix, rerender, inspect again

Create `qa/defects.json` with defect ID, frame/timestamp range, observation,
source scene/element, planned fix, status, and verification evidence.
Classify the actual problem: layout, asset, factual/semantic, timing, motion,
caption, presenter or encoding. Fix source composition/cue data rather than
painting over captured frames. Reuse unaffected narration and assets.

First rerender the affected excerpt and inspect its action/transition and nearby
frames. After it passes, render the corrected full video and rerun the complete
three-second extraction. Review all new sheets for regressions; old findings
must point to the new export's evidence before being marked fixed. Recheck
changed audio alignment, subtitle timing, total duration and technical export
properties as applicable. Do not iterate paid TTS for a purely visual defect.

## 5. Completion and handoff

Deliver as ready only when sampled-frame review is complete, no known defects
remain unresolved, and required temporal/listening checks were actually done.
Summarize inspected frame count, time coverage, defects fixed, remaining issues,
and final video hash. Keep extracted frames, sheets and review records with the
episode. If any required review cannot be performed, return a labeled review
draft with that limitation and do not fabricate a passed publishing manifest.

The extractor is an evidence tool, not an automatic visual-quality classifier.
The existing pipeline does not independently infer visual correctness from it.
