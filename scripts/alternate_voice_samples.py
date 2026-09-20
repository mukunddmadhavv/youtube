"""Generate explicitly requested alternative-voice auditions, without changing defaults."""
import hashlib
import json
from pathlib import Path
import subprocess
import requests
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
TEXT=("Your server crashes. Does the customer's order disappear? Not if you use a queue. "
      "Think of it as a waiting line for work. The queue keeps the order safe while a worker "
      "gets ready. But here is the important part: receiving a job is not the same as finishing it.")
VOICES=[('charlie','IKne3meq5aSn9XLyUdCD'),('liam','TX3LPaxmHKxFdv7VOQHJ'),('brian','nPczCjzI2devNBz1zQrb')]

def main():
    out=ROOT/'assets/alternate-voice-samples';out.mkdir(parents=True,exist_ok=True)
    cache=ROOT/'state/narration-sample-cache';cache.mkdir(parents=True,exist_ok=True)
    env=dotenv_values(ROOT/'.env')
    payload={'text':TEXT,'model_id':'eleven_multilingual_v2',
             'voice_settings':{'stability':.35,'similarity_boost':.75,'style':.4,'use_speaker_boost':True,'speed':1.0}}
    results=[]
    for name,voice in VOICES:
        key=hashlib.sha256(json.dumps([voice,payload],sort_keys=True).encode()).hexdigest()
        raw=cache/f'{key}.mp3'
        if not raw.exists():
            response=requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128',
                                   headers={'xi-api-key':env['ELEVEN_LABS_KEY'],'Content-Type':'application/json'},
                                   json=payload,timeout=180)
            if not response.ok:
                print(f'{name}: synthesis unavailable (HTTP {response.status_code})');continue
            if not response.content: raise RuntimeError('Empty synthesis response')
            raw.write_bytes(response.content)
        file=out/f'{name}.mp3'
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(raw),'-af',
                        'atempo=1.15,loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','-c:a','libmp3lame','-b:a','192k',str(file)],check=True)
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(file)],text=True))
        results.append({'name':name,'voice_id':voice,'file':file.name,'duration':round(duration,2),'post_tempo':1.15,'settings':payload['voice_settings']})
    (out/'catalog.json').write_text(json.dumps({'text':TEXT,'samples':results,'review':'Awaiting owner listening; no default changed'},indent=2))
    print(json.dumps([{'name':s['name'],'seconds':s['duration']} for s in results]))

if __name__=='__main__':main()
