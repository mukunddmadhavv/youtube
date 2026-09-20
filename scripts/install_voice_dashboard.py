"""Wire voice auditions without overwriting remote dashboard or agent changes."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/'scripts/dashboard.py';text=path.read_text()
anchor='    return app\n'
if 'app.register_blueprint(voices)' not in text:
    if text.count(anchor)!=1: raise SystemExit('Unexpected dashboard entry point')
    text=text.replace(anchor,'    from voice_dashboard import voices\n    app.register_blueprint(voices)\n'+anchor)
    path.write_text(text)
path=root/'dashboard/index.html';text=path.read_text()
if 'href="/voices"' not in text:
    text=text.replace('</nav>','<a href="/voices">♫ Voice auditions</a></nav>');path.write_text(text)
# The selected preset's tempo must take precedence over legacy fixed-1.3 examples.
for name in ('SKILL.md','references/narration-delivery.md','references/ffmpeg-workflow.md'):
    path=root/'.opencode/skills/richard-system-design'/name
    text=path.read_text()
    note=('\n## Owner-selected audition preset takes precedence\n\n'
          'Read project-root `narration.json` before synthesis. A dashboard-selected\n'
          'preset overrides older numerical voice-settings and fixed-1.3 examples\n'
          'in this skill. Use its `voice_settings` at native speed 1.0 and apply its\n'
          '`post_tempo` exactly once with FFmpeg. Transform alignment timestamps by\n'
          'that same ratio, not a hardcoded 1.3. Include the resolved preset in cache\n'
          'keys. Keep each episode\'s audition and actual listening verification.\n')
    if '## Owner-selected audition preset takes precedence' not in text:path.write_text(text+note)
print('Voice auditions wired; selected presets govern future narration settings and tempo.')
