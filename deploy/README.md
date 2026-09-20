# Richard Studio deployment — u.trypitch.co

The app listens on **127.0.0.1:2021**. Cloudflare terminates HTTPS at
**https://u.trypitch.co** and forwards to that loopback address.

## Local use

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/dashboard.py setup
.venv/bin/python scripts/dashboard.py import-drafts
.venv/bin/python scripts/dashboard.py serve
# Separate terminal:
.venv/bin/python scripts/dashboard.py worker
```

Visit http://localhost:2021. The generated password is in
`secrets/dashboard-login.txt`. The server stores only its password hash and a
session signing key in `secrets/dashboard.json`; both files are private and
excluded from Git. Sessions expire after 12 hours. Login is rate-limited and
mutations require a session CSRF token. Media and documents require login.
Only named MP4/thumbnail/caption files are served, not arbitrary output HTML or
the workspace. Session log responses redact configured secrets.

## Moving the workspace to SSH host `mukund`

1. Stop generation/publishing on the old host and disable its Richard cron
   entries before enabling the new host. Stop the dashboard worker and any
   production child before copying. Copy `state/` consistently with SQLite's
   WAL files, or checkpoint/backup it while stopped. This is a **single-host
   queue**; never run the same workspace on both hosts simultaneously.
2. Copy project source, `output/`, `assets/`, `state/`, `.opencode/`, `.env` and
   `secrets/` privately to the destination. Exclude `.venv`, `node_modules` and
   platform-specific browser caches; recreate those on Linux. Do not copy
   environment directories from macOS and expect their executables to work.
3. Install Python 3.11+, FFmpeg/ffprobe, Node 22+, Bun, OpenCode and cloudflared.
   Sign in to the chosen OpenCode model provider on that host. The local
   `.opencode/skills/richard-system-design` is the production authority.
4. From the moved workspace:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python scripts/dashboard.py setup
   .venv/bin/python scripts/dashboard.py import-drafts
   .venv/bin/python scripts/configure_host.py
   ```

   `setup` preserves an existing dashboard login. `configure_host.py` updates
   `opencode_binary` for the new host and generates systemd units with the actual
   workspace, user and PATH. Review `deploy/generated/` before installation.
   The agent's relative `output/**` permission supports the moved project.
   Optional source references in Pitch/Instagram are local absolute paths;
   copy those references too or use the extracted workspace recipes without
   claiming unavailable source implementations were inspected.
5. Install the generated app and worker services (requires sudo):

   ```sh
   sudo install -m 644 deploy/generated/richard-dashboard.service /etc/systemd/system/
   sudo install -m 644 deploy/generated/richard-worker.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now richard-dashboard richard-worker
   .venv/bin/python scripts/pipeline.py install-cron
   ```

   Cron provides hourly buffer checks and five-minute publishing/archive checks.
   The persistent dashboard worker handles explicit user requests; automatic
   buffer flags do not disable manual creation. Both share the generation lock.

## Cloudflare token setup on the SSH host

1. In Cloudflare Zero Trust → Networks → Tunnels, create/select a remotely
   managed tunnel. Save **only its token** in `secrets/cloudflare-token.txt`
   with file permissions 600. Do not paste it into a command-line argument.
2. Add the public hostname route:

   | Field | Value |
   | --- | --- |
   | Subdomain | `u` |
   | Domain | `trypitch.co` |
   | Service type | HTTP |
   | Origin URL | `127.0.0.1:2021` |

   The Cloudflare hostname configuration must also create the tunnel DNS route.
   A tunnel connector token can run the connector; it cannot by itself create
   DNS/hostname routes through the account management API. Do not overwrite
   another service's hostname route. `cloudflare-ingress.yml` documents the
   equivalent ingress for a locally managed tunnel; token-managed tunnels use
   remote configuration, not that YAML.
3. Start the tunnel:

   ```sh
   sudo install -m 644 deploy/generated/richard-tunnel.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now richard-tunnel
   ```

   Or run `.venv/bin/python scripts/run_tunnel.py` directly for diagnosis.
   The runner uses cloudflared's `--token-file` and does not log the token.
4. Verify https://u.trypitch.co/healthz returns `ok: true`, then sign in at
   https://u.trypitch.co. The generated services enable Secure cookies. For
   direct localhost HTTP development, leave DASHBOARD_SECURE_COOKIE unset.
   Port 2021 need not be publicly exposed through the host firewall.

## Dashboard behavior

- **Create video:** topic and optional directions → persistent queued job →
  fresh OpenCode session using the workspace skill → draft for review.
- **Revision:** a fresh session reads the same folder, brief and QA plus feedback;
  it preserves reusable artifacts. This version does not resume an old chat ID.
- **Review:** play/download MP4, inspect captions, sources, QA, brief and a
  redacted tail of the session log. Existing local renders import as drafts.
- **Validate & queue:** runs the existing strict manifest/export checks. It
  cannot bypass missing review evidence. Approved-ready videos enter scheduled
  publishing; the button does not immediately upload them.
- **Automation:** edit the two daily times, timezone, target buffer, language,
  provider/model and activation flags. Provider credentials remain local files.
- **Recovery:** link an already-existing YouTube video after an uncertain upload,
  or finish thumbnail/visibility on a known ID. No blind duplicate insert.
- **Activity:** queued/running/completed/failed/interrupted commands with errors.
  Worker restart marks interrupted commands for inspection; it never silently
  repeats a possibly-running paid generation. Inspect a stuck `generating` job
  and its worker.json/process before using the CLI `fail` recovery command.

The app/worker are separate processes so six-hour renders do not block HTTP.
Queue state stays in SQLite; completed validated episodes use the existing
Supabase archive. Draft QA is never rewritten as passed simply to archive it.

Logs: `journalctl -u richard-dashboard -u richard-worker -u richard-tunnel`;
cron logs remain `state/buffer.log` and `state/publish.log`.
Tests: `.venv/bin/python -m unittest discover -s tests -v`.
