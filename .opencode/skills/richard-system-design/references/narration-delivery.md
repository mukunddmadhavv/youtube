# Energetic, confident teaching voice

User direction: make ElevenLabs narration more energetic, confident and teaching-oriented.
The project-root `narration.json` is the authoritative synthesis preset. Read it
before each audition or new narration take, rather than copying settings from
an older episode's script. Preserve the configured Adam voice unless overridden
explicitly by the owner. Dashboard selection takes precedence over legacy environment voice defaults.

## Delivery

Sound like an enthusiastic expert helping one learner understand a mechanism:

- Project clearly, with natural pitch variation and crisp consonants.
- Emphasize the entity and action: “The **queue** keeps the job. The **worker**
  picks it up.” Make contrasts audible: “Received is not the same as committed.”
- Use short spoken sentences, concrete verbs and occasional prediction questions.
- Deliver the hook with curiosity and conviction, then settle into explanation.
- Slow down for new terms, code and numerical claims. Leave a brief pause after
  the result so viewers can connect the voice to the animation.
- Keep warmth and confidence without sustained shouting, fake urgency, sales
  delivery, baby talk, or overstating uncertain technical claims.

## Synthesis preset and limits

Starting preset: Adam, eleven_multilingual_v2, stability 0.30,
similarity_boost 0.75, style 0.45, speaker boost enabled, native speed 1.0.
Compared with the prior 0.35 stability / 0.25 style preset, this allows a little
more variation and stronger style expression. These controls do not guarantee
a particular emotion, clarity or quality; the audition decides.

The `direction` field in narration.json is an editorial instruction for the
scriptwriter/reviewer, **not** a supported ElevenLabs request field. Send only
the documented API payload fields. Do not prepend the direction to spoken text.
Do not insert Eleven v3 audio tags such as [excited] into multilingual_v2 text.
Use natural punctuation and phrasing; do not capitalize whole paragraphs.

Generate native speed 1.0 and apply `atempo=1.3` exactly once per the FFmpeg
reference. Energy comes from phrasing and performance, not extra acceleration,
pitch shifts or louder normalization. Preserve comprehension holds at the
final processed speed. No further renderer playback-rate change.

## Audition before a full take

1. Read narration.json and save the resolved voice/model/settings without secrets.
2. Generate a cached 10–15-second sample combining the hook, a contrast, and a
   teaching line containing an actual episode term. Process it at the final tempo.
3. Listen for energy, confidence, warmth, pronunciation and intelligibility. A
   waveform or successful API response is not listening evidence.
4. If unstable or overly theatrical, raise stability toward 0.35–0.40 or lower
   style toward 0.30–0.35. Try at most two adjusted auditions; save the selected
   settings and reviewer/tool/outcome. Do not silently change voice or provider.
5. Use the accepted settings for the continuous full take. Include the complete
   preset in cache keys. A changed preset must not reuse an old cached take.

If listening is unavailable, record NOT VERIFIED and identify the sample for
owner review. Do not claim the new performance has been auditioned.
For an existing episode, a narration change requires a new audio master,
alignment, visual cue adjustment and render. Never replace its audio alone and
leave the old captions/animation timestamps unchanged.

## Owner-selected audition preset takes precedence

Read project-root `narration.json` before synthesis. A dashboard-selected
preset overrides older numerical voice-settings and fixed-1.3 examples
in this skill. Use its `voice_settings` at native speed 1.0 and apply its
`post_tempo` exactly once with FFmpeg. Transform alignment timestamps by
that same ratio, not a hardcoded 1.3. Include the resolved preset in cache
keys. Keep each episode's audition and actual listening verification.

## Per-job voice snapshot

The launcher writes `output/<id>/narration-preset.json` before new production
or a requested revision. Read that snapshot as the authority for this run.
Use its voice ID in the ElevenLabs URL, model/settings in the payload, and
tempo exactly once. `.env` supplies the API key, not a voice override.
Changing the dashboard while a job runs affects subsequent jobs. A revision
uses the current selected preset if narration is regenerated; a visual-only
revision can retain existing audio. Never reuse a different voice cache.
