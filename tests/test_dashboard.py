import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,MagicMock
from werkzeug.security import generate_password_hash

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import dashboard as d
import pipeline as p
REAL_ROOT=p.ROOT

class DashboardTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.patches=[patch.object(p,'ROOT',self.root),patch.object(d,'ROOT',self.root)]
        for obj in self.patches:obj.start()
        (self.root/'pipeline.json').write_text((REAL_ROOT/'pipeline.json').read_text())
        (self.root/'topics.json').write_text('["A first topic"]')
        (self.root/'output').mkdir()
        self.app=d.create_app({'TESTING':True,'SECRET_KEY':'test-secret','PASSWORD_HASH':generate_password_hash('test-password')})
        self.client=self.app.test_client();self.csrf=''
    def tearDown(self):
        for obj in self.patches:obj.stop()
        self.temp.cleanup()
    def login(self):
        r=self.client.post('/api/login',json={'password':'test-password'});self.assertEqual(r.status_code,200);self.csrf=r.json['csrf']
    def post(self,url,data):return self.client.post(url,json=data,headers={'X-CSRF-Token':self.csrf})
    def test_auth_media_and_settings_protected(self):
        self.assertEqual(self.client.get('/api/state').status_code,401)
        self.assertEqual(self.client.get('/media/jev-vs-llms/video').status_code,401)
        self.assertEqual(self.client.post('/api/login',json={'password':'wrong'}).status_code,401)
    def test_csrf_and_origin_required(self):
        self.login()
        self.assertEqual(self.client.post('/api/videos',json={'topic':'An example'}).status_code,403)
        self.assertEqual(self.client.post('/api/videos',json={'topic':'An example'},headers={'X-CSRF-Token':self.csrf,'Origin':'https://evil.example'}).status_code,403)
    def test_create_is_queued_not_generated_by_request(self):
        self.login()
        with patch.object(d.subprocess,'Popen') as proc:
            r=self.post('/api/videos',{'topic':'How queues retry','notes':'Explain idempotency'})
            self.assertEqual(r.status_code,202);proc.assert_not_called()
        state=self.client.get('/api/state').json
        self.assertEqual(state['episodes'][0]['status'],'queued')
        self.assertEqual(state['jobs'][0]['kind'],'create')
    def test_settings_validation_preserves_secrets_and_channel(self):
        self.login();old=json.loads((self.root/'pipeline.json').read_text())
        self.assertEqual(self.post('/api/settings',{'timezone':'Bad/Zone'}).status_code,400)
        self.assertEqual(self.post('/api/settings',{'channel_id':'attacker'}).status_code,400)
        self.assertEqual(self.post('/api/settings',{'buffer_target':12}).status_code,200)
        new=json.loads((self.root/'pipeline.json').read_text())
        self.assertEqual(new['channel_id'],old['channel_id']);self.assertEqual(new['buffer_target'],12)
    def test_media_allowlist_and_range(self):
        self.login();folder=self.root/'output/example';folder.mkdir();(folder/'video.mp4').write_bytes(b'0123456789')
        r=self.client.get('/media/example/video',headers={'Range':'bytes=2-5'})
        self.assertEqual(r.status_code,206);self.assertEqual(r.data,b'2345');r.close()
        self.assertEqual(self.client.get('/media/example/session.jsonl').status_code,404)
        (folder/'thumbnail.png').symlink_to(self.root/'pipeline.json')
        self.assertEqual(self.client.get('/media/example/thumbnail').status_code,404)
    def test_import_draft_does_not_approve(self):
        folder=self.root/'output/example';folder.mkdir();(folder/'video.mp4').write_bytes(b'video')
        d.import_drafts();d.import_drafts();self.login()
        state=self.client.get('/api/state').json
        self.assertEqual(len(state['episodes']),1);self.assertEqual(state['episodes'][0]['status'],'draft')
    def test_duplicate_operation_rejected(self):
        self.login();self.assertEqual(self.post('/api/operations/sync',{}).status_code,202)
        self.assertEqual(self.post('/api/operations/sync',{}).status_code,400)
    def test_secrets_redacted(self):
        (self.root/'.env').write_text('ELEVEN_LABS_KEY=sk_test_abcdef12345\n')
        self.assertNotIn('sk_test_abcdef12345',d.redact('key sk_test_abcdef12345'))
    def test_topic_updates(self):
        self.login();self.assertEqual(self.post('/api/topics',{'topics':['New question','New question']}).status_code,200)
        self.assertEqual(json.loads((self.root/'topics.json').read_text()),['New question'])
    def test_manual_production_ignores_automatic_flag_and_becomes_draft(self):
        self.login();r=self.post('/api/videos',{'topic':'Why caches expire'});eid=r.json['id']
        conn=d.database();job=conn.execute('SELECT * FROM dashboard_jobs').fetchone()
        def started(*args,**kwargs):
            (self.root/'output'/eid/'video.mp4').write_bytes(b'video');return MagicMock(pid=111,returncode=0,poll=MagicMock(return_value=0),wait=MagicMock(return_value=0))
        with patch.object(p,'generation_preflight'),patch.object(d.subprocess,'Popen',side_effect=started):
            self.assertTrue(d.produce(conn,job))
        self.assertEqual(conn.execute('SELECT status FROM episodes').fetchone()[0],'draft');conn.close()
    def test_publish_now_action_and_operation(self):
        self.login()
        with d.closing(d.database()) as conn:
            with conn:
                conn.execute("INSERT INTO episodes(id,status,title,created_at,updated_at) VALUES('ep_now','draft','Publish Now Ep',?,?)", (p.utcnow(), p.utcnow()))
        r = self.post('/api/videos/ep_now/publish-now', {})
        self.assertEqual(r.status_code, 202)
        with d.closing(d.database()) as conn:
            job = conn.execute("SELECT * FROM dashboard_jobs WHERE episode_id='ep_now'").fetchone()
            self.assertEqual(job['kind'], 'publish-now')
        r_op = self.post('/api/operations/publish-now', {})
        self.assertEqual(r_op.status_code, 202)

    def test_reject_video(self):
        self.login()
        with d.closing(d.database()) as conn:
            with conn:
                conn.execute("INSERT INTO episodes(id,status,title,created_at,updated_at) VALUES('ep1','draft','A Draft',?,?)", (p.utcnow(), p.utcnow()))
        r = self.post('/api/videos/ep1/reject', {'reason': 'Artifacts in scene 2'})
        self.assertEqual(r.status_code, 202)
        with d.closing(d.database()) as conn:
            job = conn.execute("SELECT * FROM dashboard_jobs WHERE episode_id='ep1'").fetchone()
            self.assertEqual(job['kind'], 'reject')
            payload = json.loads(job['payload'])
            self.assertEqual(payload['reason'], 'Artifacts in scene 2')
        with d.closing(d.database()) as conn:
            with conn:
                conn.execute("INSERT INTO episodes(id,status,title,slot,created_at,updated_at) VALUES('ep2','ready','Ready Ep','2026-09-22-1200',?,?)", (p.utcnow(), p.utcnow()))
        r = self.post('/api/videos/ep2/reject', {'reason': 'Cannot reject slotted'})
        self.assertEqual(r.status_code, 400)
    def test_session_log_parsed_and_redacted(self):
        self.login()
        (self.root/'.env').write_text('ELEVEN_LABS_KEY=sk_secret_eleven12345\n')
        folder = self.root / 'output/ep-log'
        folder.mkdir()
        with d.closing(d.database()) as conn:
            with conn:
                conn.execute("INSERT INTO episodes(id,status,title,created_at,updated_at) VALUES('ep-log','draft','Log Ep',?,?)", (p.utcnow(), p.utcnow()))
        log_lines = [
            json.dumps({"type": "step_start", "timestamp": 1000}),
            json.dumps({"type": "tool_use", "timestamp": 1050, "part": {"tool": "bash", "state": {"status": "completed", "input": {"command": "echo sk_secret_eleven12345"}, "output": "output sk_secret_eleven12345", "time": {"start": 1050, "end": 1100}}}}),
            json.dumps({"type": "tool_use", "timestamp": 1200, "part": {"tool": "todowrite", "state": {"status": "completed", "input": {"todos": [{"content": "Task 1", "status": "completed", "priority": "high"}]}}}}),
            json.dumps({"type": "tool_use", "timestamp": 1300, "part": {"tool": "read", "state": {"status": "error", "input": {"filePath": "test.txt"}, "error": "file not found sk_secret_eleven12345"}}}),
            json.dumps({"type": "step_finish", "timestamp": 1400, "part": {"tokens": {"total": 5000}, "cost": 0.025}}),
        ]
        (folder / 'session.jsonl').write_text("\n".join(log_lines) + "\n")
        r = self.client.get('/api/videos/ep-log')
        self.assertEqual(r.status_code, 200)
        data = r.json
        self.assertIn('session_log', data)
        slog = data['session_log']
        self.assertEqual(slog['summary']['total_tools'], 3)
        self.assertEqual(slog['summary']['tool_counts']['bash'], 1)
        self.assertEqual(slog['summary']['tool_counts']['todowrite'], 1)
        self.assertEqual(slog['summary']['tool_counts']['read'], 1)
        self.assertEqual(slog['summary']['errors_count'], 1)
        self.assertEqual(slog['summary']['total_tokens'], 5000)
        self.assertEqual(slog['summary']['total_cost'], 0.025)
        dumped = json.dumps(slog)
        self.assertNotIn('sk_secret_eleven12345', dumped)
        self.assertIn('[REDACTED]', dumped)

if __name__=='__main__':unittest.main()
