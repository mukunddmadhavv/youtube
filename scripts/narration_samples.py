"""Create cached, timestamp-independent voice auditions without exposing keys."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
TEXT = ("Your server crashes. Does the customer's order disappear? Not if you use a queue. "
        "Think of it as a waiting line for work. The queue keeps the order safe while a worker "
        "gets ready. But here is the important part: receiving a job is not the same as finishing it.")
PRESETS = [
    ('warm-teacher', 'Warm teacher', 'Friendly, measured explanation with gentler expression.', .48, .20, 1.12),
    ('energetic-explainer', 'Energetic explainer', 'Lively teaching with stronger emphasis and a brisk pace.', .30, .45, 1.25),
    ('calm-authority', 'Calm authority', 'Steady, confident explanation with restrained expression.', .65, .12, 1.10),
    ('punchy-presenter', 'Punchy presenter', 'More expressive variation and the fastest final pace.', .25, .60, 1.30),
]


def main():
    folder=ROOT/'assets/narration-samples';folder.mkdir(parents=True,exist_ok=True)
    cache=ROOT/'state/narration-sample-cache';cache.mkdir(parents=True,exist_ok=True)
    env=dotenv_values(ROOT/'.env')
    current=json.loads((ROOT/'narration.json').read_text())
    voice=env.get('ELEVEN_LABS_VOICE_ID') or current['voice_id']
    def generate(spec):
        ident,name,description,stability,style,tempo=spec
        settings={'stability':stability,'similarity_boost':.75,'style':style,'use_speaker_boost':True,'speed':1.0}
        payload={'text':TEXT,'model_id':current['model_id'],'voice_settings':settings}
        key=hashlib.sha256(json.dumps([voice,payload],sort_keys=True).encode()).hexdigest()
        raw=cache/f'{key}.mp3'
        if not raw.exists():
            r=requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128',
                            headers={'xi-api-key':env['ELEVEN_LABS_KEY'],'Content-Type':'application/json'},json=payload,timeout=180)
            if not r.ok: raise RuntimeError(f'{ident}: ElevenLabs HTTP {r.status_code}')
            if not r.content: raise RuntimeError('Empty synthesis response')
            raw.write_bytes(r.content)
        out=folder/f'{ident}.mp3'
        # Same mastering target for fair comparison; tempo is applied once.
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(raw),'-af',
                        f'atempo={tempo},loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','-c:a','libmp3lame','-b:a','192k',str(out)],check=True)
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(out)],text=True))
        return {'id':ident,'name':name,'description':description,'voice_id':voice,'model_id':current['model_id'],
                'voice_settings':settings,'post_tempo':tempo,'direction':description+' Clear, confident, friendly technical teaching; pause for comprehension.',
                'duration':round(duration,2),'file':out.name,'cache_key':key,'audition_required':True,'review':'Awaiting owner listening and choice'}
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(generate,PRESETS))
    (folder/'catalog.json').write_text(json.dumps({'text':TEXT,'samples':results},indent=2)+'\n')
    print(json.dumps([{'name':x['name'],'seconds':x['duration']} for x in results],indent=2))


if __name__=='__main__':main()
