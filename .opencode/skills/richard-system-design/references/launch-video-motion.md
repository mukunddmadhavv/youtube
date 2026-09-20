# Pitch launch-video → Richard system-design motion

Extracted September 21, 2026 from
`/Users/mukundmadhav/pitch/.pi/skills/launch-video/` and the effect implementations
that its catalog references under `/Users/mukundmadhav/pitch/effects/`.
Read this before choosing motion for a new episode. Use the companion
`launch-video-catalog.json` to select effects and locate inspected sources.

## What this extraction supplies

Reusable visual recipes, timing/continuity rules, system-design adaptations,
and exact source locations. The source skill indexes **443 effects / 32 families**.
Seven implementation studies are analyzed in the catalog, with six recommended
for regular use and one constrained code-highlight adaptation. Additional IDs
are discovery candidates, explicitly distinguished from inspected implementations.

The `pitch` command was unavailable on this host's PATH during extraction.
Sources and four frame strips were read directly from the local effects lab.
No Pitch source-command receipt was generated. No effect has been ported,
browser-seek tested or rendered as a Richard episode by this extraction alone.
The rules below are sufficient local planning guidance; actual implementation
ports require the relevant source and current runtime documentation.

## Direction: demonstrate a change, then give it time to land

Extracted from `authoring.md`, `continuity.md`, `pacing.md`, and the product,
feature, kinetic and 3D treatment references:

1. Start with a meaningful task: input → mechanism → visible result.
2. Pick the motion mechanism before locking the storyboard. Explain WHY it
   teaches the current clause; a catalog ID is provenance, not a quality score.
3. Each beat has a focal subject, essential visible copy, action, readable hold,
   and connection to the next beat. Count all visible reading tasks, including
   unchanged code, labels and result text.
4. Continuity can be causal or verbal: question→answer and failure→recovery can
   use a clean cut. A persistent object is useful only if it carries meaning.
5. A source object can become the next subject: a request envelope opens to its
   payload; a selected row expands into a record; a queue item becomes the
   worker's current job. Clear old labels, move/transform, settle, reveal detail.
6. Preserve the system's semantics. A visual handoff does not mean stored data
   was deleted. Keep the source for a copy; distinguish response from request.
7. Show useful states sequentially. A grid of six panels does not become a
   single lesson just because they arrived one by one.
8. Choose depth only when it explains structure: partitioned chunks, replica
   placement or nested components. Keep the camera still while reading labels.

### Reading time and narration

Use `max(1.5, 0.5 + essentialWords / 3)` seconds as a starting estimate for a
**settled independent focal phrase**. Six words start around 2.5 seconds of
reading time, plus entry/exit. Code, unfamiliar names and units may need longer.
This is a planning heuristic, not a minimum subtitle duration: Richard's aligned
3–7-word captions still follow speech. Remove redundant reading tasks instead
of forcing every short caption to remain for 2.5 seconds.

Blur, scrambling, offscreen motion and clipped exits do not count as reading.
Write the spoken story first; finalize choreography only after generating and
aligning the final processed voiceover. One continuous thought may span several
beats, and a result can have a brief silent hold. Keep the configured Adam voice
and existing single `atempo=1.3` chain; Pitch TTS tags/settings are provider-specific.

Pitch's measured ~0.75-second whole-frame turnovers and its pixel-change audit
thresholds came from short launch films. They are not targets for a 3–8-minute
systems lesson. Preserve useful comprehension holds. A pulse or shake added
solely to increase event count is not meaningful motion.

## Recommended recipes

### `pitch.focus-target` — overview → relevant component → next component

Source ID: `launch-primitives/focus-target-camera`, preset `focus-camera`.
Inspected source: `_lib/launch-primitives.js`, focus-camera branch.

- Source mechanism: fixed world coordinates, two eased camera legs, destination
  holds and a brief focus blur. Source legs are 0.5–2.1s and 2.55–4.3s in a
  five-second study. They are study times, not mandatory episode durations.
- Teach: move from browser context to the cache key, then to the returned object;
  or inspect the scheduler's chosen node after explaining its placement decision.
- Adapt: move the camera ONLY inside the focal demonstration stage. Richard and
  the caption region stay fixed. Finish the reframe before the request moves.
  Keep at most the currently needed endpoints and hide unrelated components.
- Source caveat: the study notes imply blur on both legs; source code only
  produces a blur envelope on the first leg. Design any additional blur explicitly.
- Verify: destination is centered in the demonstration viewport and sharp,
  all labels are stable during reading, and backward seeking restores overview.

