"""Read-only destination checks, including authenticated dashboard login."""
import hashlib
import json
from pathlib import Path
import requests
import sqlite3

root=Path(__file__).resolve().parents[1]
password=(root/'secrets/dashboard-login.txt').read_text().split('Password: ',1)[1].strip()
client=requests.Session()
r=client.post('http://127.0.0.1:2021/api/login',json={'password':password},timeout=10)
assert r.status_code==200, r.status_code
# Production uses Secure cookies for Cloudflare HTTPS. This loopback probe
# explicitly sends the returned cookie once to test the protected endpoint.
cookie=r.headers.get('Set-Cookie','').split(';',1)[0]
r=client.get('http://127.0.0.1:2021/api/state',headers={'Cookie':cookie},timeout=10)
assert r.status_code==200, r.status_code
data=r.json()
video=root/'output/jev-vs-llms/video.mp4'
with sqlite3.connect(root/'state/queue.sqlite3') as conn:
    integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
assert integrity=='ok'
assert data['worker']['online']
assert any(e['id']=='jev-vs-llms' for e in data['episodes'])
print(json.dumps({'dashboard_login':'passed','worker_online':True,'database_integrity':integrity,
                  'episode_count':len(data['episodes']),'video_sha256':hashlib.file_digest(video.open('rb'),'sha256').hexdigest(),
                  'generation_enabled':data['settings']['generation_enabled'],
                  'publishing_enabled':data['settings']['publishing_enabled']},indent=2))
