# Energetic, modulated, and expressive teaching voice

User direction: use ElevenLabs Alex (`S9UjcNYIwfBOtZiDnIQT`) with the `eleven_v3`
model and Eleven v3 emotional audio tags for dynamic voice modulation across all videos,
preventing monotonic delivery and keeping learners thoroughly engaged.
The project-root `narration.json` is the authoritative synthesis preset. Read it
before each audition or new narration take, rather than copying settings from
an older episode's script. Preserve the configured Alex voice unless overridden
explicitly by the owner. Dashboard selection takes precedence over legacy environment voice defaults.

## Delivery & Voice Modulation

Sound like an enthusiastic, expert systems mentor who brings complex engineering
concepts to life with dynamic vocal range:

- Project clearly, with natural pitch variation, varied pace, and crisp consonants.
- Eliminate monotonic delivery by actively modulating tone, inflection, and tempo across clauses.
- Emphasize the entity and action: “The **queue** keeps the job. The **worker**
  picks it up.” Make contrasts audible: “Received is not the same as committed.”
- Use short spoken sentences, concrete verbs, and occasional prediction questions.
- **First 5–10 seconds hook and intro**: Deliver with high curiosity and conviction:
  punch the hook in the first 0–4 seconds with tension or surprise (`[excited]`, `[gasp]`,
  `[urgent]`), then by second 5–10 explicitly tell them what is going to be explained
  (`[authoritative]`, `[confident]`: "In this video, we're breaking down how X works...").
- **Two-tier progressive teaching**:
  1. *Tier 1 (Child-level intuition / ELI5)*: Warm, conversational, friendly tone (`[warmly]`,
     `[cheerfully]`, `[chuckle]`) using relatable everyday analogies (pizza shop, lunch line,
     toy bins) with zero jargon.
  2. *Tier 2 (Technical & architectural depth)*: Elevate into an authoritative, sharp,
     in-depth delivery (`[authoritative]`, `[thoughtful]`, `[intrigued]`) as components,
     protocols, data structures, concurrency, failure modes, scale, and tradeoffs are unpacked.
- Emphasize pivotal action nouns and trigger words with crisp inflection so that kinetic
  spoken-word typography highlights and visual pop-in/pop-out animations land with punch.
- Slow down for new terms, code, and numerical claims. Use `[pauses]` after major takeaways
  so viewers can digest the insight and connect the narration to the visual animation.
- Keep warmth and authenticity without sustained shouting, fake hype, or sales delivery.

## Eleven v3 Audio Tags for Emotional Context and Prosody

Eleven v3 supports inline bracketed audio tags (e.g. `[excited]`, `[whispers]`, `[pauses]`)
that direct emotional nuance, prosody, pacing, and vocal texture moment to moment, as documented in
ElevenLabs Eleven v3 Audio Tags:

### Common tag categories:
- **Emotional states**: `[excited]`, `[curious]`, `[fascinated]`, `[calm]`, `[nervous]`,
  `[frustrated]`, `[sorrowful]`, `[proud]`, `[incredulous]`
- **Reactions & Vocal textures**: `[sigh]`, `[gasps]`, `[whispers]`, `[chuckle]`,
  `[light chuckle]`, `[gulps]`, `[laughs]`, `[clears throat]`
- **Cognitive beats & Pacing**: `[pauses]`, `[hesitates]`, `[thoughtful]`, `[stammers]`,
  `[resigned tone]`
- **Tone cues**: `[authoritative]`, `[cheerfully]`, `[warmly]`, `[playfully]`,
  `[urgently]`, `[flatly]`, `[deadpan]`, `[sarcastically]`

### Practical script examples:
- *Hook & Intro*: `[excited] Your primary database just crashed! [gasp] Does your entire business stop? [confident] In this video, we're breaking down how distributed consensus keeps your systems alive.`
- *ELI5 Analogy*: `[warmly] Think of it like a busy pizza kitchen. [chuckle] If the cook took orders directly from every customer, tickets would get lost in seconds. [cheerfully] Instead, the cashier puts every ticket in a neat stack.`
- *Architecture & Outages*: `[thoughtful] But what happens when the network splits? [pauses] [authoritative] Now, two nodes both believe they are the leader. That is split-brain.`

## Subtitle & Caption Rule: Strip Audio Tags

**Crucial Production Rule**:
- Audio tags in square brackets `[...]` are strictly performance instructions for the ElevenLabs
  synthesis model.
- **Audio tags must NEVER appear in on-screen captions or subtitles (`subtitles.srt`)**.
- When generating captions, visual beats, or transcript checks, sanitize text with
  `re.sub(r'\[.*?\]', '', text)` and normalize extra whitespace.
- On `with-timestamps` character alignments, bracketed tags produce zero or pause duration;
  visual highlighting and word pop-ins attach to the actual spoken words.

## Synthesis preset and limits

Authority preset: Alex (`S9UjcNYIwfBOtZiDnIQT`), model `eleven_v3`, stability 0.35,
similarity_boost 0.80, style 0.45, speaker boost enabled, native speed 1.0.
This balance gives Alex vibrant expressive range and inflection while maintaining clear,
articulate technical pronunciation.

The `direction` field in narration.json is an editorial instruction for the scriptwriter
and reviewer, **not** an API request field. Send only documented ElevenLabs API fields.
Do not prepend the direction text to the spoken script.

Generate native speed 1.0 and apply FFmpeg `atempo=1.20` (or the preset's configured `post_tempo`)
exactly once per the FFmpeg reference. Energy comes from phrasing, performance, and audio tags,
not artificial speedup or pitch shifts. Preserve comprehension holds at the final tempo.

## Audition before a full take

1. Read `narration.json` (or snapshot `narration-preset.json`) and resolve voice/model/settings.
2. Generate a cached 10–15-second sample combining the hook, a contrast, and a teaching line
   with audio tags and actual episode terms. Process it at the final tempo.
3. Listen for energy, voice modulation, warmth, pronunciation, and intelligibility. A successful
   API response or waveform is not listening evidence.
4. If unstable or overly theatrical, adjust stability toward 0.40 or style toward 0.35.
   Try at most two adjusted auditions; save the accepted settings.
5. Use the accepted settings for the continuous full take. Include the complete preset and tags in
   cache keys.

## Owner-selected audition preset takes precedence

Read project-root `narration.json` before synthesis. A dashboard-selected preset overrides
legacy defaults. Use its `voice_settings` at native speed 1.0 and apply its `post_tempo`
exactly once with FFmpeg. Transform alignment timestamps by that same ratio.

## Per-job voice snapshot

The launcher writes `output/<id>/narration-preset.json` before new production.
Read that snapshot as the authority for this run. Use its voice ID in the ElevenLabs URL,
model/settings in the payload, and tempo exactly once. Include voice, model, tags, and settings
in audio cache keys.