### `pitch.request-path` — reveal the route, then follow the request

Source ID: `launch-primitives/reasoning-path-camera`, preset `reasoning-path`.

- Source mechanism: reveal a curved SVG connector, introduce nodes in sequence,
  and pan across the world. Cards represent Prompt / Best match / Book it.
- Teach: API→cache→database as sequential close-ups; enqueue→worker→result;
  a multi-hop request where the current hop stays dominant.
- Adapt: use the existing System Design Simulator packet grammar for actual
  transit. Draw the relevant route, hold the camera, send one visible token,
  show arrival, then advance. A line drawing is not itself a moving request.
- Source caveats: camera Y interpolates between endpoints rather than following
  the full curve. Dash length is hard-coded as 2100. Use actual path length
  measured ONCE at initialization; define target coordinates for each hop.
- Verify: destination corresponds to narration, return traffic is separate,
  and path/camera/token phases do not compete.

### `pitch.detail-expansion` — compact result becomes a readable detail

Source ID: `launch-primitives/result-card-focus-expansion`, preset `card-focus`.

- Source mechanism: a blurred 300×180 card expands toward 720×420 and moves
  toward center; details reveal separately.
- Teach: open a cached record, inspect an HTTP response, expand a message's
  payload, or reveal the matching indexed database row.
- Adapt: precompute compact and detailed geometry. Animate shell transforms
  with fixed final layout; use a separate text wrapper so letters are not
  stretched. Reveal detail after settling, then hold for reading. This avoids
  tween-time reflow and width/height animation in the HyperFrames composition.
- Source caveat: metadata says details appear after geometry settles, but the
  source reveals details from 2.1–3.2s while geometry runs until 3.3s. Correct
  that overlap in the port; do not claim the original already enforces it.
- Verify: one record identity, no duplicate old/new copy, no clipping or distorted
  text, and complete initial-state restoration on a backwards seek.

### `pitch.precision-zoom` — overview → inspect one control → return

Source ID: `launch/perceptual-scale-zoom`.

- Source mechanism: seek-driven zoom/pan, overview→roughly 2.5× detail→hold→return,
  a focus ring and a brief control emphasis. The source uses an `anim.interpolate`
  helper with `output: 'perceptual-scale'`; its interpolation implementation was
  not inspected, so this extraction makes no claim about its exact scale math.
- Teach: zoom into the idempotency key of a request or a token-bucket setting,
  then return to the demonstrated effect on the system.
- Adapt: choose world coordinates from the real control. Recompute the pan for
  Richard's viewport instead of copying source offsets −130/−20. Limit zoom to
  what preserves legibility and context. Use an emphasis only at the spoken cue.
- Remove the study's tiny sidebar, extra caption and repeated pulse. Use the
  episode's sole caption block and 1–3 readable code lines when appropriate.

### `pitch.pending-to-confirmed` — work in progress becomes a result

Source ID: `ui-elements/loading-spinner-success-animation`.

- Source mechanism: finite rotating arc, arc completion, success disc, drawn
  check, changed status and hold. The original is an eight-second payment demo
  with particles, button pulsing and GSAP/DrawSVG.
- Teach: upload receipt, committed transaction acknowledgment, completed queue
  work or a replica that has become ready.
- Adapt: keep finite pending motion, one state change and one check draw. Remove
  particle bursts, extra buttons, decorative bounce and the source payment claim.
  Use a failure/X outcome if work failed. Never signal success merely because
  the timer elapsed; its cue represents the narrated confirmation.
- Implement stroke progress using an actual SVG path/dash technique supported
  by the pinned Anime.js version; GSAP's `drawSVG` option is not an Anime option.

### `pitch.metric-trace` — trace one metric and reveal its consequence

Source ID: `charts/animated-line-chart-blue`.

- Source mechanism: line drawing, a dot/tooltip traveling along the path, an area
  reveal and a counter linked to path position; local plot coordinates map into
  a fixed SVG viewBox.
- Teach: an explicitly illustrative queue depth rising after arrivals exceed
  processing, or a documented latency curve with clear units and source.
- Adapt: one meaningful curve, legible units and one annotated event. Remove
  source subscription figures, '+42% YoY', extra KPI cards and generic glow.
  Do not smooth a measured/discrete series into unsupported values. Keep the
  trace through its reading hold instead of erasing it while explaining it.
- Source caveat: it reads plot.clientWidth/clientHeight inside onUpdate. Resolve
  geometry once and render every path/tooltip/counter state at absolute time.
  A callback that depends on previously visited frames is insufficient.

