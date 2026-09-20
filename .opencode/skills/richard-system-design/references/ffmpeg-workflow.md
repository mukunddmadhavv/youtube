# FFmpeg production — Richard YouTube

User-requested production tool. Use **FFmpeg and ffprobe** for every episode's
audio processing, final MP4, preview media and technical checks. Keep editable
HTML/Anime.js animation and the local Pitch-derived recipes: FFmpeg encodes the
animated frames, it does not turn a few static slides into adequate animation.

## Ownership and reproducibility

- One paused Anime.js master, absolute cue times, fixed 1920×1080 canvas, 30fps.
- Freeze local artwork/fonts/runtime. Capture frame N at exactly N/30 seconds
  using the installed HyperFrames renderer or a deterministic browser capture
  that explicitly seeks the same master. Await images/fonts before capture.
- Save capture command, browser/runtime versions and FFmpeg settings in QA.
- No FFmpeg concat of mismatched video codecs/frame sizes. Never use `-shortest`
  to hide a narration/canvas timing mismatch or cut off speech.
- Tool exit success proves a technical operation, not artistic/listening QA.
- First encode a short representative excerpt and probe it. Confirm source
  range/matrix and final stream properties before committing to full capture.
  Follow `production-lessons.md` for preflight, sample review and evidence scope.

## Narration: generate once, process once

Load the workspace `.env` only inside a tool process; never embed keys in HTML,
report files, command arguments or stdout. ElevenLabs Adam and the selected
voice/model remain unchanged unless the user chooses another.

Save original provider audio and alignment. Use native speed 1.0, then one
pitch-preserving `atempo=1.3`. Example (paths are episode-relative):

```sh
ffmpeg -nostdin -y -i audio/native.mp3 -af atempo=1.3 \
  -ar 48000 -ac 1 -c:a pcm_s16le audio/full.wav
ffprobe -v error -show_entries format=duration -of json audio/full.wav
```

When provider character/word timestamps are native-speed, map timestamps by
dividing by 1.3. If native chunks were joined, include their measured native
offsets before dividing. Confirm aligned transcript coverage, monotonic times,
final duration and actual sync. Do not label heuristic word-count timing as
alignment. Regenerating/reprocessing audio invalidates dependent cues.

Cache TTS by text + voice + model + settings + output format. Save voice settings
without credentials. Do not regenerate a completed take because a render failed.

## H.264/AAC output

For a PNG frame sequence named frame-000000.png, etc.:

```sh
ffmpeg -nostdin -y -framerate 30 -i frames/frame-%06d.png \
  -i audio/full.wav -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -vf setsar=1 -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart video.mp4
```

A verified lossless/visually lossless intermediate or image pipe is also valid.
If using a captured visual-only intermediate, mux that visual track with the
same audio master. Export duration is ceil((audio duration + chosen tail)*30)/30;
all values and any audio padding must be recorded. Include the tail in 180–480s.
Use a final hold rather than a blank ending. Retain the same visual timing and
never apply `atempo` again during muxing. Export BT.709 SDR when applicable.

### JPEG/full-range capture: convert samples, not just metadata

The Jev run's browser JPEG pipe initially yielded `yuvj420p` even with an output
pixel-format request. Inspect an encoded sample with ffprobe. When the decoded
source is full-range, explicitly convert it to limited range during the first
delivery encode, for example:

```sh
ffmpeg -nostdin -y -i full-range-intermediate.mp4 -i audio/full.wav \
  -map 0:v:0 -map 1:a:0 \
  -vf "scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuv420p,setsar=1" \
  -c:v libx264 -preset medium -crf 18 \
  -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart video-candidate.mp4
```

This example assumes a **verified full-range SDR source**. Supply its known
input matrix when conversion needs it; do not copy these flags to an unknown
or already limited-range source. Metadata flags do not perform color conversion.
Do not apply full→limited conversion twice. Compare decoded colors and probe
actual `pix_fmt`, `color_range`, matrix, primaries and transfer characteristics;
requested command options alone do not prove the resulting metadata or pixels.

Keep raw capture/intermediates immutable. Write a candidate, verify it, then
promote to the delivery filename. A rerun must select the original declared
source, not take the already-converted `video.mp4` as full-range input again.
Record source hashes and conversion history. Prefer one final delivery encode
over repairing a predictable range error with successive lossy encodes.

For parallel frame capture, partition integer frame indices into contiguous,
non-overlapping ranges. Verify each chunk's frame count/fps/size/color properties,
the total `ceil(duration*30)` frames, and the actual boundary frames before
concatenation. Missing/duplicated frames and mismatched timestamps can introduce
seams even when FFmpeg concat exits successfully.

## Technical checks

```sh
ffprobe -v error -show_format -show_streams -of json video.mp4
ffmpeg -nostdin -v error -i video.mp4 -f null -
ffmpeg -nostdin -i video.mp4 -af ebur128=peak=true -vn -f null -
ffmpeg -nostdin -i video.mp4 \
  -vf blackdetect=d=0.25:pix_th=0.10 -an -f null -
ffmpeg -nostdin -y -i video.mp4 -vf scale=640:360 -c:v libx264 \
  -crf 22 -c:a aac qa/preview-640.mp4
ffmpeg -nostdin -y -i video.mp4 -vf scale=320:180 -c:v libx264 \
  -crf 22 -c:a aac qa/preview-320.mp4
```

Verify 1920×1080, 30fps, square pixels, H.264/yuv420p, AAC, complete duration,
no decode errors, no unintentional black sections, and no clipped final audio.
Measure final encoded loudness/true peak; target clear voice near −16 to −14 LUFS
with true peak ≤−1 dBTP as mastering guidance, not a promise from TTS settings.
If gain changes are needed, measure first, apply one documented correction to a
derived mix, then remux. Preserve natural pitch and avoid double normalization.

Capture actual exported frames at hook 0/1/3/5s, all chapter midpoints, each
distinct action's start/mid/end, and final-minus-hold. Build contact sheets with
FFmpeg `tile` for inspection. Compare repeated forward/backward browser seeks
to identical timestamps independently of export sampling.

Check captions at 640×360 and 320×180; use 3–7 aligned words and two lines,
allowing shorter cues at semantic boundaries. Inspect actual native-size images
or playback: generating preview files alone is not a readability review.
Create thumbnail.png at 1280×720 under 2MB. Review motion temporally and listen
to the full render before claiming PASS. If listening/playback is unavailable,
deliver the generated video as a review draft with checks marked NOT VERIFIED;
do not admit it to automatic publishing under a false QA status.

## Owner-selected audition preset takes precedence

Read project-root `narration.json` before synthesis. A dashboard-selected
preset overrides older numerical voice-settings and fixed-1.3 examples
in this skill. Use its `voice_settings` at native speed 1.0 and apply its
`post_tempo` exactly once with FFmpeg. Transform alignment timestamps by
that same ratio, not a hardcoded 1.3. Include the resolved preset in cache
keys. Keep each episode's audition and actual listening verification.
