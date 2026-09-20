# Extracted teaching and animation guidance

Apply `production-lessons.md` alongside this guide. It records the Jev run's
specific failures and the evidence required to prevent them.

## Teaching

Open with a concrete 3–5-second knowledge gap. Begin answering by second five,
without a greeting. Show a familiar shop, lunchbox, waiting line or library
analogy, then explicitly map each relevant object to the real system. Explain
where the analogy fails. Define jargon immediately in short sentences.

Follow one request, upload, message, job or response. Explain what enters each
component, why the component exists, what it does and what leaves. Include a
failure/recovery and an honest tradeoff. Never imply that an interface guide
documents a company's private internal architecture.

Every meaningful spoken clause needs a matching noun/action/result on screen.
Nouns appear, verbs cause changes, outcomes visibly resolve. A caption change
or pose swap is not explanatory motion. Relevant reading holds are allowed
when documented. A coherent collection can show 4–8 cards with a single current
item dominant; otherwise use one object or two endpoints plus a moving token.

For syntax: intent → 1–3 valid lines → highlight explained parts → actual
effect → result hold. Keep identifiers and example data consistent. Verify
syntax with documentation and a local fixture when available; do not invent
successful execution. Keep stage directions out of narration.txt.

## Motion sources and ownership

Consult the official feature relevant to each chosen effect:

- Anime.js: https://animejs.com/documentation/ and https://github.com/juliangarnier/anime
- Motion: https://motion.dev/docs/animate, /docs/stagger, /docs/react-layout-animations
  and https://github.com/motiondivision/motion
- System Design Simulator:
  https://github.com/vijaygupta18/system-design-simulator/tree/a1bf2049de1f5d97dbe3a765b6658c56b5074f48

The reference inspected Anime.js 4.5.0. Verify a compatible version and pin it
locally. Use v4 createTimeline/add and millisecond positions, not v3 callable
anime() or GSAP-specific properties. Consult installed runtime documentation
for specific integration questions. Build one paused master (`autoplay: false`) and register it on
`window.__hfAnime = [master]`; HyperFrames owns time and media playback.
Animate clip inner wrappers, keeping framework lifecycle ownership intact.

Use Motion as a technique source: restrained spring settles, staggered builds,
shared-element continuity, selection handoff, submit→feedback, SVG draws and
fixed-position scripted scrolling. Prefer porting those techniques to Anime.js.
Record mode as `motion-inspired/animejs`, not as running Motion. Direct Motion
controls need their own explicit absolute-time bridge, isolated properties and
verified seeking; there is no assumed native `__hfMotion` registry.

Useful simulator families: directional edge packets, solid sync/dashed async
routes, node readiness, bottleneck emphasis, capacity fill, replica arrival,
branch routing, connection draws, finite progress/counts and scene handoffs.
Upstream files include src/components/canvas/edges/AnimatedEdge.tsx,
src/components/canvas/nodes/ComponentNode.tsx, src/components/Walkthrough.tsx
and public/traffic-sim.svg. Treat upstream timers/SMIL/React effects as source
ideas, not render-safe code. Read relevant actual source before adaptation.
Record URLs, commit/version, license, target ownership and spoken trigger.
Retain MIT notices with copied code; premium Motion+ examples are not assumed
to share the core library's license.

## Causal and deterministic behavior

Establish endpoints → draw route → send token → arrive → change destination
state → hold 0.5–1s → hand off. Usually only one 70–110px token is visible.
Use large travel distances suited to the landscape stage. Motion duration
illustrates causality, never a measured network latency without evidence.

Copy retains source; cache hit skips database; rejection stops; queue consumes
after enqueue; acknowledgment follows receipt; response is a separate reverse
trip. Replicas receive traffic only after readiness. Counters are illustrative
unless independently sourced. Arrival must precede success.

Precreate state, use explicit start/end values, finite repeats and fixed layout.
No free-running CSS transitions, loops, wall-clock timers, unseeded randomness,
runtime downloads, callback-only DOM creation or autonomous audio. Repeated
direct, forward, backward and fresh-browser seeks to T must match. Scene
boundaries must have no overlap, gaps, reset flashes or ghosted presenter poses.

Watch the actual exported action excerpts, not only screenshots. Audit every
spoken clause across opening, middle and ending, including named supporting
brands and result holds. Record files, timestamps, tools/reviewer and outcome.
If full audiovisual review is unavailable, record NOT VERIFIED, never PASS.
