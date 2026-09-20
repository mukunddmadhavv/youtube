"""Patch deployed entry points without replacing other remote dashboard changes."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/'scripts/dashboard.py';text=path.read_text()
if 'session_tracking.resume_id' not in text:
    anchor='        p.generation_preflight(c)\n'
    replacement=(anchor+"        import session_tracking\n"
                 "        saved_session = session_tracking.resume_id(ROOT,eid,c['opencode_binary']) if job['kind']=='revise' else None\n")
    assert text.count(anchor)==1
    text=text.replace(anchor,replacement)
    anchor="        with (folder/'session.jsonl').open('a') as log:\n"
    text=text.replace(anchor,"        if saved_session: command[-1:-1] = ['--session', saved_session]\n"+anchor)
    anchor='            proc=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)'
    assert text.count(anchor)==1
    text=text.replace(anchor,"            proc=session_tracking.launch(ROOT,eid,command,log,job['id'])")
    anchor="            try: code=proc.wait(timeout=c['generation_timeout_seconds'])"
    text=text.replace(anchor,anchor+"; proc.session_monitor.join(timeout=5)")
    anchor="                data={'notes':data['notes'],'topic':row['title']}"
    assert text.count(anchor)==1
    text=text.replace(anchor,"                import session_tracking\n                if not session_tracking.recover(ROOT,eid): raise ValueError('No saved session for this video; revision cannot silently create a new conversation')\n"+anchor)
    anchor='        return jsonify(documents=docs,log=legacy_log,session_log=parsed)'
    assert text.count(anchor)==1
    text=text.replace(anchor,'        import session_tracking\n        return jsonify(documents=docs,log=legacy_log,session_log=parsed,**session_tracking.details(ROOT,eid))')
    compile(text,str(path),'exec');path.write_text(text)
path=root/'scripts/pipeline.py';text=path.read_text()
if 'session_tracking.launch' not in text:
    anchor='                    proc = subprocess.Popen(generation_command(c, episode_id), cwd=ROOT,\n                                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)'
    # Preserve surrounding formatting from the deployed file.
    import re
    pattern=r'(?m)^(\s*)proc = subprocess\.Popen\(generation_command\(c, episode_id\), cwd=ROOT,\s*stdout=log, stderr=subprocess.STDOUT, start_new_session=True\)'
    text,count=re.subn(pattern,lambda m:m[1]+'import session_tracking\n'+m[1]+'proc = session_tracking.launch(ROOT, episode_id, generation_command(c, episode_id), log)',text)
    assert count==1,'Unexpected automatic generation launcher'
    anchor='                        code = proc.wait(timeout=c["generation_timeout_seconds"])'
    assert anchor in text
    text=text.replace(anchor,anchor+'\n                        proc.session_monitor.join(timeout=5)')
    compile(text,str(path),'exec');path.write_text(text)
path=root/'dashboard/index.html';text=path.read_text()
if 'id="saved-session"' not in text:
    text=text.replace('<div id="detail-media">','<p id="saved-session" class="muted"></p><div id="detail-media">')
text=text.replace('>Start revision</button>','>Resume session & revise</button>')
path.write_text(text)
path=root/'dashboard/app.js';text=path.read_text()
anchor="  $('#detail-title').textContent=v.title||id;"
if "$('#saved-session').textContent" not in text:
    assert text.count(anchor)==1,'Unexpected detail UI'
    text=text.replace(anchor,anchor+"\n  $('#saved-session').textContent=data.session_id ? `OpenCode session: ${data.session_id} · ${data.session_runs.length} tracked runs` : 'No saved OpenCode session. Same-session revision unavailable.';\n  $('#revision-form button').disabled=!data.resume_available;")
path.write_text(text)
print('Session tracking, exact-session revisions and visible session IDs installed.')
