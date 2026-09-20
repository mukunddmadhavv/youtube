# Production lessons — mandatory checks before the next episode

Derived from the Jev review draft (`output/jev-vs-llms/qa/report.md`), its
implementation, and the user's workspace-only correction. These rules prevent
specific observed mistakes; they do not retroactively certify that draft.
Read before planning and revisit before the first full-length render.

## 1. Use the commissioned workspace workflow

Read this workspace's `SKILL.md` and local references directly. Loading a global
creative workflow and only switching back after the user's correction was a
mistake. Do not install/update global skills as an episode setup step. Use local
rules for style, motion, voice, length and delivery; consult narrowly relevant
CLI help/API documentation for technical questions.

Inspect the actual local environment first. Verify the pinned browser can launch
and the installed Anime.js bundle loads before requesting the complete voiceover
or rendering thousands of frames. A dependency lockfile does not prove browser
availability. Prefer an existing compatible browser or an episode-scoped
`PLAYWRIGHT_BROWSERS_PATH` when installing one; avoid garbage-collecting another
project's shared browser cache as a side effect of this production.

## 2. Check narration capability with a short audition

An ElevenLabs `401 missing_permissions` for `voices_read` does not establish
that the key lacks speech-generation permission. Inspect the sanitized error
code and identify the specific missing permission. When the user supplied an
explicit voice ID, try one short cached TTS audition on that voice. Do not
repeatedly retry a denied listing endpoint or request broader credentials when
the required synthesis operation already works.

The Jev run went straight to a full take after voice lookup failed. Next time:
generate a 10–15-second hook plus explanation sample, apply the single 1.3×
tempo change, and listen for names, articulation, energy and comprehension.
Record the reviewer/tool and outcome. Check whether a full listening/temporal
review path is available now, not after the full encode. If unavailable, surface
the limitation early and label any subsequent local deliverable a review draft.
Do not pretend waveform, ASR or loudness checks constitute a listening review.

## 3. Align the visual verbs, not only the subtitles

The draft had real provider-aligned captions but actions placed at generic
offsets such as `sceneStart + 2400ms` and `sceneDuration * .58`. That is not
narration-synchronized choreography.

After the final audio is aligned, create `beats.json` entries for each meaningful
clause with:

- clause ID and transcript word/character range;
- named subject/asset and spoken trigger word or phrase;
- absolute reveal, action start, arrival, result, hold and handoff times;
- visible state before and after; source/destination identity when relevant;
- source claim, recipe inspiration, actual implemented mechanism and QA status.

Use scoped word indices to resolve repeated words, not a global first-text
match. Multiple clauses can share a justified continued action/result hold.
Every clause still needs a recorded visual explanation or meaningful hold.
Derive transfers, selections, code highlights and verdicts from these events.
Do not evenly distribute them across a paragraph because it is convenient.

Bound caption groups to semantic phrases and scene handoffs. The draft grouped
every five words across the whole transcript, sometimes mixing the end of one
idea with the next scene's words. Split at sentence/clause/scene boundaries,
then fit approximately 3–7 words; a shorter boundary cue is preferable to a
mixed-idea caption. Verify timing transformations against the final audio:
dividing provider timestamps by 1.3 is a mapping, not proof of perceptual sync.

## 4. A recipe name must match what actually moves

The draft labeled some scale/fade scenes `pitch.focus-target` or
`pitch.precision-zoom` despite having no focused camera handoff. Keep separate
fields for `inspiration_recipe` and `implemented_mechanism`.

- A focus-camera treatment moves a defined world point into a fixed viewport,
  lands sharply, and holds before the next causal action.
- Detail expansion preserves a selected object's identity and reveals detail
  after its geometry settles. A generic card entrance alone is not this recipe.
- Request-path motion visibly travels between the correct endpoints. A route
  draw or success check alone does not demonstrate a request.
- A fix changes the actual code/data and its outcome. A green border is not
  evidence of corrected behavior.

Implement the chosen mechanism or relabel the scene honestly and improve its
teaching. Do not use one generic server box for every entity when its shape
obscures the subject: a ticket, choice set, probability distribution, policy
check and human review should be visually distinguishable.

## 5. Preserve causality and avoid conflicting motion

The draft initially gave one packet two overlapping X-position tweens, and a
transfer stopped short of its destination. Assign one timeline owner per
element/property. For each mechanism, inspect departure, midpoint, arrival and
result; verify actual packet bounds against endpoint geometry.

