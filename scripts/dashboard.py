#!/usr/bin/env python3
"""Richard Studio: authenticated dashboard, durable commands and media review."""
import argparse
from collections import defaultdict, deque
from contextlib import closing
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import time
import uuid

from flask import Flask, abort, jsonify, request, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash
import pipeline as p

ROOT = p.ROOT
STATIC = ROOT / "dashboard"
CONFIG_KEYS = {"generation_enabled", "publishing_enabled", "timezone", "publish_times",
               "buffer_target", "max_generations_per_run", "model", "language", "made_for_kids",
               "contains_synthetic_media", "auto_admit", "upload_thumbnails"}
MEDIA = {"video": "video.mp4", "thumbnail": "thumbnail.png", "captions": "subtitles.srt",
         "preview": "qa/preview-640.mp4"}
DOCS = {"brief": "BRIEF.md", "script": "script.md", "sources": "sources.md", "qa": "qa/report.md",
        "blocked": "BLOCKED.md", "description": "description.md"}


def database():
    conn = p.db()
    conn.executescript("""
      CREATE TABLE IF NOT EXISTS dashboard_jobs (
        id TEXT PRIMARY KEY, kind TEXT NOT NULL, episode_id TEXT, payload TEXT NOT NULL,
        status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, error TEXT
      );
    """)
    return conn


def setup():
    directory = ROOT / "secrets"
    directory.mkdir(exist_ok=True, mode=0o700)
    target = directory / "dashboard.json"
    if target.exists():
        print("Dashboard credentials already configured.")
        return
    password = secrets.token_urlsafe(24)
    data = {"secret_key": secrets.token_hex(32), "password_hash": generate_password_hash(password)}
    for path, content in ((target, json.dumps(data)), (directory / "dashboard-login.txt", f"Username: admin\nPassword: {password}\n")):
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as f:
            f.write(content)
    print("Dashboard login created in secrets/dashboard-login.txt (local file; not logged).")


def redact(text):
    # Provider logs can contain keys in model-generated commands. Redact actual
    # local credentials as well as common token/password forms before returning.
    from dotenv import dotenv_values
    values = []
    for path in (ROOT / ".env", ROOT / "secrets/supabase.env"):
        if path.exists():
            values += [v for k, v in dotenv_values(path).items() if v and any(x in k for x in ("KEY", "TOKEN", "PASSWORD", "DATABASE_URL", "DIRECT_URL"))]
    for name in ("youtube-token.json", "client_secret.json", "dashboard.json"):
        path = ROOT / "secrets" / name
        if path.exists():
            def collect(obj):
                for k, v in obj.items():
                    if isinstance(v, dict): collect(v)
                    elif isinstance(v, str) and any(x in k for x in ("secret", "token", "password")): values.append(v)
            collect(json.loads(path.read_text()))
    for value in values:
        if len(value) > 5: text = text.replace(value, "[REDACTED]")
    return re.sub(r"(?:sk_[A-Za-z0-9_-]+|Bearer\s+\S+|eyJ[A-Za-z0-9_.-]{30,}|postgres(?:ql)?://\S+)", "[REDACTED]", text)


