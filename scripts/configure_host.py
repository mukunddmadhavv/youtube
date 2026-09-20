"""Prepare this workspace after moving it to a Linux/systemd host.

Writes service units to deploy/generated; does not install or start them.
"""
import json
import os
from pathlib import Path
import pwd
import shutil
import sys
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--user',action='store_true',help='Generate user services without sudo')
options=parser.parse_args()

root=Path(__file__).resolve().parents[1]
binary=shutil.which('opencode')
if not binary: raise SystemExit('Install and sign in to OpenCode on this host first.')
config_path=root/'pipeline.json'
c=json.loads(config_path.read_text());c['opencode_binary']=binary
tmp=config_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(c,indent=2)+'\n');tmp.replace(config_path)
out=root/'deploy/generated';out.mkdir(parents=True,exist_ok=True)
user=pwd.getpwuid(os.getuid()).pw_name
python=root/'.venv/bin/python'
if not python.is_file(): raise SystemExit('Recreate .venv on this host before configuring services.')
def quote(value):
    return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'
for name,script,args in [('dashboard','dashboard.py','serve'),('worker','dashboard.py','worker'),('tunnel','run_tunnel.py','')]:
    content=f'''[Unit]
Description=Richard YouTube {name}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
{'' if options.user else 'User='+user}
WorkingDirectory={str(root).replace('%', '%%')}
Environment={quote('PATH='+os.environ['PATH'])}
Environment=DASHBOARD_HOST=127.0.0.1
Environment=DASHBOARD_SECURE_COOKIE=true
ExecStart={quote(python)} {quote(root/'scripts'/script)} {args}
Restart=on-failure
RestartSec=5
KillMode=control-group
TimeoutStopSec=30
UMask=0077

[Install]
WantedBy={'default.target' if options.user else 'multi-user.target'}
'''
    (out/f'richard-{name}.service').write_text(content)
print(f'Configured portable OpenCode path and generated three systemd units in {out}.')
print('Install dashboard + worker units now; install/start the tunnel unit after saving the token and hostname route.')
