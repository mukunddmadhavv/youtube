"""Link Netflix-specific lessons without overwriting remote skill/agent changes."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
note = ('\n## Netflix-derived production checks\n\n'
        'Before building or repairing a video, read the workspace Richard skill\n'
        '`references/netflix-production-lessons.md`. Separate static SVG layout\n'
        'from motion wrappers, avoid repeated collection resets, preserve legible\n'
        'text and real causal movement, validate generated markup, and synchronize\n'
        'factual changes across narration/captions/visuals. Verify numerical examples\n'
        'and review evidence rather than inheriting a previous report\'s PASS labels.\n')
for relative in ('.opencode/agents/richardSystemDesign.md',
                 '.opencode/skills/richard-system-design/SKILL.md',
                 '.opencode/skills/richard-system-design/references/production-lessons.md',
                 '.opencode/skills/richard-system-design/references/full-video-frame-audit.md'):
    path = root / relative
    text = path.read_text()
    if 'netflix-production-lessons.md' not in text:
        path.write_text(text + note)
print('Netflix lessons linked from Richard agent, skill, production lessons and frame QA.')
