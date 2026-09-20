"""Persist OpenCode session IDs from JSON events and resume explicit sessions."""
import json
import re
import sqlite3
import subprocess
import threading
import time
import uuid

VALID = re.compile(r'^ses_[A-Za-z0-9_-]+$')


def connect(root):
    conn = sqlite3.connect(root / 'state/queue.sqlite3', timeout=30)
    conn.row_factory = sqlite3.Row
    conn.executescript('''
      CREATE TABLE IF NOT EXISTS episode_sessions (
        episode_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, updated_at REAL NOT NULL
      );
      CREATE TABLE IF NOT EXISTS session_runs (
        run_id TEXT PRIMARY KEY, episode_id TEXT NOT NULL, session_id TEXT,
        job_id TEXT, mode TEXT NOT NULL, started_at REAL NOT NULL, ended_at REAL,
        exit_code INTEGER
      );
    ''')
    return conn


def ids_from_lines(lines):
    for line in lines:
        try: event = json.loads(line)
        except (ValueError, TypeError): continue
        if not isinstance(event, dict): continue
        sid = event.get('sessionID') or event.get('session_id')
        if isinstance(sid, str) and VALID.fullmatch(sid): yield sid


def record(root, eid, sid, run_id=None):
    with connect(root) as conn:
        conn.execute('INSERT INTO episode_sessions VALUES(?,?,?) ON CONFLICT(episode_id) DO UPDATE SET session_id=excluded.session_id,updated_at=excluded.updated_at', (eid, sid, time.time()))
        if run_id: conn.execute('UPDATE session_runs SET session_id=? WHERE run_id=?', (sid, run_id))
    conn.close()


def recover(root, eid):
    with connect(root) as conn:
        row = conn.execute('SELECT session_id FROM episode_sessions WHERE episode_id=?', (eid,)).fetchone()
    conn.close()
    log = root / 'output' / eid / 'session.jsonl'
    latest = None
    if log.is_file() and log.resolve().is_relative_to((root / 'output' / eid).resolve()):
        with log.open(errors='replace') as stream:
            for sid in ids_from_lines(stream): latest = sid
    if latest:
        record(root, eid, latest)
        return latest
    return row['session_id'] if row else None


def details(root, eid):
    sid = recover(root, eid)
    with connect(root) as conn:
        runs = [dict(row) for row in conn.execute('SELECT * FROM session_runs WHERE episode_id=? ORDER BY started_at DESC', (eid,))]
    conn.close()
    return {'session_id': sid, 'session_runs': runs, 'resume_available': bool(sid)}


def resume_id(root, eid, binary):
    sid = recover(root, eid)
    if not sid: raise ValueError('No saved OpenCode session for this video. Create a new video explicitly; revision will not silently start fresh.')
    # List metadata instead of exporting a potentially very large conversation.
    result = subprocess.run([binary, 'session', 'list', '--format', 'json'], cwd=root, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError('Saved OpenCode session is unavailable on this host. Restore its OpenCode session data; no replacement session was created.')
    try:
        data = json.loads(result.stdout)
        actual = next((row.get('id') for row in data if isinstance(row,dict) and row.get('id')==sid),None)
    except (ValueError, AttributeError, TypeError): actual = None
    if actual != sid: raise ValueError('Could not verify saved OpenCode session; revision stopped without creating a new session.')
    return sid


def launch(root, eid, command, log, job_id=None):
    run_id = uuid.uuid4().hex
    sid = command[command.index('--session')+1] if '--session' in command else None
    with connect(root) as conn:
        conn.execute('INSERT INTO session_runs(run_id,episode_id,session_id,job_id,mode,started_at) VALUES(?,?,?,?,?,?)',
                     (run_id,eid,sid,job_id,'resume' if sid else 'new',time.time()))
    conn.close()
    log.flush()
    offset = log.tell()
    try:
        proc = subprocess.Popen(command,cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    except Exception:
        with connect(root) as conn: conn.execute('UPDATE session_runs SET ended_at=?,exit_code=-1 WHERE run_id=?',(time.time(),run_id))
        conn.close()
        raise
    def monitor():
        pending='';last=None
        with open(log.name,errors='replace') as stream:
            stream.seek(offset)
            while True:
                pending += stream.read()
                chunks=pending.split('\n');pending=chunks.pop()
                for found in ids_from_lines(chunks):
                    if found!=last: record(root,eid,found,run_id);last=found
                if proc.poll() is not None:
                    for found in ids_from_lines([pending]): record(root,eid,found,run_id)
                    break
                time.sleep(.25)
        with connect(root) as conn:
            conn.execute('UPDATE session_runs SET ended_at=?,exit_code=? WHERE run_id=?',(time.time(),proc.returncode,run_id))
        conn.close()
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    proc.session_monitor=thread
    return proc
