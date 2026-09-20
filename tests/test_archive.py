"""Archive isolation, verified uploads and retry safety without remote writes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import supabase_archive as a
import pipeline as p


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.archive = a.Archive.__new__(a.Archive)
        self.archive.root = self.root
        self.archive.pipeline_id = "10d70d0c-3e12-45a7-b7a7-728cd3c242ba"
        self.file = self.root / "video.mp4"
        self.file.write_bytes(b"test video fixture")
        self.sha = hashlib.sha256(self.file.read_bytes()).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def response(self, status=200, body=None, content=b"test video fixture"):
        response = MagicMock(status_code=status, ok=200 <= status < 300)
        response.json.return_value = body
        response.iter_content.return_value = [content]
        return response

    def test_new_upload_is_private_namespaced_and_not_upserted(self):
        with patch.object(self.archive, "request", side_effect=[self.response(), self.response()]) as request:
            key = self.archive.upload("episode-one", "video.mp4", self.file, self.sha)
        self.assertTrue(key.startswith(self.archive.pipeline_id + "/episode-one/" + self.sha))
        self.assertEqual(request.call_args_list[0].kwargs["headers"]["x-upsert"], "false")
        self.assertIn("/richard-youtube/", request.call_args_list[0].args[1])
        self.assertIn("/authenticated/", request.call_args_list[1].args[1])

    def test_duplicate_upload_is_verified_without_overwrite(self):
        with patch.object(self.archive, "request", side_effect=[self.response(400, {"error": "Duplicate"}), self.response()]) as request:
            self.archive.upload("episode-one", "video.mp4", self.file, self.sha)
        self.assertEqual([call.args[0] for call in request.call_args_list], ["POST", "GET"])

    def test_duplicate_with_wrong_bytes_fails(self):
        with patch.object(self.archive, "request", side_effect=[self.response(409), self.response(content=b"different")]):
            with self.assertRaisesRegex(a.ArchiveError, "hash mismatch"):
                self.archive.upload("episode-one", "video.mp4", self.file, self.sha)

    def test_unauthorized_upload_does_not_try_to_overwrite(self):
        with patch.object(self.archive, "request", return_value=self.response(403)) as request:
            with self.assertRaisesRegex(a.ArchiveError, "403"):
                self.archive.upload("episode-one", "video.mp4", self.file, self.sha)
            self.assertEqual(request.call_count, 1)

    def test_metadata_only_sync_reuses_verified_objects_and_scopes_row(self):
        key = f"{self.archive.pipeline_id}/episode-one/{self.sha}/video.mp4"
        objects = {"video.mp4": {"key": key, "sha256": self.sha}}
        row = {"id": "episode-one", "topic_key": "topic", "title": "title", "status": "published",
               "youtube_id": "yt-id", "slot": "slot", "updated_at": "2026-09-21T00:00:00+00:00"}
        with patch.object(self.archive, "request", side_effect=[self.response(body=[{"objects": objects}]), self.response()]) as request, \
                patch.object(self.archive, "upload") as upload:
            self.archive.sync(row, {"title": "title"}, {"video.mp4": self.sha}, MagicMock())
            upload.assert_not_called()
        lookup = request.call_args_list[0]
        self.assertEqual(lookup.kwargs["params"]["pipeline_id"], "eq." + self.archive.pipeline_id)
        write = request.call_args_list[1]
        self.assertEqual(write.args[1], "/rest/v1/richard_youtube_episodes")
        self.assertEqual(write.kwargs["params"]["on_conflict"], "pipeline_id,episode_id")
        self.assertEqual(write.kwargs["json"]["youtube_id"], "yt-id")

    def test_failed_sync_has_no_receipt_and_retries(self):
        with patch.object(p, "ROOT", self.root):
            conn = p.db()
        with conn:
            conn.execute("INSERT INTO episodes(id,status,created_at,updated_at,hashes) VALUES(?,?,?,?,?)",
                         ("episode-one", "ready", "now", "now", json.dumps({"video.mp4": self.sha})))
        settings = {"enabled": True}
        remote = MagicMock()
        remote.sync.side_effect = [a.ArchiveError("network failure"), None]
        with patch.object(a, "Archive", return_value=remote):
            with self.assertRaises(a.ArchiveError):
                a.sync_queue(self.root, settings, conn, lambda row: {}, MagicMock())
            self.assertEqual(conn.execute("SELECT count(*) FROM archive_receipts").fetchone()[0], 0)
            a.sync_queue(self.root, settings, conn, lambda row: {}, MagicMock())
            a.sync_queue(self.root, settings, conn, lambda row: {}, MagicMock())
        self.assertEqual(remote.sync.call_count, 2)
        self.assertEqual(conn.execute("SELECT count(*) FROM archive_receipts").fetchone()[0], 1)
        conn.close()


class OAuthTest(unittest.TestCase):
    def test_existing_broad_scope_is_preserved_on_refresh(self):
        creds = MagicMock(expired=True, refresh_token="test", valid=True)
        creds.has_scopes.side_effect = lambda scopes: scopes == ["https://www.googleapis.com/auth/youtube"]
        with patch("google.oauth2.credentials.Credentials.from_authorized_user_file", return_value=creds) as load, \
                patch("google.auth.transport.requests.Request"), patch.object(p, "save_token") as save:
            self.assertIs(p.credentials(), creds)
            self.assertEqual(len(load.call_args.args), 1)
            creds.refresh.assert_called_once()
            save.assert_called_once_with(creds)


if __name__ == "__main__":
    unittest.main()