Compute the route from authored boundaries or initialized SVG geometry. Record
why arrival means received, processed, committed or merely selected; these are
different states. Do not attach a success check automatically to every transfer.
Demonstrate the promised branch/recovery: an uncertainty scene needs an actual
review path, and a re-query claim needs its new context and follow-up event.

Avoid unexplained static stretches after a generic entrance. Split long
paragraphs into semantic beats and add relevant changes, rather than decorative
loops or arbitrary camera movement. Preserve deliberate reading/result holds.

## 6. Verify the local layout contract before full rendering

The draft retained a large heading on every scene alongside diagram labels and
captions, and some text used smaller sizes than the local target. Follow the
three-group rule: focal demonstration, Richard, one caption block. The hook
headline uses the caption region or temporarily serves as the focal subject;
do not add a persistent fourth reading region throughout the video.

Check all rendered text bounds against x=96–1824, y=54–972, including at
animation extrema. Caption containers must remain within y=870–972; the draft's
905–1000 container exceeded that lower bound even though its text fit inside.
Container fit and canvas safe-zone fit are different tests; perform both.

Inspect representative diagrams, code, charts, longest captions and all pose
layouts at native **640×360 and 320×180 without zooming**. An inspected large
contact sheet is not that check. Start essential labels/code at 48–64px and
captions at 52–64px; simplify/split before shrinking. Check full SVG text and
its painted bounds, not only HTML caption scrollWidth/scrollHeight.

Measure Richard's visible alpha height, keep it ≥450px, and record pose intervals.
Use pose changes at meaningful handoffs, not index modulo arithmetic. Left/right
placement follows the current demonstration, not arbitrary periodic swapping.

Every quantitative mark is a claim. Decorative bars labeled quality, latency
and cost suggested measured values in the draft and had to be removed. Use a
checklist for dimensions to evaluate; give a chart actual units and sourced or
clearly labeled example data. Numerical labels and bar geometry must agree:
zero means a zero-length bar, not a minimum visible filled sliver.

Inventory every named brand in the narration, including supporting mentions.
Source and inspect authentic assets or use truthful text identification; record
that choice rather than claiming whole-script brand-asset coverage without it.

## 7. Prove a representative excerpt before full-length capture

Encode a short excerpt that includes a camera/detail treatment, a directed
transfer, a caption change, a presenter handoff and readable code/chart content.
Review its actual motion and sound using the planned review path. This catches
timing, browser, text and encoding issues before a full multi-minute render.

Run installed HyperFrames lint/check on compositions intended for its runtime;
report concrete incompatibilities instead of silently skipping them. If using
the local skill's direct-browser/FFmpeg path, explicitly identify it and perform
equivalent browser checks: console/page errors, missing assets, timed visibility,
frame coverage, text bounds, color contrast, and fresh/direct/sequential/backward
seeks. Custom `__hfSeek` registration alone does not prove framework compatibility.

Sample each distinct mechanism and every scene seam, not just six arbitrary
timestamps. Use exact event times plus/minus a frame. A hard-cut seam must show
one active scene, with no blank frame, double presenter or reset flash.

## 8. Check the encoded file and report the real status

Follow `ffmpeg-workflow.md` for range conversion and encoding. The Jev JPEG
capture initially produced full-range `yuvj420p` and needed a second encode.
Validate a sample encode's decoded stream properties before the full run.

Save technical probe, decode, black-frame, loudness, subtitle-fit and seek
evidence against the exact source/artifact hashes. Once a scene changes, affected
proof must be rerun; old screenshot comparisons cannot certify new code.
Do not mutate the timeline while collecting layout data and assume a screenshot
still depicts the requested time. Assert the active scene/time at capture.

Technical success, frame strips and a contact sheet do not establish full
temporal comprehension or intelligible speech. Record full playback/listening
as passed only after actual review, with tool/reviewer, file and timestamps.
Complete the clause/asset coverage audit and actual small-preview inspection.

If those reviews are unavailable, deliver an honestly labeled draft with an
actionable report. Do not treat naming missing checks as finishing them, claim
all skill requirements passed, or admit/upload the draft as a finished episode.
Archive/publication state must retain the real review status through the
existing pipeline; do not fabricate passed evidence to enable scheduling.
