"""Initialize Linux-only runtime dependencies after the workspace transfer."""
import json
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
runtime=root/'state/node-runtime'
runtime.mkdir(exist_ok=True)
subprocess.run(['npm','install','--prefix',str(runtime),'node@22'],check=True)
env=os.environ.copy()
env['PATH']=f"{runtime}/node_modules/.bin:{Path.home()}/.bun/bin:{Path.home()}/.opencode/bin:"+env['PATH']
subprocess.run([str(root/'.venv/bin/python'),str(root/'scripts/configure_host.py'),'--user'],env=env,check=True)
subprocess.run([str(root/'.venv/bin/python'),str(root/'scripts/pipeline.py'),'install-cron'],env=env,check=True)
episode=root/'output/jev-vs-llms'
subprocess.run(['npm','ci'],cwd=episode,env=env,check=True)
# Browser already installed on destination. A smoke probe checks its usability
# without deleting or changing shared Playwright browser caches.
subprocess.run([str(runtime/'node_modules/.bin/node'),'--input-type=module','-e',
    'import {chromium} from "playwright"; const b=await chromium.launch({executablePath:"/usr/bin/google-chrome",headless:true}); console.log("Linux browser launch verified."); await b.close();'],cwd=episode,env=env,check=True)
print('Linux runtime prepared. Provider authentication remains host-local.')
