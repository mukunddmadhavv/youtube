"""Apply narration guidance without replacing destination-specific agent config."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / '.opencode/skills/richard-system-design/SKILL.md'
text = path.read_text()
anchor = '7. Verify ElevenLabs account voice/model access using ELEVEN_LABS_KEY from .env.\n'
addition = ("   Read project-root `narration.json` and `references/narration-delivery.md` for\n"
            "   the owner's energetic, confident teaching preset. Use its resolved settings\n"
            "   in the generation script rather than an older episode's hardcoded values.\n")
if 'references/narration-delivery.md' not in text:
    if text.count(anchor) != 1:
        raise SystemExit('Unexpected skill structure; inspect before modifying')
    text = text.replace(anchor, anchor + addition)
text = text.replace('.35, similarity_boost .75, style .25', '.30, similarity_boost .75, style .45')
path.write_text(text)
path = root / '.opencode/agents/richardSystemDesign.md'
text = path.read_text()
addition = ('\n## Narration performance\n\n'
            'For new narration, read project-root `narration.json` and the local skill\n'
            '`references/narration-delivery.md`. Use the energetic, confident, friendly\n'
            'teaching preset with an actual audition, clear emphasis and comprehension\n'
            'holds. Do not reuse an old episode\'s hardcoded voice settings.\n')
if '## Narration performance' not in text:
    path.write_text(text + addition)
print('Updated narration preset guidance; existing rendered audio was preserved.')