def parse_session_log(folder):
    log = folder / "session.jsonl"
    if not log.is_file() or not log.resolve().is_relative_to(folder.resolve()):
        return None
    events = []
    tool_counts = {}
    errors_count = 0
    total_tokens = 0
    total_cost = 0.0
    start_time = None
    end_time = None
    raw_lines = []

    with log.open("r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f):
            raw_lines.append(line)
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
            except Exception:
                events.append({
                    "id": idx,
                    "type": "notice",
                    "text": redact(line_str),
                })
                continue

            ev_type = data.get("type")
            ts = data.get("timestamp")
            if ts:
                if start_time is None or ts < start_time:
                    start_time = ts
                if end_time is None or ts > end_time:
                    end_time = ts

            part = data.get("part", {})
            if ev_type == "tool_use":
                tool = part.get("tool", "unknown")
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
                state = part.get("state", {})
                status = state.get("status", "unknown")
                if status == "error":
                    errors_count += 1
                inp = state.get("input", {})
                out = state.get("output", "")
                err = state.get("error")

                summary = ""
                details = {}
                if tool == "bash":
                    summary = inp.get("command", "")
                    details["command"] = redact(inp.get("command", ""))
                    if "workdir" in inp:
                        details["workdir"] = inp["workdir"]
                elif tool == "read":
                    fp = inp.get("filePath", "")
                    summary = fp.split("/")[-1] if "/" in fp else fp
                    details["filePath"] = fp
                    if "offset" in inp:
                        details["offset"] = inp["offset"]
                    if "limit" in inp:
                        details["limit"] = inp["limit"]
                elif tool == "write":
                    fp = inp.get("filePath", "")
                    summary = fp.split("/")[-1] if "/" in fp else fp
                    details["filePath"] = fp
                    details["content"] = redact(str(inp.get("content", ""))[:3000])
                elif tool == "edit":
                    fp = inp.get("filePath", "")
                    summary = fp.split("/")[-1] if "/" in fp else fp
                    details["filePath"] = fp
                elif tool == "glob":
                    pattern = inp.get("pattern", "*")
                    target_path = inp.get("path")
                    summary = pattern + (f" in {target_path}" if target_path else "")
                    details["pattern"] = pattern
                    if target_path:
                        details["path"] = target_path
                elif tool == "todowrite":
                    todos = inp.get("todos", [])
                    done = sum(1 for t in todos if t.get("status") == "completed")
                    prog = sum(1 for t in todos if t.get("status") == "in_progress")
                    summary = f"{len(todos)} tasks ({done} done, {prog} active)"
                    details["todos"] = todos
                elif tool == "skill":
                    summary = inp.get("name", "")
                    details["name"] = summary
                elif tool == "webfetch":
                    summary = inp.get("url", "")
                    details["url"] = summary
                else:
                    summary = f"{tool} call"

                summary = redact(summary)
                if out:
                    details["output"] = redact(str(out)[:3000])
                if err:
                    details["error"] = redact(str(err))

                duration_ms = None
                t_info = state.get("time", {})
                if t_info.get("start") and t_info.get("end"):
                    duration_ms = t_info["end"] - t_info["start"]

                events.append({
                    "id": idx,
                    "type": "tool",
                    "tool": tool,
                    "status": status,
                    "summary": summary,
                    "details": details,
                    "timestamp": ts,
                    "duration_ms": duration_ms,
                })
            elif ev_type == "step_finish":
                toks = part.get("tokens", {})
                if toks.get("total"):
                    total_tokens = toks["total"]
                cost = part.get("cost", 0.0)
                if cost:
                    total_cost = round(total_cost + float(cost), 4)
                events.append({
                    "id": idx,
                    "type": "step_finish",
                    "tokens": toks,
                    "cost": cost,
                    "reason": part.get("reason"),
                    "timestamp": ts,
                })

    duration_sec = round((end_time - start_time) / 1000, 1) if (start_time and end_time) else None
    summary = {
        "total_events": len(events),
        "total_tools": sum(tool_counts.values()),
        "tool_counts": tool_counts,
        "errors_count": errors_count,
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 4),
        "duration_seconds": duration_sec,
    }
    raw_joined = "".join(raw_lines)
    raw_text = redact(raw_joined[-80000:] if len(raw_joined) > 80000 else raw_joined)
    return {"summary": summary, "events": events, "raw": raw_text}


def enqueue(conn, kind, eid=None, payload=None):
    jid = uuid.uuid4().hex
    with conn:
        if conn.execute("SELECT 1 FROM dashboard_jobs WHERE status IN ('queued','running') AND kind=? AND episode_id IS ?", (kind, eid)).fetchone():
            raise ValueError("This operation is already queued or running")
        conn.execute("INSERT INTO dashboard_jobs VALUES(?,?,?,?,?,?,?,NULL)",
                     (jid, kind, eid, json.dumps(payload or {}), "queued", p.utcnow(), p.utcnow()))
    return jid


