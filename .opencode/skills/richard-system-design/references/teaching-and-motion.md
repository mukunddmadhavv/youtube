# Extracted teaching and animation guidance

Apply `production-lessons.md` alongside this guide. It records the Jev run's
specific failures and the evidence required to prevent them.

## Teaching structure: 5–10s intro hook and child-to-advanced escalation

### First 5–10 seconds: engaging hook + explicit intro
Open immediately with high energy and no generic greeting:
- **0–4 seconds (The Hook):** Present an arresting mystery, catastrophic failure,
  shocking scale metric, or counterintuitive question (e.g., "Why did 10,000 servers
  crash when one user pressed Refresh?").
- **4–10 seconds (The Explicit Intro):** Directly tell the viewer what is going to
  be explained in this video and why they must watch (e.g., "In this video, we're
  breaking down how cache stampedes happen under the hood, and how Netflix and Discord
  prevent them using single-flight request coalescing.").
- Visually, the opening 5–10s must showcase the bold topic mark, kinetic title words,
  and Richard's enthusiastic presentation in the focal area before the deep dive begins.

### Progressive pedagogical escalation: child-friendly (ELI5) to advanced engineering
Structure the lesson in two clear, deliberate tiers:

1. **Tier 1: Explain it to a child (ELI5 intuition):**
   - Start by explaining the core concept so simply that a 6-to-8-year-old could
     instinctively grasp it.
   - Use vivid, tangible everyday analogies: a pizza kitchen, toy sorting bins,
     a school lunch line, a postal clerk, traffic lights, or Lego towers.
   - Use short, friendly sentences without acronyms or jargon. Connect what the
     viewer already knows in the physical world to how information moves.
2. **Tier 2: Systematic technical escalation:**
   - Smoothly bridge the child-simple analogy to professional engineering reality.
   - Explicitly map each analogy piece: the pizza chef becomes the worker thread pool;
     the order ticket becomes a distributed Kafka event; the counter shelf becomes
     an in-memory Redis cluster.
   - Dive into real architectural depth: network protocols (HTTP/2, gRPC, TCP),
     data structures (ring buffers, bloom filters, LSM trees), concurrency,
     cache invalidation, quorum consensus, failure modes, backpressure, and
     hard production tradeoffs.
   - Explain what enters each component, why it exists, what it does, what leaves,
     and where the real system can break down.

Every meaningful spoken clause needs a matching noun/action/result on screen.
Nouns appear, verbs cause changes, outcomes visibly resolve. A caption change
or pose swap is not explanatory motion. Relevant reading holds are allowed
when documented. A coherent collection can show 4–8 cards with a single current
item dominant; otherwise use one object or two endpoints plus a moving token.

For syntax: intent → 1–3 valid lines → highlight explained parts → actual
effect → result hold. Keep identifiers and example data consistent. Verify
syntax with documentation and a local fixture when available; do not invent
successful execution. Keep stage directions out of narration.txt.

## Creative animations and kinetic motion

Be creative and dynamic with visual motion throughout the entire video:

### Kinetic typography and spoken-word animations
- Animate words dynamically as they are spoken, rather than relying solely on static
  captions.
- **Word-by-word highlights:** As narration progresses, the currently spoken word or
  key technical term lights up with the topic's signature accent color, scales up
  subtly (e.g., 1.0 → 1.18 → 1.0), or receives an energetic glowing underline.
- **Punchy word reveals:** High-impact words (e.g., "CRASH", "10X FASTER", "LOCK",
  "TIMEOUT", "DEADLOCK") burst into the scene or pop onto screen in lockstep with the
  spoken audio cue.
- Ensure kinetic word effects remain within safe reading zones and settle cleanly
  so readability is never compromised.

### Pop-in and pop-out dynamics
- Bring elements into the scene with an elastic bounce or spring pop-in:
  `scale: [0, 1.15, 1.0]`, `opacity: [0, 1]` with a crisp ease-out-back or spring.
- When an entity is introduced (e.g., "Enter Redis", "The client sends a query",
  "A new worker spins up"), its card, cylinder, or badge pops in right on the
  trigger word.
- When an entity is dismissed, invalidated, expired, or replaced (e.g., "The cache
  expires", "The connection drops", "We discard the stale payload"), it pops out:
  a quick bounce `scale: [1.0, 1.1, 0]` or a smooth vanishing dissolve.
- Give UI elements, node badges, protocol envelopes, and metric cards distinct
  and satisfying entrance and exit choreography.

### Causal system and flow animations
- **Directional energetic pulses:** SVG dashed or glowing lines with traveling pulse
  tokens showing data flowing across network edges.
- **Status badges popping over nodes:** Dynamic pills (`200 OK`, `PENDING`, `504 TIMEOUT`,
  `QUORUM MET`) popping into place with color shifts.
- **Failure & recovery effects:** A subtle camera shudder or flashing red alert state
  when a bottleneck or crash occurs, followed by clean recovery transitions.
- **Card and container morphs:** Compact request badges smoothly expanding into detailed
  payload views upon arrival.

## Authentic web logos and thematic brand identity

### Fetching real web logos
- Always fetch and use authentic, high-resolution vector (SVG) or transparent PNG logos
  of the exact technology, company, database, or tool being discussed (e.g., Docker,
  Kubernetes, Redis, PostgreSQL, Netflix, AWS, Kafka, Cloudflare, Nginx).
- Fetch logos directly from verified web sources:
  - SimpleIcons (`cdn.jsdelivr.net/npm/simple-icons@v11/icons/<slug>.svg` or official repo)
  - Wikimedia Commons (official SVG brand assets)
  - Official GitHub repositories or developer documentation brand kits
- Store all fetched assets in `output/<id>/assets/` and record their exact source URL,
  license, and provenance in `assets/manifest.json`.
- Never use generic geometric colored blocks or unbranded text when a real brand logo exists.

### Topic-specific font style and brand colors
- Adapt the visual theme of the video to match the desired topic's authentic identity:
  - **Color palette:** Extract and use the topic's signature brand colors for stage accents,
    cards, badges, and kinetic word highlights (e.g., Netflix Red `#E50914`, Docker Blue
    `#2496ED`, Redis Red `#D82C20`, PostgreSQL Blue `#336791`, AWS Orange `#FF9900`,
    Stripe Blurple `#635BFF`, Kubernetes Blue `#326CE5`).
  - **Typography:** Select a font style that mirrors the topic's brand identity. Load
    matching Google Fonts (e.g., bold condensed display fonts like Bebas Neue for Netflix,
    crisp modern grotesque fonts like Inter or Roboto for cloud infrastructure, JetBrains
    Mono for code-centric tools, Space Grotesk for Web3).
  - Ensure high contrast: render on clean light ivory (`#F7F5EB`) or crisp white backgrounds
    with dark charcoal (`#202628`) body text so legibility is crystal-clear at 320px preview.

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
