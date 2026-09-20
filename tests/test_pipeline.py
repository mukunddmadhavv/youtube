"""Queue, scheduling, export admission and duplicate-upload regression tests.

No real API calls, paid generations or crontab changes.
"""

import copy
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

SPEC = importlib.util.spec_from_file_location("pipeline", Path(__file__).resolve().parents[1] / "scripts/pipeline.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)
REAL_ROOT = p.ROOT


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(p, "ROOT", Path(self.temp.name))
        self.root_patch.start()
        self.c = json.loads((REAL_ROOT / "pipeline.json").read_text())
        self.c.update(generation_enabled=True, publishing_enabled=True, channel_id="test-channel")
        self.c["supabase_archive"] = {"enabled": False}
        self.conn = p.db()
        self.db_patch = patch.object(p, "db", return_value=self.conn)
        self.db_patch.start()
        self.video_probe = {"format": {"duration": "240.0"}, "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080,
             "pix_fmt": "yuv420p", "avg_frame_rate": "30/1", "sample_aspect_ratio": "1:1"},
            {"codec_type": "audio", "codec_name": "aac"}]}

    def tearDown(self):
        self.db_patch.stop()
        self.conn.close()
        self.root_patch.stop()
        self.temp.cleanup()

    def fixture(self, eid="episode-one", topic="test-topic"):
        folder = p.episode_dir(eid)
        folder.mkdir(parents=True)
        data = {"topic_key": topic, "title": "How a test system works", "description": "A sourced explanation",
                "video": "video.mp4", "thumbnail": "thumbnail.png", "tags": ["system design"],
                "artifacts": {name: f"{name}.txt" for name in p.ARTIFACTS},
                "qa": {"status": "passed", "report": "qa/report.md", "checks": {
                    name: {"status": "passed", "evidence": f"qa/{name}.md"} for name in p.CHECKS}}}
        paths = [data["video"], data["thumbnail"], *data["artifacts"].values(), data["qa"]["report"],
                 *(check["evidence"] for check in data["qa"]["checks"].values())]
        for relative in paths:
            target = folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("Test-only artifact, not production evidence.")
        p.dump(folder / "episode.json", data)
        with self.conn:
            self.conn.execute("INSERT INTO episodes(id,status,created_at,updated_at) VALUES(?,?,?,?)",
                              (eid, "generating", p.utcnow(), p.utcnow()))
        return data

    def fake_probe(self, path):
        if path.name == "thumbnail.png":
            return {"streams": [{"width": 1280, "height": 720, "codec_name": "png"}]}
        return copy.deepcopy(self.video_probe)

    def ready(self, eid="episode-one", topic="test-topic"):
        data = self.fixture(eid, topic)
        with patch.object(p, "probe", side_effect=self.fake_probe):
            p.admit(self.conn, eid)
        return data

    def row(self, eid="episode-one"):
        return self.conn.execute("SELECT * FROM episodes WHERE id=?", (eid,)).fetchone()

    def test_timezone_window_and_no_catchup(self):
        # UTC 03:30 is 09:00 in Kolkata.
        self.assertIn("09:00:00+05:30", p.due_slot(self.c, datetime(2026, 9, 21, 3, 30, tzinfo=timezone.utc)))
        self.assertIsNone(p.due_slot(self.c, datetime(2026, 9, 21, 3, 29, tzinfo=timezone.utc)))
        self.assertIsNone(p.due_slot(self.c, datetime(2026, 9, 21, 4, 0, tzinfo=timezone.utc)))

    def test_midnight_grace_uses_previous_day(self):
        self.c.update(timezone="UTC", publish_times=["12:00", "23:50"])
        self.assertEqual(p.due_slot(self.c, datetime(2026, 9, 22, 0, 5, tzinfo=timezone.utc)),
                         "2026-09-21T23:50:00+00:00")

    def test_dst_repeated_hour_has_one_slot_key(self):
        self.c.update(timezone="America/New_York", publish_times=["01:00", "18:00"])
        first = p.due_slot(self.c, datetime(2026, 11, 1, 5, 5, tzinfo=timezone.utc))
        second = p.due_slot(self.c, datetime(2026, 11, 1, 6, 5, tzinfo=timezone.utc))
        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_artifact_path_escape_rejected(self):
        self.fixture()
        with self.assertRaises(ValueError):
            p.local_file(p.episode_dir("episode-one"), "../../state/queue.sqlite3")

    def test_admission_and_changed_manifest_rejected(self):
        self.ready()
        self.assertEqual(self.row()["status"], "ready")
        p.unchanged(self.row())
        (p.episode_dir("episode-one") / "episode.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "changed"):
            p.unchanged(self.row())

    def test_duplicate_topic_does_not_enter_buffer(self):
        self.ready()
        self.fixture("episode-two")
        with patch.object(p, "probe", side_effect=self.fake_probe), self.assertRaises(sqlite3.IntegrityError):
            p.admit(self.conn, "episode-two")
        self.assertEqual(self.row("episode-two")["status"], "generating")

    def test_export_duration_and_missing_audio_rejected(self):
        self.fixture()
        with patch.object(p, "probe", side_effect=self.fake_probe):
            for duration in ("179.9", "480.1", "nan"):
                self.video_probe["format"]["duration"] = duration
                with self.assertRaises(ValueError):
                    p.validate_files("episode-one")
            self.video_probe["format"]["duration"] = "240"
            self.video_probe["streams"].pop()
            with self.assertRaisesRegex(ValueError, "AAC"):
                p.validate_files("episode-one")

    def test_unverified_qa_rejected(self):
        data = self.fixture()
        data["qa"]["checks"]["full_listening"]["status"] = "not_verified"
        p.dump(p.episode_dir("episode-one") / "episode.json", data)
        with self.assertRaisesRegex(ValueError, "full_listening"):
            p.validate_files("episode-one")

    def test_new_generation_session_command(self):
        command = p.generation_command(self.c, "episode-one")
        self.assertNotIn("--continue", command)
        self.assertNotIn("--session", command)
        self.assertIn("richardSystemDesign", command)
        self.assertIn("--dir", command)

    def test_full_buffer_starts_no_session(self):
        self.ready()
        self.c["buffer_target"] = 1
        with patch.object(p, "generation_preflight"), patch.object(p.subprocess, "Popen") as process:
            p.generate(self.c)
            process.assert_not_called()

    def test_orphan_generation_is_not_duplicated(self):
        self.fixture()
        with patch.object(p, "generation_preflight"), patch.object(p.subprocess, "Popen") as process:
            with self.assertRaisesRegex(ValueError, "Unfinished"):
                p.generate(self.c)
            process.assert_not_called()

    def test_low_buffer_launches_bounded_distinct_sessions(self):
        p.dump(p.ROOT / "topics.json", ["A focused system-design question"])
        self.c.update(buffer_target=3, max_generations_per_run=2)
        worker = MagicMock(pid=12345,returncode=0,poll=MagicMock(return_value=0))
        worker.wait.return_value = 0

        def fake_admit(conn, eid):
            p.update(conn, eid, status="ready", topic_key=eid, title=eid)

        with patch.object(p, "generation_preflight"), patch.object(p, "admit", side_effect=fake_admit), \
                patch.object(p.subprocess, "Popen", return_value=worker) as process:
            p.generate(self.c)
            self.assertEqual(process.call_count, 2)
            rows = list(self.conn.execute("SELECT * FROM episodes"))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["status"] == "ready" for row in rows))
            self.assertNotEqual(rows[0]["id"], rows[1]["id"])
            p.generate(self.c)
            self.assertEqual(process.call_count, 3)
            self.assertEqual(self.conn.execute("SELECT count(*) FROM episodes WHERE status='ready'").fetchone()[0], 3)

    def test_successful_process_without_valid_manifest_stays_failed(self):
        p.dump(p.ROOT / "topics.json", ["A focused system-design question"])
        worker = MagicMock(pid=12345,returncode=0,poll=MagicMock(return_value=0))
        worker.wait.return_value = 0
        with patch.object(p, "generation_preflight"), \
                patch.object(p.subprocess, "Popen", return_value=worker):
            with self.assertRaises(ValueError):
                p.generate(self.c)
        rows = list(self.conn.execute("SELECT status FROM episodes"))
        self.assertEqual([r["status"] for r in rows], ["failed"])

    def test_generation_lock_prevents_overlap(self):
        with p.lock("generation") as first:
            self.assertTrue(first)
            with p.lock("generation") as second:
                self.assertFalse(second)

    def api(self):
        api = MagicMock()
        api.videos().insert().next_chunk.return_value = (None, {"id": "video-123"})
        api.videos().list().execute.return_value = {"items": [{
            "snippet": {"channelId": "test-channel"}, "status": {"privacyStatus": "public"}}]}
        return api

    def test_publish_twice_only_inserts_once(self):
        self.ready()
        api = self.api()
        api.videos().insert.reset_mock()
        with patch.object(p, "due_slot", return_value="test-slot"), patch.object(p, "youtube", return_value=api):
            p.publish(self.c)
            p.publish(self.c)
        self.assertEqual(api.videos().insert.call_count, 1)
        self.assertEqual(self.row()["status"], "published")

    def test_uncertain_insert_never_reinserts(self):
        self.ready()
        api = self.api()
        api.videos().insert().next_chunk.side_effect = ConnectionError("connection lost")
        api.videos().insert.reset_mock()
        with patch.object(p, "due_slot", return_value="test-slot"), patch.object(p, "youtube", return_value=api):
            with self.assertRaises(ConnectionError):
                p.publish(self.c)
            p.publish(self.c)
        self.assertEqual(api.videos().insert.call_count, 1)
        self.assertEqual(self.row()["status"], "uploading")

    def test_thumbnail_failure_retries_existing_id(self):
        self.ready()
        api = self.api()
        api.thumbnails().set().execute.side_effect = [ConnectionError("connection lost"), {}]
        api.videos().insert.reset_mock()
        with patch.object(p, "due_slot", return_value="test-slot"), patch.object(p, "youtube", return_value=api):
            with self.assertRaises(ConnectionError):
                p.publish(self.c)
            self.assertEqual(self.row()["status"], "uploaded")
            p.publish(self.c)
        self.assertEqual(api.videos().insert.call_count, 1)
        self.assertEqual(self.row()["status"], "published")

    def test_private_only_api_response_not_marked_published(self):
        self.ready()
        api = self.api()
        api.videos().list().execute.return_value["items"][0]["status"]["privacyStatus"] = "private"
        with patch.object(p, "due_slot", return_value="test-slot"), patch.object(p, "youtube", return_value=api):
            p.publish(self.c)
        self.assertEqual(self.row()["status"], "blocked")

    def test_playlist_existing_membership_does_not_insert_again(self):
        self.ready()
        api = self.api()
        api.playlistItems().list().execute.return_value = {"items": [{"id": "membership"}]}
        with patch.object(p, "due_slot", return_value="test-slot"), patch.object(p, "youtube", return_value=api):
            p.publish(self.c)
        api.playlistItems().insert.assert_not_called()

    def test_archive_failure_after_publication_never_reuploads(self):
        self.ready()
        api = self.api()
        api.videos().insert.reset_mock()
        with patch.object(p, "due_slot", return_value="test-slot"), patch.object(p, "youtube", return_value=api), \
                patch.object(p, "sync_archive", side_effect=[None, None, RuntimeError("archive offline"), None]):
            with self.assertRaises(RuntimeError):
                p.publish(self.c)
            self.assertEqual(self.row()["status"], "published")
            p.publish(self.c)
        self.assertEqual(api.videos().insert.call_count, 1)

    def test_disabled_commands_have_no_side_effects(self):
        self.c.update(generation_enabled=False, publishing_enabled=False)
        with patch.object(p, "generation_preflight") as preflight, patch.object(p, "youtube") as api:
            p.generate(self.c)
            p.publish(self.c)
            preflight.assert_not_called()
            api.assert_not_called()

    def test_cron_install_preserves_other_jobs(self):
        (p.ROOT / ".venv/bin").mkdir(parents=True)
        (p.ROOT / ".venv/bin/python").write_text("test")
        old = "MAILTO=owner@example.com\n15 2 * * * /bin/true\n"
        with patch.object(p.subprocess, "run") as run:
            run.return_value = MagicMock(returncode=0, stdout=old, stderr="")
            p.install_cron()
            installed = run.call_args.kwargs["input"]
            self.assertIn(old.strip(), installed)
            self.assertEqual(installed.count("# BEGIN richard-youtube"), 1)
            run.return_value = MagicMock(returncode=0, stdout=installed, stderr="")
            p.install_cron()
            self.assertEqual(run.call_args.kwargs["input"].count("# BEGIN richard-youtube"), 1)

    def test_reject_command(self):
        p.dump(p.ROOT / "pipeline.json", self.c)
        self.fixture("ep-rej", "reject-topic")
        with patch.object(p.sys, "argv", ["pipeline.py", "reject", "ep-rej", "Audio issue"]):
            self.assertEqual(p.main(), 0)
        row = self.conn.execute("SELECT status, error FROM episodes WHERE id='ep-rej'").fetchone()
        self.assertEqual(row["status"], "failed")
        self.assertEqual(row["error"], "Audio issue")


if __name__ == "__main__":
    unittest.main()
