"""Apply full-video QA instructions without replacing host-specific settings."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
for relative in ('.opencode/skills/richard-system-design/SKILL.md',
                 '.opencode/agents/richardSystemDesign.md'):
    path = root / relative
    text = path.read_text()
    note = ('\n## Mandatory full-export frame audit\n\n'
            'After every full render, follow the workspace Richard skill reference\n'
            '`references/full-video-frame-audit.md`. Run `scripts/frame_audit.py`\n'
            'against the actual exported MP4 to extract one frame every 3 seconds\n'
            'across the whole video plus the final frame. Inspect EVERY sheet/frame,\n'
            'record timestamped defects, fix the source and rerender. Review moving\n'
            'excerpts and every transition as well; still images cannot prove motion\n'
            'quality or narration sync. Re-extract and inspect the corrected final\n'
            'export before declaring QA passed. Never equate extraction success with\n'
            'visual approval. Preserve honest draft status if review is unavailable.\n')
    if '## Mandatory full-export frame audit' not in text:
        path.write_text(text + note)
print('Full-export three-second frame audit is required by the skill and agent.')
