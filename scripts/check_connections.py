"""Read-only remote checks; secret values are never printed."""
import json
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from dotenv import dotenv_values
import psycopg
import requests
from googleapiclient.discovery import build
import pipeline


def database_url(env):
    parts = urlsplit(env["DATABASE_URL"])
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "pgbouncer"]
    return urlunsplit(parts._replace(query=urlencode(query)))


def main():
    env = dotenv_values(pipeline.ROOT / "secrets/supabase.env")
    try:
        api = build("youtube", "v3", credentials=pipeline.credentials(), cache_discovery=False)
        items = api.channels().list(part="id,snippet", mine=True).execute().get("items", [])
        print(json.dumps({"youtube_channels": [{"id": i["id"], "title": i["snippet"]["title"]} for i in items]}))
        playlists = api.playlists().list(part="id,snippet", mine=True, maxResults=50).execute().get("items", [])
        print(json.dumps({"playlists": [{"id": i["id"], "title": i["snippet"]["title"]} for i in playlists]}))
    except Exception as exc:
        print(json.dumps({"youtube_error_type": type(exc).__name__, "http_status": getattr(getattr(exc, "resp", None), "status", None)}))
    try:
        headers = {"apikey": env["SUPABASE_SERVICE_ROLE_KEY"], "Authorization": "Bearer " + env["SUPABASE_SERVICE_ROLE_KEY"]}
        response = requests.get(env["SUPABASE_URL"] + "/storage/v1/bucket", headers=headers, timeout=30)
        print(json.dumps({"storage_http_status": response.status_code, "buckets": [
            {k: item.get(k) for k in ("id", "public", "file_size_limit")} for item in response.json()
        ] if response.ok else []}))
        response = requests.get(env["SUPABASE_URL"] + "/rest/v1/richard_youtube_episodes",
                                headers=headers, params={"select": "episode_id", "limit": 1}, timeout=30)
        print(json.dumps({"archive_table_api_status": response.status_code,
                          "archive_has_episodes": bool(response.json()) if response.ok else None}))
    except Exception as exc:
        print(json.dumps({"storage_error_type": type(exc).__name__}))
    try:
        with psycopg.connect(database_url(env), sslmode="require", connect_timeout=15, prepare_threshold=None) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '10s'")
            rows = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name").fetchall()
            print(json.dumps({"public_tables": [row[0] for row in rows]}))
            print(json.dumps({"new_table_exists": conn.execute("SELECT to_regclass('public.richard_youtube_episodes') IS NOT NULL").fetchone()[0]}))
            if conn.execute("SELECT to_regclass('public.richard_youtube_episodes') IS NOT NULL").fetchone()[0]:
                row = conn.execute("SELECT relrowsecurity, "
                                   "has_table_privilege('anon', oid, 'SELECT'), "
                                   "has_table_privilege('authenticated', oid, 'SELECT'), "
                                   "has_table_privilege('service_role', oid, 'INSERT') "
                                   "FROM pg_class WHERE oid='public.richard_youtube_episodes'::regclass").fetchone()
                print(json.dumps(dict(zip(("archive_rls_enabled", "anon_can_select", "authenticated_can_select", "service_role_can_insert"), row))))
    except Exception as exc:
        print(json.dumps({"database_error_type": type(exc).__name__, "sqlstate": getattr(exc, "sqlstate", None)}))


if __name__ == "__main__":
    main()
