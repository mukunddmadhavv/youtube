"""Add the owner's buffer research instructions while preserving host changes."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
skill=root/'.opencode/skills/richard-system-design/SKILL.md'
text=skill.read_text()
note=('\n## Automatic buffer topic discovery\n\n'
      'Before choosing every automatic buffer topic, read\n'
      '`references/fireship-topic-research.md`. First inspect recent content at\n'
      'https://www.youtube.com/@Fireship/videos, then independently search current\n'
      'tech trends and primary sources. Deduplicate against history.json, choose\n'
      'one original Richard teaching angle, and save topic-research.md before\n'
      'scripting. Record actual access and evidence; never invent a live channel\n'
      'check or trending status. Explicit owner topics remain authoritative.\n')
if '## Automatic buffer topic discovery' not in text: skill.write_text(text+note)
agent=root/'.opencode/agents/richardSystemDesign.md'
text=agent.read_text()
anchor='## Scheduled production\n'
note=('\nFor each automatic buffer episode, FIRST check the recent videos at\n'
      'https://www.youtube.com/@Fireship/videos, THEN research current tech trends\n'
      'and original sources. Follow the local skill reference\n'
      '`references/fireship-topic-research.md`, save topic-research.md, and choose\n'
      'a fresh topic after checking history. Adapt useful editorial techniques\n'
      'into an original Richard script and animation, preserving the selected\n'
      'voice and 16:9 teaching format. Keep explicit dashboard topics unchanged.\n')
if 'references/fireship-topic-research.md' not in text:
    if text.count(anchor)!=1: raise SystemExit('Unexpected agent structure')
    agent.write_text(text.replace(anchor,anchor+note))
path=root/'scripts/pipeline.py';text=path.read_text()
anchor='                     "question after checking history.json.\\n\\n"'
addition=('\n                     "First inspect https://www.youtube.com/@Fireship/videos for recent topics, "'
          '\n                     "then independently search current tech trends and primary sources. Follow "'
          '\n                     "the workspace references/fireship-topic-research.md, save topic-research.md, "'
          '\n                     "and choose an original Richard explanation after deduplicating history.\\n\\n"')
if 'First inspect https://www.youtube.com/@Fireship/videos' not in text:
    if text.count(anchor)!=1: raise SystemExit('Unexpected buffer brief structure')
    text=text.replace(anchor,anchor+addition)
text=text.replace('"Adam narration, causal animations, research and QA contract.\\n"',
                  '"the owner-selected narration preset, causal animations, research and QA contract.\\n"')
compile(text,str(path),'exec')
path.write_text(text)
print('Fireship-first research linked in the local skill, Richard agent, and automatic buffer brief.')
