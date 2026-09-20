"""Wire explicit voice snapshots into current remote production entry points."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
path = root / 'scripts/pipeline.py'
text = path.read_text()
anchor = '    return command + [prompt]  # No --continue / --session: new session each time.'
replacement = ('    if (ROOT / "narration.json").exists():\n'
               '        from voice_selection import snapshot, instruction\n'
               '        snapshot(ROOT, episode_id)\n'
               '        prompt += instruction(episode_id)\n' + anchor)
if 'from voice_selection import snapshot, instruction' not in text:
    if text.count(anchor) != 1: raise SystemExit('Unexpected pipeline source')
    path.write_text(text.replace(anchor, replacement))
path = root / 'scripts/dashboard.py'
text = path.read_text()
anchor = "        with (folder/'session.jsonl').open('a') as log:"
addition = ("        from voice_selection import instruction\n"
            "        if job['kind']=='revise': command[-1] += instruction(eid)\n")
if 'from voice_selection import instruction' not in text:
    if text.count(anchor) != 1: raise SystemExit('Unexpected dashboard source')
    path.write_text(text.replace(anchor, addition + anchor))
path = root / '.opencode/skills/richard-system-design/references/narration-delivery.md'
text = path.read_text().replace('explicitly by the owner; an explicit ELEVEN_LABS_VOICE_ID override takes precedence.',
    'explicitly by the owner. Dashboard selection takes precedence over legacy environment voice defaults.')
note = ('\n## Per-job voice snapshot\n\n'
        'The launcher writes `output/<id>/narration-preset.json` before new production\n'
        'or a requested revision. Read that snapshot as the authority for this run.\n'
        'Use its voice ID in the ElevenLabs URL, model/settings in the payload, and\n'
        'tempo exactly once. `.env` supplies the API key, not a voice override.\n'
        'Changing the dashboard while a job runs affects subsequent jobs. A revision\n'
        'uses the current selected preset if narration is regenerated; a visual-only\n'
        'revision can retain existing audio. Never reuse a different voice cache.\n')
if '## Per-job voice snapshot' not in text: text += note
path.write_text(text)
print('Voice selection priority and per-job snapshots installed.')