### `pitch.code-risk-resolution` — optional, constrained extraction

Source ID: `launch-primitives/code-scan-constellation`, preset `code-constellation`.

Retain the useful **highlight defect → explain fix → show verified result**
principle. The source scatters seven copies of code across a zooming world;
even green-bordered copies retain the same red 'exposed' mark. This is not an
actual demonstrated fix. For Richard, use ONE enlarged 1–3-line snippet, make
the real correction, then show its matching behavior. Reject the constellation
layout, tiny text and color-only claim of resolution. This branch's source was
read; its frame strip was not inspected.

## 16:9 and runtime adaptation

- The examined studies are 1280×720. 1.5× maps their full canvas to 1920×1080,
  but Richard reserves space for a presenter and captions, so **recompose**
  inside x=96–1370, y=80–790 rather than applying a global 1.5× scale blindly.
- Keep Richard's visible silhouette ≥450px, captions within y=870–972, and the
  light palette. A source's 16px label at 1.5× is still only 24px: rewrite and
  enlarge essential labels to the local 48–64px target.
- For a camera with transform-origin 0 0 and no rotation, a world point `(x,y)`
  can be centered in a demonstration viewport `(W,H)` using translate
  `(W/2 - zoom*x, H/2 - zoom*y)` followed by scale(zoom). Viewport-local
  coordinates, not the full video's center, determine this calculation.
- Pitch `_lib/motion.js` is a **local helper named Motion**, not proof of an
  imported `motiondivision/motion` package. Record `pitch-inspired/animejs`
  separately from existing `motion-inspired/animejs` recipes.
- `fx.register`, `fx.timeline`, `ShotKit`, `Motion.camera`, GSAP plugins and Pitch
  actor fields are source-runtime APIs. They are not available automatically
  in HyperFrames. Translate meaningful state/easing/geometry into the paused
  Anime.js master (`window.__hfAnime`); convert cue seconds to milliseconds once.
- For Canvas/Three.js, read the installed HyperFrames adapter and render from
  absolute time. Pin/bundle actual dependencies locally before capture.
- Use explicit pre/action/post states and finite repetitions; precreate DOM.
  No independent ticker, network fetch, unseeded randomness or callback-only
  state creation. Do not copy the lab's preview loop or whole runtime.
- For masked type, preserve accents/descenders with sufficient mask padding.
  The reference suggests `.16em .08em .24em` padding with compensating negative
  margins as a starting point. Verify actual bounds; never hide overflow as a
  substitute for caption fitting.

## Selection and evidence per episode

1. Choose only the techniques that explain the topic; there is no effect quota.
   Use the local catalog and `production-lessons.md` first. An installed registry
   can help with a specific primitive, but is not a replacement creative workflow.
2. Consult the catalog's inspected sources for candidates. If Pitch is available
   in the episode environment, `pitch effects show <id>` gives the study and
   `pitch effects show <id> --source` the implementation. Otherwise read the
   listed local source paths. Inspect selected strips before implementing.
3. Record in STORYBOARD.md: recipe ID, source effect ID/path, inspection method,
   inspiration recipe and actual implemented mechanism separately, implementation
   mode, changes, target/property ownership, spoken cue IDs,
   initial/action/result states, timing and actual verification outcome.
4. Treat a source-ID-driven signature treatment as one chapter-level sequence
   per episode. Repeat ordinary request transit when explanation needs it;
   do not force 443 different effects into a long lesson. If one sequence spans
   several clips, record it as one sequence with those clip IDs. This is Richard's
   long-form adaptation of Pitch's one-lab-ID-per-shot rule, not a claim to pass
   Pitch's own checker.
5. Keep source/license records when copying implementation code. No independent
   redistribution license for the local Pitch study collection was established
   in this extraction; do not label it MIT merely because another runtime is.
6. Do not fabricate `.studio/effect-sources.json`, `lab` receipts or verification.
   Direct local reads are valid provenance here but are not Pitch CLI receipts.
7. Audit that the port preserves the actual mechanism, not just its entrance.
   Test direct/sequential/backward seeks at initial/action midpoint/landing,
   verify 640×360 and 320×180 readability, then inspect actual exported motion
   and listen to narration. Frame strips establish sample appearance only.

The source launch-video workflow delivers a `shots.js` preview and leaves MP4
export to its user. Richard's commissioned workflow still delivers and verifies
the actual 180–480-second HyperFrames export for the YouTube pipeline.
