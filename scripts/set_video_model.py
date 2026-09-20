"""Set the commissioned video model without replacing remote settings."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "scripts/pipeline.py"
source = path.read_text()
anchor = '    if c["model"]:\n        command += ["--model", c["model"]]\n'
addition = '    if c.get("variant"):\n        command += ["--variant", c["variant"]]\n'
if addition not in source:
    if source.count(anchor) != 1:
        raise SystemExit("Unexpected generation command; inspect before changing")
    path.write_text(source.replace(anchor, anchor + addition))

path = root / ".opencode/agents/richardSystemDesign.md"
source = path.read_text()
front, body = source[4:].split("---", 1)
lines = [line for line in front.splitlines() if not line.startswith(("model:", "variant:"))]
lines += ["model: google/gemini-3.8-flash", "variant: high"]
path.write_text("---\n" + "\n".join(lines) + "\n---" + body)

path = root / "pipeline.json"
config = json.loads(path.read_text())
config.update(model="google/gemini-3.8-flash", variant="high")
temporary = path.with_suffix(".json.tmp")
temporary.write_text(json.dumps(config, indent=2) + "\n")
temporary.replace(path)
print("Video sessions configured: google/gemini-3.8-flash --variant high")
