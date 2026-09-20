# Netflix generation: root causes and prevention

Mandatory for future productions and revisions. Derived from Netflix episode
`manual-21dfa91755ae4fa6`, original frame defects N01–N10, revised animation.js,
build_animation_js.py and QA reports. This does not certify the repaired video.

## Observed failures → required prevention

| Failure | Prevention |
| --- | --- |
| Device screens escaped cards; codec/quality/recap cards collapsed together | Separate static SVG positioning from animated inner groups |
| Packets left routes; badges jumped to unexpected positions | Explicit coordinate systems, origins, endpoint bounds and property ownership |
| Text spilled across Richard and outside the canvas | Check all painted SVG/HTML text bounds at action extrema, not just captions |
| Repairs shrank essential text to 20–40px | Shorten labels and split scenes; preserve readable local font targets |
| Broken mechanisms were replaced by opacity reveals | Restore the actual operation, then prove movement/state change |
| Corrected on-screen claims disagreed with retained narration | Update sources, script, audio, alignment, captions and visuals together |
| Generated preview files were treated as reviewed previews | Separate extraction, measurement and actual viewing/listening evidence |

## 1. Separate SVG placement from motion

Use an outer group for static layout and an inner group for animation:

```html
<g transform="translate(480 225)">
  <g id="codec-card-motion">
    <rect x="0" y="0" width="300" height="180" rx="20" />
    <text x="150" y="100" text-anchor="middle">HEVC</text>
  </g>
</g>
```

Keep the outer translate static. Animate the inner visual offset, scale or
opacity with explicit initial/final values. Do not animate the same group's
x/y in a way that overrides its existing positioning. When moving an entire
illustration, move its wrapper and labels together; do not inadvertently change
a rect's x/y geometry while leaving the rest of the object behind.

Determine whether the pinned Anime.js API treats x/y/cx/cy/rotate as attributes
or CSS transforms for that target. Verify in a short rendered test rather than
assuming. A packet and its label should share one wrapper. Gauges require an
explicit local pivot. Compare initial, midpoint, arrival and backward-seek states.

Check actual easing support in the pinned runtime. Netflix's revised source
mixes newer and older easing-name conventions; do not copy them as verified
recipes. Use supported names/functions and inspect console errors and actual
movement rather than trusting a silent fallback.

## 2. Schedule one intended event once

The revised code applies some full collection animations inside a loop over
every narration clause. This can repeatedly reset all codec cards, ladder
items or recap pillars to opacity zero. Give events unique cue IDs and schedule
each once. For separate spoken items, reveal only the corresponding item, not
the whole collection on every clause.

Do not clamp an event to sceneDuration minus 400ms while ignoring its actual
duration: a 1.8-second transfer started there is cut off. Budget entry, action,
arrival, result and hold inside the scene. If the subject crosses a boundary,
author that handoff explicitly. Assert event ends and inspect seam frames.

## 3. Layout fixes must preserve readability and meaningful movement

The revised text helper defaults to 22/26/34px, while essential local labels
and code target roughly 48–64px. At a 320px preview width, 24px source text is
about 4px high. Containment is not readability.

Remove redundant card subtitles, badges, headings and numerical specs. Split
chunks, codec comparisons and bitrate ladders into sequential close-ups rather
than compressing them into one information-dense panel. Preserve Richard's
size and the single caption region. Never shrink everything to make an overflow
test pass. Reassess font size after any viewport or parent scale transform.

Measure actual painted text bounds, including SVG tspans and ancestor transforms.
Check safe zones, assigned stage/panel bounds, sibling overlaps and collisions
with Richard. Caption scrollWidth checks cover none of the other diagram text.
Inspect representative frames at native 640×360 and 320×180 without zooming.

Do not replace all broken movement with fades. Show the operation: splitting,
transit, arrival, buffer fill/drain, selection, or recovery. A ladder appearing
is not adaptive quality selection. A “buffer protected” check is not proof that
a download arrived before depletion. Restore causal events on the spoken cues,
then hold the readable result. Keep comparisons sequential and labels stable.

## 4. Correct facts in every representation

The repaired picture names a ProRes mezzanine master, while sampled captions
still say “uncompressed master.” ProRes is compressed; a mezzanine master is
not inherently uncompressed. A visual correction cannot leave the old spoken
claim in place. Propagate factual changes through the full chain:

`sources → script/narration → audio → word alignment → captions → visual cues → export`

Regenerate affected speech when wording must change, then realign and retime.
Reuse existing audio only for genuinely visual-only changes. Check actual spoken
and displayed numbers against the same example, not just a rewritten QA report.

Record units, assumptions and calculations for numerical examples:

- Decimal GB download time: `seconds = GB × 8 × 1000 / Mbps`.
  420 GB over 50 Mbps is 67,200 seconds, about 18.7 hours, ignoring overhead.
- Size from bitrate: `GB = Mbps × durationSeconds / (8 × 1000)`.
  880 Mbps for two hours is about 792 GB, not 420 GB. Calling both numbers
  “illustrative” does not make an inconsistent example correct.
- Distinguish GB/GiB, Mb/MB, encoded bitrate/network throughput, segment playback
  duration/download time, and network latency/buffer depth.

Avoid unsupported universal Netflix claims: zero stalls, fixed 480p startup,
fixed segment lengths, a universal buffer threshold, “typical” latency without
measurements, universal VMAF indistinguishability or unsourced annual savings.
“Typical” requires evidence; changing an exact number to a range is not proof.
Label illustrative parameters where the viewer sees and hears them. Source
historical algorithm behavior with its date instead of claiming it is the exact
current production implementation. Recheck thumbnail promises too: changing
video wording while leaving “ZERO BUFFERING” on the thumbnail is not a full fix.

## 5. Validate generated markup and its authoritative source

The repair identified an unclosed font-size quote that hid content. Prefer
structured DOM/SVG attributes or small tested helpers to arbitrary interpolated
attribute strings. Escape text, validate generated markup and assert expected
labels/elements exist in the actual DOM. Check code examples and their results.

When Python generates animation.js or HTML, repair the generator and generated
file together, or explicitly retire the generator. A later rebuild must not
restore old defects. Record the build command and final source hashes.

## 6. Evidence must match each claim

Follow full-video-frame-audit.md: extract every 3 seconds plus the last frame,
inspect all sheets and relevant original/phone-size frames, record findings,
repair and repeat against the new video hash. Inspect moving excerpts for each
distinct mechanism and all transitions as well.

Do not call still inspection “motion verification,” eight repeated seeks “all
transitions checked,” or preview generation “readability verified.” Each defect
needs its before frame/time, root cause, source change, final export hash,
after frame/time, verification method and actual outcome.

Use separate statuses for containment, phone-size readability, factual agreement,
semantic movement, full listening and full playback. A defect can pass layout
while still failing one of the other criteria. Per-frame manifest reviews,
defect records and qa/report.md must agree. Report templates must not assign
PASS from an empty overflow list or successful encode. Loudness measurements
are not an invented YouTube compliance range or proof that speech was heard.

Do not automatically mark all defects fixed. Final acceptance requires no known
unresolved defects and actual completion of required reviews. Unavailable review
remains NOT VERIFIED; a cleaner contact sheet is progress, not perfection.
