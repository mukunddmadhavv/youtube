"""Isolated immutable artifact storage and owned-row metadata synchronization."""
import hashlib
import json
import mimetypes
import re
from urllib.parse import quote
from uuid import UUID

from dotenv import dotenv_values
import requests

BUCKET = "richard-youtube"
TABLE = "richard_youtube_episodes"


class ArchiveError(RuntimeError):
    pass


class Archive:
    def __init__(self, root, settings):
        self.root = root
        self.pipeline_id = str(UUID(settings["pipeline_id"]))
        env = dotenv_values(root / "secrets/supabase.env")
        self.url = env["SUPABASE_URL"].rstrip("/")
        if not self.url.startswith("https://"):
            raise ArchiveError("Supabase requires HTTPS")
        self.headers = {"apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
                        "Authorization": "Bearer " + env["SUPABASE_SERVICE_ROLE_KEY"]}

    def request(self, method, path, **kwargs):
        headers = {**self.headers, **kwargs.pop("headers", {})}
        try:
            response = requests.request(method, self.url + path, headers=headers,
                                        timeout=(30, 600), **kwargs)
        except requests.RequestException:
            raise ArchiveError("Supabase connection failed; retry sync") from None
        return response

    @staticmethod
    def require(response, operation):
        if not response.ok:
            raise ArchiveError(f"Supabase {operation} failed (HTTP {response.status_code})")

    def verify_object(self, key, expected):
        response = self.request("GET", f"/storage/v1/object/authenticated/{BUCKET}/{quote(key, safe='/')}", stream=True)
        try:
            self.require(response, "object verification")
            h = hashlib.sha256()
            for chunk in response.iter_content(1024 * 1024):
                h.update(chunk)
            if h.hexdigest() != expected:
                raise ArchiveError("Remote artifact hash mismatch; existing object preserved")
        finally:
            response.close()

    def upload(self, episode_id, relative, path, expected):
        if not re.fullmatch(r"[a-z0-9-]+", episode_id):
            raise ArchiveError("Invalid episode ID")
        key = f"{self.pipeline_id}/{episode_id}/{expected}/{relative}"
        with path.open("rb") as stream:
            response = self.request("POST", f"/storage/v1/object/{BUCKET}/{quote(key, safe='/')}",
                                    headers={"Content-Type": mimetypes.guess_type(relative)[0] or "application/octet-stream",
                                             "x-upsert": "false"}, data=stream)
        if not response.ok:
            # Supabase versions return 400 or 409 for duplicate immutable objects.
            try:
                body = response.json()
            except ValueError:
                body = {}
            duplicate = response.status_code == 409 or (response.status_code == 400 and
                        (body.get("error") == "Duplicate" or str(body.get("statusCode")) == "409"))
            if not duplicate:
                self.require(response, "upload")
        # Includes the ambiguous-upload retry case: never overwrite; verify bytes.
        self.verify_object(key, expected)
        return key

    def sync(self, row, manifest, hashes, local_file):
        folder = self.root / "output" / row["id"]
        response = self.request("GET", f"/rest/v1/{TABLE}", params={
            "pipeline_id": "eq." + self.pipeline_id, "episode_id": "eq." + row["id"],
            "select": "objects,source_updated_at"})
        self.require(response, "metadata lookup")
        existing = response.json()
        remote_objects = existing[0]["objects"] if existing else {}
        objects = {}
        for relative, expected in hashes.items():
            previous = remote_objects.get(relative, {})
            expected_key = f"{self.pipeline_id}/{row['id']}/{expected}/{relative}"
            if previous.get("sha256") == expected and previous.get("key") == expected_key:
                key = expected_key
            else:
                key = self.upload(row["id"], relative, local_file(folder, relative), expected)
            objects[relative] = {"key": key, "sha256": expected}
        record = {"pipeline_id": self.pipeline_id, "episode_id": row["id"],
                  "topic_key": row["topic_key"], "title": row["title"], "status": row["status"],
                  "youtube_id": row["youtube_id"], "publish_slot": row["slot"],
                  "bucket": BUCKET, "objects": objects, "manifest": manifest,
                  "source_updated_at": row["updated_at"]}
        response = self.request("POST", f"/rest/v1/{TABLE}",
                                params={"on_conflict": "pipeline_id,episode_id"},
                                headers={"Prefer": "resolution=merge-duplicates,return=minimal"}, json=record)
        self.require(response, "metadata sync")


def sync_queue(root, settings, conn, unchanged, local_file, only_id=None):
    if not settings.get("enabled", False):
        return
    archive = Archive(root, settings)
    rows = conn.execute("SELECT * FROM episodes WHERE hashes IS NOT NULL ORDER BY created_at").fetchall()
    for row in rows:
        if only_id and row["id"] != only_id:
            continue
        receipt = conn.execute("SELECT source_updated_at FROM archive_receipts WHERE episode_id=?", (row["id"],)).fetchone()
        if receipt and receipt[0] == row["updated_at"]:
            continue
        manifest = unchanged(row)
        archive.sync(row, manifest, json.loads(row["hashes"]), local_file)
        with conn:
            conn.execute("INSERT INTO archive_receipts(episode_id,source_updated_at) VALUES(?,?) "
                         "ON CONFLICT(episode_id) DO UPDATE SET source_updated_at=excluded.source_updated_at",
                         (row["id"], row["updated_at"]))


def bootstrap(root):
    """Run once, only for the new table and bucket; collision means stop."""
    import psycopg
    from check_connections import database_url
    env = dotenv_values(root / "secrets/supabase.env")
    with psycopg.connect(database_url(env), sslmode="require", connect_timeout=15, prepare_threshold=None) as conn:
        conn.execute("SET LOCAL lock_timeout = '5s'")
        conn.execute("SET LOCAL statement_timeout = '15s'")
        exists = conn.execute("SELECT to_regclass('public.richard_youtube_episodes') IS NOT NULL").fetchone()[0]
        if exists:
            marker = conn.execute("SELECT obj_description('public.richard_youtube_episodes'::regclass)").fetchone()[0]
            if marker != "Richard YouTube archive v1; isolated from existing application and Instagram records":
                raise ArchiveError("Table name collision; existing table preserved")
        else:
            conn.execute((root / "migrations/001_richard_youtube.sql").read_text())
    settings = json.loads((root / "pipeline.json").read_text())["supabase_archive"]
    archive = Archive(root, settings)
    response = archive.request("GET", f"/storage/v1/bucket/{BUCKET}")
    if response.ok:
        if response.json().get("public"):
            raise ArchiveError("Existing archive bucket is public; preserved for manual inspection")
    elif response.status_code in (400, 404):
        response = archive.request("POST", "/storage/v1/bucket", json={"id": BUCKET, "name": BUCKET, "public": False})
        archive.require(response, "new private bucket creation")
    else:
        archive.require(response, "bucket lookup")
    print("Richard table and private bucket provisioned; existing tables and buckets preserved.")


if __name__ == "__main__":
    from pathlib import Path
    try:
        bootstrap(Path(__file__).resolve().parents[1])
    except Exception as exc:
        print(f"Archive setup failed ({type(exc).__name__}); no destructive fallback attempted.")
        raise SystemExit(1)
