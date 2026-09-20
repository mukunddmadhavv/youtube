import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import session_tracking as s

class SessionTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'state').mkdir();self.folder=self.root/'output/example';self.folder.mkdir(parents=True)
    def tearDown(self): self.temp.cleanup()
    def test_recovery_uses_latest_explicit_id(self):
        (self.folder/'session.jsonl').write_text('noise\n'+json.dumps({'sessionID':'ses_original'})+'\n'+json.dumps({'sessionID':'ses_revision'})+'\n')
        self.assertEqual(s.recover(self.root,'example'),'ses_revision')
        (self.folder/'session.jsonl').unlink()
        self.assertEqual(s.recover(self.root,'example'),'ses_revision')
    def test_missing_session_stops_without_launch(self):
        with patch.object(s.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'No saved'): s.resume_id(self.root,'example','opencode')
            run.assert_not_called()
    def test_exact_id_lookup(self):
        s.record(self.root,'example','ses_saved')
        with patch.object(s.subprocess,'run',return_value=MagicMock(returncode=0,stdout='[{"id":"ses_saved"}]')) as run:
            self.assertEqual(s.resume_id(self.root,'example','opencode'),'ses_saved')
            self.assertEqual(run.call_args.args[0],['opencode','session','list','--format','json'])
    def test_wrong_or_deleted_session_stops(self):
        s.record(self.root,'example','ses_saved')
        for result in [MagicMock(returncode=1),MagicMock(returncode=0,stdout='{}')]:
            with patch.object(s.subprocess,'run',return_value=result):
                with self.assertRaises(ValueError):s.resume_id(self.root,'example','opencode')
    def test_live_event_persistence_and_run_history(self):
        with (self.folder/'session.jsonl').open('a') as log:
            proc=s.launch(self.root,'example',[sys.executable,'-c','import json; print(json.dumps({"sessionID":"ses_live"}),flush=True)'],log,'job-123')
            self.assertEqual(proc.wait(timeout=10),0);proc.session_monitor.join(timeout=5)
        data=s.details(self.root,'example')
        self.assertEqual(data['session_id'],'ses_live')
        self.assertEqual(data['session_runs'][0]['job_id'],'job-123')
        self.assertEqual(data['session_runs'][0]['exit_code'],0)
        self.assertEqual(data['session_runs'][0]['mode'],'new')
    def test_dashboard_revision_passes_saved_session(self):
        import dashboard as d
        import pipeline as p
        preset={'voice_id':'test','model_id':'test','voice_settings':{},'post_tempo':1.0}
        (self.root/'narration.json').write_text(json.dumps(preset))
        (self.folder/'BRIEF.md').write_text('Existing brief')
        (self.folder/'video.mp4').write_bytes(b'draft')
        c={'opencode_binary':'opencode','model':'google/gemini-3.8-flash','variant':'high','generation_timeout_seconds':20}
        with patch.object(p,'ROOT',self.root),patch.object(d,'ROOT',self.root),patch.object(p,'config',return_value=c),patch.object(p,'generation_preflight'):
            conn=d.database()
            conn.execute("INSERT INTO episodes(id,status,title,created_at,updated_at) VALUES('example','draft','Test','now','now')");conn.commit()
            job={'id':'revision-123','episode_id':'example','kind':'revise','payload':json.dumps({'notes':'Fix overlapping labels'})}
            proc=MagicMock(pid=123,returncode=0);proc.wait.return_value=0
            with patch.object(s,'resume_id',return_value='ses_saved'),patch.object(s,'launch',return_value=proc) as launch:
                self.assertTrue(d.produce(conn,job))
                command=launch.call_args.args[2]
                self.assertEqual(command[command.index('--session')+1],'ses_saved')
                self.assertIn('Fix overlapping labels',command[-1])
                self.assertNotIn('--continue',command)
            conn.close()

if __name__=='__main__':unittest.main()
