"""Helper utilities for parsing Eleven v3 alignments and handling emotional audio tags."""
import re
from typing import Any, Dict, List


def strip_audio_tags(text: str) -> str:
    """Strip bracketed audio tags like [excited], [pauses] from narration text."""
    cleaned = re.sub(r"\[.*?\]", "", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_words_from_alignment(
    alignment: Dict[str, Any], tempo: float = 1.0
) -> List[Dict[str, Any]]:
    """Extract spoken words and their start/end timestamps from ElevenLabs alignment.
    
    Audio tags enclosed in square brackets [...] are skipped so that they do not
    appear in the visual word stream or caption output.
    Timestamps are adjusted by tempo (e.g. atempo=1.2 means time is divided by 1.2).
    """
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])

    if not (len(chars) == len(starts) == len(ends)):
        raise ValueError("Mismatched alignment array lengths")

    words = []
    curr_chars: List[str] = []
    curr_start = None
    curr_end = None
    in_tag = False

    for c, s, e in zip(chars, starts, ends):
        if c == "[":
            in_tag = True
            continue
        if in_tag:
            if c == "]":
                in_tag = False
            continue

        if c == " ":
            if curr_chars:
                words.append({
                    "word": "".join(curr_chars),
                    "start": round(curr_start / tempo, 3),
                    "end": round(curr_end / tempo, 3),
                })
                curr_chars = []
                curr_start = None
                curr_end = None
        else:
            if curr_start is None:
                curr_start = s
            curr_end = e
            curr_chars.append(c)

    if curr_chars:
        words.append({
            "word": "".join(curr_chars),
            "start": round(curr_start / tempo, 3),
            "end": round(curr_end / tempo, 3),
        })

    return words


def format_srt_time(seconds: float) -> str:
    """Format seconds into SRT timestamp string HH:MM:SS,mmm."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis -= 1000
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def generate_srt_cues(words: List[Dict[str, Any]], max_words_per_cue: int = 5) -> str:
    """Group words into semantic 3-6 word subtitle cues without any audio tags."""
    if not words:
        return ""

    cues = []
    cue_idx = 1
    i = 0
    while i < len(words):
        chunk = words[i : i + max_words_per_cue]
        start_time = chunk[0]["start"]
        end_time = chunk[-1]["end"]
        cue_text = " ".join(w["word"] for w in chunk)

        cues.append(
            f"{cue_idx}\n{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n{cue_text}\n"
        )
        cue_idx += 1
        i += max_words_per_cue

    return "\n".join(cues)
