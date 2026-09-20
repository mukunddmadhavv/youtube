"""Run the remotely managed Cloudflare tunnel without putting its token in argv."""
import os
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[1]
token=root/'secrets/cloudflare-token.txt'
if not token.is_file() or not token.read_text().strip():
    raise SystemExit('Save your tunnel token in secrets/cloudflare-token.txt first.')
binary=shutil.which('cloudflared')
if not binary: raise SystemExit('Install cloudflared on this host first.')
token.chmod(0o600)
os.execv(binary,[binary,'tunnel','--no-autoupdate','run','--token-file',str(token)])
