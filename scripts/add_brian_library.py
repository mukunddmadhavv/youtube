"""Add the existing Brian audition to the selectable voice library."""
import json
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[1]
source=root/'assets/alternate-voice-samples'
target=root/'assets/narration-samples'
alternate=json.loads((source/'catalog.json').read_text())
brian=next(s for s in alternate['samples'] if s['name']=='brian')
catalog=json.loads((target/'catalog.json').read_text())
shutil.copy2(source/brian['file'],target/'brian.mp3')
entry={'id':'brian','name':'Brian','voice_name':'Brian',
       'description':'An alternative narrator for clear, confident technical teaching. Compare the recorded sample.',
       'voice_id':brian['voice_id'],'model_id':'eleven_multilingual_v2',
       'voice_settings':brian['settings'],'post_tempo':brian['post_tempo'],
       'direction':'Confident, engaging, friendly technical teacher. Emphasize key ideas and pause for comprehension.',
       'duration':brian['duration'],'file':'brian.mp3','audition_required':True,
       'review':'Awaiting owner listening and choice'}
catalog['samples']=[s for s in catalog['samples'] if s['id']!='brian']+[entry]
for sample in catalog['samples']:
    sample.setdefault('voice_name','Adam')
path=target/'catalog.json';temp=path.with_suffix('.tmp')
temp.write_text(json.dumps(catalog,indent=2)+'\n');temp.replace(path)
path=root/'dashboard/voices.js';text=path.read_text()
text=text.replace('Adam · ${s.post_tempo}',"${esc(s.voice_name||'Adam')} · ${s.post_tempo}")
path.write_text(text)
path=root/'dashboard/voices.html';text=path.read_text()
text=text.replace('Four fresh Adam recordings. Same passage, different expression and pacing.',
                  'Compare Adam delivery styles and Brian’s voice. Same passage, different expression and pacing.')
path.write_text(text)
print('Brian added to voice library; current default preserved.')