def import_drafts():
    with closing(database()) as conn:
        for folder in (ROOT / "output").glob("*"):
            if not folder.is_dir() or not re.fullmatch(r"[a-z0-9-]+", folder.name): continue
            if not (folder / "video.mp4").is_file(): continue
            title = folder.name.replace("-", " ").title()
            with conn:
                conn.execute("INSERT OR IGNORE INTO episodes(id,status,title,created_at,updated_at) VALUES(?,?,?,?,?)",
                             (folder.name, "draft", title, p.utcnow(), p.utcnow()))


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    if test_config:
        app.config.update(test_config)
    else:
        auth = json.loads((ROOT / "secrets/dashboard.json").read_text())
        app.config.update(SECRET_KEY=auth["secret_key"], PASSWORD_HASH=auth["password_hash"])
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict",
                      SESSION_COOKIE_SECURE=os.getenv("DASHBOARD_SECURE_COOKIE", "false").lower() == "true",
                      MAX_CONTENT_LENGTH=32768, PERMANENT_SESSION_LIFETIME=43200)
    attempts = defaultdict(deque)

    @app.before_request
    def protect():
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            # No cross-origin form/JSON mutations, including login CSRF.
            origin = request.headers.get("Origin")
            allowed = {"http://localhost:2021", "http://127.0.0.1:2021", "https://u.trypitch.co"}
            if origin and origin not in allowed: abort(403)
            if not request.is_json: abort(415)
        if request.path.startswith(("/api/", "/media/")) and request.path != "/api/login":
            if not session.get("authenticated"): abort(401)
            if request.method == "POST" and not hmac.compare_digest(request.headers.get("X-CSRF-Token", ""), session.get("csrf", "missing")):
                abort(403)

    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    @app.errorhandler(Exception)
    def error(exc):
        from werkzeug.exceptions import HTTPException
        if isinstance(exc, HTTPException): return jsonify(error=exc.name), exc.code
        if isinstance(exc, (ValueError, KeyError, TypeError)): return jsonify(error=redact(str(exc))), 400
        app.logger.error("Dashboard operation failed: %s", type(exc).__name__)
        return jsonify(error="Operation failed; check the local service log."), 500

    @app.get("/")
    def index(): return send_file(STATIC / "index.html")

    @app.get("/static/<name>")
    def static(name):
        if name not in ("app.js", "style.css"): abort(404)
        return send_file(STATIC / name)

    @app.get("/healthz")
    def health(): return jsonify(ok=True, service="richard-studio")

    @app.post("/api/login")
    def login():
        key = request.remote_addr
        history = attempts[key]
        while history and history[0] < time.monotonic() - 300: history.popleft()
        if len(history) >= 10: abort(429)
        history.append(time.monotonic())
        password = request.get_json().get("password", "")
        if not isinstance(password, str) or not check_password_hash(app.config["PASSWORD_HASH"], password): abort(401)
        history.clear(); session.clear()
        session.update(authenticated=True, csrf=secrets.token_urlsafe(32)); session.permanent = True
        return jsonify(csrf=session["csrf"])

    @app.post("/api/logout")
    def logout(): session.clear(); return jsonify(ok=True)

    @app.get("/api/state")
    def state():
        with closing(database()) as conn:
            episodes = [dict(r) for r in conn.execute("SELECT id,status,title,created_at,updated_at,youtube_id,slot,error FROM episodes ORDER BY created_at DESC LIMIT 300")]
            jobs = [dict(r) for r in conn.execute("SELECT id,kind,episode_id,status,created_at,updated_at,error FROM dashboard_jobs ORDER BY created_at DESC LIMIT 50")]
        for row in episodes:
            folder=p.episode_dir(row["id"])
            row["media"]={k:f"/media/{row['id']}/{k}" for k,v in MEDIA.items() if (folder/v).is_file()}
        c=p.config()
        return jsonify(csrf=session["csrf"], episodes=episodes, jobs=jobs,
                       settings={k:c[k] for k in CONFIG_KEYS}, channel_id=c["channel_id"], playlist_id=c.get("playlist_id"),
                       archive_enabled=c.get("supabase_archive",{}).get("enabled",False),
                       worker=worker_status(), topics=json.loads((ROOT/"topics.json").read_text()))

    @app.post("/api/videos")
    def create_video():
        data=request.get_json(); topic=data.get("topic", ""); notes=data.get("notes", "")
        if not isinstance(topic,str) or not 3 <= len(topic.strip()) <= 300: raise ValueError("Topic must be 3–300 characters")
        if not isinstance(notes,str) or len(notes)>4000: raise ValueError("Notes must be under 4000 characters")
        eid="manual-"+uuid.uuid4().hex[:16]
        with closing(database()) as conn:
            with conn:
                conn.execute("INSERT INTO episodes(id,status,title,created_at,updated_at) VALUES(?,?,?,?,?)",(eid,"queued",topic.strip(),p.utcnow(),p.utcnow()))
            jid=enqueue(conn,"create",eid,{"topic":topic.strip(),"notes":notes})
        return jsonify(id=eid,job_id=jid),202

    @app.get("/api/videos/<eid>")
    def detail(eid):
        folder=p.episode_dir(eid)
        with closing(database()) as conn:
            row=conn.execute("SELECT id FROM episodes WHERE id=?",(eid,)).fetchone()
        if not row: abort(404)
        docs={}
        for kind,relative in DOCS.items():
            try: file=p.local_file(folder,relative)
            except ValueError: continue
            docs[kind]=redact(file.read_text()[:80000])
        parsed=parse_session_log(folder)
        legacy_log=parsed["raw"] if parsed else ""
        import session_tracking
        return jsonify(documents=docs,log=legacy_log,session_log=parsed,**session_tracking.details(ROOT,eid))

    @app.get("/media/<eid>/<kind>")
    def media(eid,kind):
        if kind not in MEDIA: abort(404)
        try: file=p.local_file(p.episode_dir(eid),MEDIA[kind])
        except ValueError: abort(404)
        return send_file(file,conditional=True,as_attachment=kind=="captions")

    @app.post("/api/videos/<eid>/<action>")
    def action(eid,action):
        if action not in ("validate","fail","reject","retry-finish","reconcile","revise","publish-now"): abort(404)
        with closing(database()) as conn:
            row=conn.execute("SELECT * FROM episodes WHERE id=?",(eid,)).fetchone()
            if not row: abort(404)
            data=request.get_json() or {}
            if action=="publish-now":
                if row["status"] == "published": raise ValueError(f"Episode {eid} is already published")
            if action=="revise":
                if row['status'] not in ('draft','failed') or row['slot']: raise ValueError("Only unassigned drafts/failed episodes can be revised")
                if not isinstance(data.get('notes'),str) or not 3<=len(data['notes'])<=4000: raise ValueError("Provide revision instructions")
                import session_tracking
                if not session_tracking.recover(ROOT,eid): raise ValueError('No saved session for this video; revision cannot silently create a new conversation')
                data={'notes':data['notes'],'topic':row['title']}
            elif action=='reconcile':
                if not re.fullmatch(r'[A-Za-z0-9_-]{11}',data.get('video_id','')): raise ValueError('Enter an 11-character YouTube video ID')
                data={'video_id':data['video_id']}
            elif action in ('fail','reject'):
                if row['slot'] and row['status'] not in ('uploading', 'blocked', 'failed'): raise ValueError("Cannot reject an episode with an assigned publishing slot")
                reason = data.get('reason', '') if isinstance(data, dict) else ''
                if not isinstance(reason, str) or len(reason) > 500: raise ValueError("Reason must be under 500 characters")
                data = {'reason': reason.strip()} if reason.strip() else {}
            else: data={}
            jid=enqueue(conn,action,eid,data)
        return jsonify(job_id=jid),202

    @app.post("/api/operations/<kind>")
    def operation(kind):
        if kind not in ('buffer','sync','publish','publish-now'): abort(404)
        with closing(database()) as conn: jid=enqueue(conn,kind)
        return jsonify(job_id=jid),202

    @app.post("/api/settings")
    def settings():
        changes=request.get_json()
        if not isinstance(changes,dict) or set(changes)-CONFIG_KEYS: raise ValueError('Unsupported settings')
        with p.lock('settings') as acquired:
            if not acquired: abort(409)
            c=p.config(); c.update(changes);p.validate_config(c)
            if not 1<=c['buffer_target']<=100 or not 1<=c['max_generations_per_run']<=10: raise ValueError('Buffer 1–100; generation batch 1–10')
            if not isinstance(c['model'],str) or len(c['model'])>200: raise ValueError('Invalid model')
            if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z]{2,4})?',c['language']): raise ValueError('Invalid language')
            p.dump(ROOT/'pipeline.json',c)
        return jsonify(ok=True)

    @app.post("/api/topics")
    def topics():
        values=request.get_json().get('topics')
        if not isinstance(values,list) or len(values)>200 or any(not isinstance(t,str) or not 3<=len(t.strip())<=300 for t in values): raise ValueError('Provide up to 200 topics, 3–300 characters each')
        p.dump(ROOT/'topics.json',list(dict.fromkeys(t.strip() for t in values)))
        return jsonify(ok=True)
    from voice_dashboard import voices
    app.register_blueprint(voices)
    return app


