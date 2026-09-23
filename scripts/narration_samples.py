"""Create cached, timestamp-independent voice auditions for Alex using eleven_v3."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import requests

ROOT = Path(__file__).resolve().parents[1]
TEXT = ("[excited] Your server crashes! [gasp] Does the customer's order disappear? "
        "[cheerful] Not if you use a queue. [warmly] Think of it as a waiting line for work. "
        "[calm] The queue keeps the order safe while a worker gets ready. [pauses] "
        "[authoritative] But here is the crucial part: receiving a job is not the same as finishing it.")

PRESETS = [
    ("expressive-explainer", "Expressive explainer", "Dynamic teaching with rich emotional modulation, active audio tags, and brisk tempo.", .35, .45, 1.20),
    ("punchy-presenter", "Punchy presenter", "High-energy, fast-paced delivery with punchy emphasis.", .25, .55, 1.28),
    ("warm-mentor", "Warm mentor", "Conversational, approachable explanation with friendly intonation.", .45, .30, 1.15),
    ("authoritative-architect", "Authoritative architect", "Deliberate, confident, measured technical delivery.", .55, .25, 1.12),
]


def load_env(path=ROOT / ".env"):
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def main():
    folder = ROOT / "assets/narration-samples"
    folder.mkdir(parents=True, exist_ok=True)
    cache = ROOT / "state/narration-sample-cache"
    cache.mkdir(parents=True, exist_ok=True)
    env = load_env()
    current = json.loads((ROOT / "narration.json").read_text())
    voice = env.get("ELEVEN_LABS_VOICE_ID") or current["voice_id"]
    model_id = current.get("model_id", "eleven_v3")

    def generate(spec):
        ident, name, description, stability, style, tempo = spec
        settings = {
            "stability": stability,
            "similarity_boost": 0.80,
            "style": style,
            "use_speaker_boost": True,
            "speed": 1.0,
        }
        payload = {"text": TEXT, "model_id": model_id, "voice_settings": settings}
        key = hashlib.sha256(json.dumps([voice, payload], sort_keys=True).encode()).hexdigest()
        raw = cache / f"{key}.mp3"
        if not raw.exists():
            r = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
                headers={"xi-api-key": env["ELEVEN_LABS_KEY"], "Content-Type": "application/json"},
                json=payload,
                timeout=180,
            )
            if not r.ok:
                raise RuntimeError(f"{ident}: ElevenLabs HTTP {r.status_code}: {r.text}")
            if not r.content:
                raise RuntimeError("Empty synthesis response")
            raw.write_bytes(r.content)

        out = folder / f"{ident}.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-v",
                "error",
                "-y",
                "-i",
                str(raw),
                "-af",
                f"atempo={tempo},loudnorm=I=-16:TP=-1.5:LRA=7",
                "-ar",
                "48000",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(out),
            ],
            check=True,
        )
        duration = float(
            subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(out)],
                text=True,
            )
        )
        return {
            "id": ident,
            "name": name,
            "voice_name": "Alex",
            "description": description,
            "voice_id": voice,
            "model_id": model_id,
            "voice_settings": settings,
            "post_tempo": tempo,
            "direction": description + " Expressive, modulated technical teaching with Eleven v3 audio tags; pause for comprehension.",
            "duration": round(duration, 2),
            "file": out.name,
            "cache_key": key,
            "audition_required": True,
            "review": "Awaiting owner listening and choice",
        }

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(generate, PRESETS))
    (folder / "catalog.json").write_text(json.dumps({"text": TEXT, "samples": results}, indent=2) + "\n")
    print(json.dumps([{"name": x["name"], "seconds": x["duration"]} for x in results], indent=2))


if __name__ == "__main__":
    main()
