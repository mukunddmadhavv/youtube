"""Resolve and freeze dashboard-selected narration for one production session."""
import json
from pathlib import Path


def snapshot(root, episode_id):
    source = root / 'narration.json'
    if not source.exists():
        raise ValueError('Missing narration.json; select a narration preset first')
    preset = json.loads(source.read_text())
    for key in ('voice_id', 'model_id', 'voice_settings', 'post_tempo'):
        if key not in preset:
            raise ValueError(f'Missing narration setting: {key}')
    folder = root / 'output' / episode_id
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / 'narration-preset.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(preset, indent=2) + '\n')
    temp.replace(target)
    return preset


def instruction(episode_id):
    return (f'\nNARRATION CONTRACT: Read output/{episode_id}/narration-preset.json. '
            'This is the owner-selected voice snapshot for this job. Use its voice_id in the '
            'ElevenLabs synthesis URL, model_id and voice_settings in the request, and post_tempo '
            'exactly once with FFmpeg. Do NOT use ELEVEN_LABS_VOICE_ID from .env or an older '
            'episode hardcoded voice. Read only ELEVEN_LABS_KEY for authentication. '
            'Record the actual resolved preset in audio/voice-settings.json. Include voice, '
            'model and settings in audio cache keys. Realign and rerender if changing narration.')