def worker_status():
    try:
        data=json.loads((ROOT/'state/dashboard-worker.json').read_text())
        return {'online':time.time()-data['heartbeat']<30,'pid':data['pid']}
    except (OSError,ValueError,KeyError): return {'online':False}


def produce(conn,job):
    c=p.config(); payload=json.loads(job['payload']);eid=job['episode_id']
    with p.lock(f'generation-{eid}') as acquired:
        if not acquired: return False
        if conn.execute("SELECT 1 FROM episodes WHERE id=? AND status='generating'",(eid,)).fetchone():
            raise ValueError(f'Episode {eid} is already generating')
        p.generation_preflight(c)
        import session_tracking
        saved_session = None
        if job['kind'] == 'revise':
            saved_session = session_tracking.resume_id(ROOT, eid, c['opencode_binary'])
        elif session_tracking.recover(ROOT, eid):
            try: saved_session = session_tracking.resume_id(ROOT, eid, c['opencode_binary'])
            except Exception: saved_session = None
        folder=p.episode_dir(eid);folder.mkdir(parents=True,exist_ok=True)
        p.dump(folder/'history.json',[dict(r) for r in conn.execute('SELECT id,title,topic_key,status FROM episodes WHERE id != ?',(eid,))])
        if job['kind']=='create':
            (folder/'BRIEF.md').write_text('---\nworkflow: richard-system-design\nflow: automation\nstoryboard: no\nmode: autonomous\n---\n\n'
                '# Dashboard commission\n\nTopic: '+payload['topic']+'\n\nOwner direction: '+payload.get('notes','')+
                '\n\nCreate a complete researched 3–8-minute 1920×1080 16:9 30fps Richard video. '
                'Use only the workspace Richard skill and its production lessons, animation and FFmpeg references. '
                'Use original local Richard assets and configured ElevenLabs voice. Render the actual MP4 and thumbnail. '
                'Keep all artifacts in this episode folder. Follow delivery.md; never invent completed QA. '
                'If a review capability is unavailable, deliver a draft and BLOCKED.md. Do not publish.\n'+
                f'Language: {c["language"]}. Character assets: {json.dumps(c["character_assets"])}\n')
        else:
            # Old approval/manifest must not certify changed output. Preserve it
            # as history while requiring the revision session to produce new QA.
            manifest=folder/'episode.json'
            if manifest.exists(): manifest.rename(folder/f"episode-before-{job['id']}.json")
            p.update(conn,eid,hashes=None)
        p.update(conn,eid,status='generating',error=None)
        command=p.generation_command(c,eid)
        if job['kind']=='revise':
            command[-1]=f"Revise the existing episode in output/{eid}/ using the workspace Richard skill and production-lessons.md. Read its BRIEF and QA first. Owner feedback: {payload['notes']}\nPreserve reusable assets/audio; rerender changed output and verify honestly. Do not publish or edit queue state."
        elif saved_session:
            command[-1]=f"Continue producing the complete Richard YouTube episode in output/{eid}/. Resume where the previous turn left off, finalize index.html and animation.js, render video.mp4, run the frame audit and full QA checks, and write episode.json."
        from voice_selection import instruction
        if job['kind']=='revise': command[-1] += instruction(eid)
        if saved_session: command[-1:-1] = ['--session', saved_session]
        with (folder/'session.jsonl').open('a') as log:
            proc=session_tracking.launch(ROOT,eid,command,log,job['id'])
            p.dump(folder/'worker.json',{'pid':proc.pid,'started_at':p.utcnow()})
            try: code=proc.wait(timeout=c['generation_timeout_seconds']); proc.session_monitor.join(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGTERM)
                try: proc.wait(timeout=15)
                except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                raise ValueError('Generation timed out; inspect the episode log')
        # Dashboard commissions always land in review. Validation is explicit,
        # and still requires the complete truthful QA manifest.
        if (folder/'video.mp4').is_file():
            has_manifest = (folder/'episode.json').is_file()
            err = None
            if code != 0: err = f'OpenCode exited {code}; review output and log'
            elif not has_manifest: err = 'Video produced, but QA manifest episode.json is missing; complete QA or revise before validating'
            p.update(conn,eid,status='draft',error=err)
        else:
            p.update(conn,eid,status='failed',error=f'No video produced; OpenCode exit {code}. Inspect BLOCKED.md/log.')
            raise ValueError('Production did not produce a video')
    return True


