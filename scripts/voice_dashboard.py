"""Authenticated audition routes, protected by the dashboard's session/CSRF hooks."""
import json
from pathlib import Path
from flask import Blueprint, abort, jsonify, request, send_file
import pipeline as p

ROOT=Path(__file__).resolve().parents[1]
voices=Blueprint('voices',__name__)

def catalog():
    return json.loads((ROOT/'assets/narration-samples/catalog.json').read_text())

@voices.get('/voices')
def page():
    return send_file(ROOT/'dashboard/voices.html')

@voices.get('/static/voices.js')
def script():
    return send_file(ROOT/'dashboard/voices.js')

@voices.get('/api/voices')
def options():
    data=catalog()
    current=json.loads((ROOT/'narration.json').read_text())
    for sample in data['samples']:
        sample['url']='/media/voice-samples/'+sample['id']
    data['selected']=current.get('preset_id')
    return jsonify(data)

@voices.get('/media/voice-samples/<sample_id>')
def audio(sample_id):
    sample=next((s for s in catalog()['samples'] if s['id']==sample_id),None)
    if not sample: abort(404)
    file=p.local_file(ROOT/'assets/narration-samples',sample['file'])
    return send_file(file,mimetype='audio/mpeg',conditional=True)

@voices.post('/api/voices/select')
def select():
    sample=next((s for s in catalog()['samples'] if s['id']==request.get_json().get('id')),None)
    if not sample: abort(400)
    with p.lock('settings') as acquired:
        if not acquired: abort(409)
        current=json.loads((ROOT/'narration.json').read_text())
        for key in ('voice_id','model_id','voice_settings','post_tempo','direction','audition_required'):
            current[key]=sample[key]
        current['preset_id']=sample['id']
        p.dump(ROOT/'narration.json',current)
    return jsonify(ok=True,selected=sample['id'])
