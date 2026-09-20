"""Recover the inspected orphan and commission repair with concrete frame findings."""
import json
import os
from pathlib import Path
import dashboard as d
import pipeline as p

eid='manual-21dfa91755ae4fa6'
folder=p.episode_dir(eid)
findings=[
    {'id':'N01','range':'0–9s','issue':'Device top geometry protrudes beyond card; excessive labels and unsupported zero-buffering wording need factual review.'},
    {'id':'N02','range':'12–21s','issue':'Multiple source/chunk/quality boxes stacked across the top with overlapping text; critical mechanism unreadable.'},
    {'id':'N03','range':'24–63s','issue':'Headings and multi-line labels exceed panel widths. Analogy mapping is crowded; split into sequential focused beats.'},
    {'id':'N04','range':'66–78s','issue':'Master ingest heading/fields overflow. Audit uncompressed/ProRes terminology and 400/420GB, 880Mbps, 40-hour numerical claims against sources.'},
    {'id':'N05','range':'81–99s','issue':'Chunk cards travel on top of title; codec cards collapse onto same position and text overlaps. Verify per-target transforms and independent labels.'},
    {'id':'N06','range':'102–123s','issue':'Bitrate bar/labels extend outside canvas; low/high complexity comparison has shifted boxes covering headings. Numbers need example/source context.'},
    {'id':'N07','range':'126–159s','issue':'Quality gauge/optimization badges overlap or escape panels; packaging and XML code are too dense/small. Review VMAF and saved-bitrate assertions.'},
    {'id':'N08','range':'162–216s','issue':'Packet drifts above endpoint, caching titles obscured, startup/buffer labels overlap, ladder items stack/move to incorrect positions. Remove unsourced guarantees (15ms, 180ms, zero stall, fixed 480p startup) or label justified examples.'},
    {'id':'N09','range':'219–255s','issue':'Throughput number and fallback card leave their containers; multiple overlapping headings. Verify buffer-driven action and claimed timing rather than universal rules.'},
    {'id':'N10','range':'258–287s','issue':'Cost cards overflow; Tens of Millions text spills across Richard and offscreen; recap cards/text collapse into one stack, including final frame.'}
]
for f in findings:f['status']='open';f['evidence']='qa/frames-every-3s/b6091da68d74d050b729b9def50db1368409b1061bc440cbfeb4e5fe1025e81a/'
notes=('Repair the Netflix video after owner-reported defects. Read qa/netflix-frame-review.md and qa/defects.json FIRST. '
       'Inspect all 9 original three-second contact sheets and selected full-resolution frames. '
       'Fix all listed defects throughout, not only the opener. Root causes appear to include SVG group transforms/stacking and text layout. '
       'Simplify crowded scenes, preserve causal motion, fix per-element transform ownership/initial states and validate all painted text bounds. '
       'Audit numerical/Netflix implementation claims; retain source-backed wording and label illustrative values. '
       'Preserve current audio when possible, but revise/re-align if factual corrections require it. '
       'Follow local references/full-video-frame-audit.md: after rerender extract one frame every 3 seconds plus last frame, inspect EVERY sheet, '
       'fix residual issues and repeat. Also inspect moving excerpts and all seams; do not substitute still extraction or DOM caption fit for visual QA. '
       'Write actual evidence in qa/report.md and defects.json. Keep draft if listening/temporal review unavailable. Do not publish.')
with p.lock('generation') as acquired:
    if not acquired:raise SystemExit('Generation lock held; repair not queued')
    worker=json.loads((folder/'worker.json').read_text())
    try:os.kill(worker['pid'],0)
    except ProcessLookupError:pass
    else:raise SystemExit('Prior worker PID still exists; inspect before recovery')
    conn=d.database()
    active=conn.execute("SELECT 1 FROM dashboard_jobs WHERE episode_id=? AND status IN ('running','queued')",(eid,)).fetchone()
    if active:raise SystemExit('Repair already active')
    p.dump(folder/'qa/defects.json',findings)
    (folder/'qa/netflix-frame-review.md').write_text(
        '# Full-export sampled-frame review\n\n'
        'Inspected all 9 contact sheets containing 97 sampled frames from 0 through 287.000s. '
        'Reviewer: assistant image inspection via Read tool. This establishes visible layout findings, not normal-speed playback or listening.\n\n'
        'Export SHA256: b6091da68d74d050b729b9def50db1368409b1061bc440cbfeb4e5fe1025e81a\n\n'
        + '\n'.join(f"- {f['id']} ({f['range']}): {f['issue']}" for f in findings)
        + '\n\nOverall sampled visual QA: FAILED. Repair and full re-extraction/review required.\n')
    row=conn.execute('SELECT status,slot FROM episodes WHERE id=?',(eid,)).fetchone()
    if row['slot']:raise SystemExit('Episode already assigned to publishing; inspect first')
    if row['status']=='generating':p.update(conn,eid,status='draft',error='Interrupted revision recovered after confirming worker exited; visual defects require repair.')
    jid=d.enqueue(conn,'revise',eid,{'topic':'Netflix System Design for streaming videos of different qualities','notes':notes})
    conn.close()
    print('Queued Netflix repair:',jid)