def run_job(conn,job):
    if job['kind'] in ('create','revise'): return produce(conn,job)
    # Prevent CLI contention from being reported as a completed UI operation.
    locks=['generation','publisher'] if job['kind'] in ('validate','fail','reject') else ['generation'] if job['kind']=='buffer' else ['publisher']
    from contextlib import ExitStack
    with ExitStack() as stack:
        if not all(stack.enter_context(p.lock(name)) for name in locks): return False
    args=[str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/pipeline.py'),job['kind']]
    if job['episode_id']: args.append(job['episode_id'])
    if job['kind']=='reconcile': args.append(json.loads(job['payload'])['video_id'])
    elif job['kind'] in ('fail','reject'):
        payload = json.loads(job['payload'] or '{}')
        if payload.get('reason'): args.append(payload['reason'])
    logpath=ROOT/'state'/f"dashboard-job-{job['id']}.log"
    with logpath.open('w') as log:
        result=subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=43200)
    if result.returncode: raise ValueError(redact(logpath.read_text()[-1500:]))
    return True


def worker():
    with p.lock('dashboard-worker') as acquired:
        if not acquired: raise ValueError('Dashboard worker already running')
        import threading

        with closing(database()) as conn:
            with conn:
                running_jobs = conn.execute("SELECT * FROM dashboard_jobs WHERE status='running'").fetchall()
                for rj in running_jobs:
                    eid = rj['episode_id']
                    worker_file = ROOT / f"output/{eid}/worker.json" if eid else None
                    is_alive = False
                    if worker_file and worker_file.is_file():
                        try:
                            wdata = json.loads(worker_file.read_text())
                            os.kill(wdata['pid'], 0)
                            is_alive = True
                        except (OSError, ValueError, KeyError): pass
                    if not is_alive:
                        conn.execute("UPDATE dashboard_jobs SET status='interrupted',error='Worker restarted; inspect running process before retrying',updated_at=? WHERE id=?", (p.utcnow(), rj['id']))

        def heartbeat():
            while True:
                p.dump(ROOT/'state/dashboard-worker.json',{'pid':os.getpid(),'heartbeat':time.time()});time.sleep(5)
        threading.Thread(target=heartbeat,daemon=True).start()

        active_jobs = {}

        def execute_job(job_id):
            with closing(database()) as thread_conn:
                job = thread_conn.execute("SELECT * FROM dashboard_jobs WHERE id=?", (job_id,)).fetchone()
                if not job: return
                try:
                    done = run_job(thread_conn, job)
                    status = 'completed' if done else 'queued'; error = None
                except Exception as exc:
                    status = 'failed'; error = redact(str(exc)) if isinstance(exc, ValueError) else f'{type(exc).__name__}: inspect local worker log'
                    if job['kind'] in ('create', 'revise'):
                        row = thread_conn.execute('SELECT status FROM episodes WHERE id=?', (job['episode_id'],)).fetchone()
                        if row and row['status'] != 'generating': p.update(thread_conn, job['episode_id'], status='failed', error=error)
                        elif row: p.update(thread_conn, job['episode_id'], error=error)
                with thread_conn:
                    thread_conn.execute('UPDATE dashboard_jobs SET status=?,error=?,updated_at=? WHERE id=?', (status, error, p.utcnow(), job_id))

        max_concurrent = int(os.getenv('DASHBOARD_MAX_CONCURRENT_JOBS', '4'))
        while True:
            # Prune finished threads
            for jid in list(active_jobs.keys()):
                if not active_jobs[jid].is_alive():
                    active_jobs.pop(jid, None)

            if len(active_jobs) < max_concurrent:
                with closing(database()) as conn:
                    queued_jobs = conn.execute("SELECT * FROM dashboard_jobs WHERE status='queued' ORDER BY created_at").fetchall()
                    for job in queued_jobs:
                        if len(active_jobs) >= max_concurrent:
                            break
                        eid = job['episode_id']
                        if eid and conn.execute("SELECT 1 FROM dashboard_jobs WHERE episode_id=? AND status='running' AND id!=?", (eid, job['id'])).fetchone():
                            continue
                        with conn:
                            conn.execute("UPDATE dashboard_jobs SET status='running',updated_at=? WHERE id=? AND status='queued'", (p.utcnow(), job['id']))
                        t = threading.Thread(target=execute_job, args=(job['id'],), daemon=True)
                        t.start()
                        active_jobs[job['id']] = t
            time.sleep(2)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['setup','serve','worker','import-drafts']);args=parser.parse_args()
    if args.command=='setup': setup()
    elif args.command=='worker': worker()
    elif args.command=='import-drafts': import_drafts();print('Local videos imported as drafts; no QA approval implied.')
    else:
        from waitress import serve
        serve(create_app(),host=os.getenv('DASHBOARD_HOST','127.0.0.1'),port=2021,threads=8)
