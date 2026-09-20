"""Extract exported frames at 0,3,6,... seconds plus the last frame.

Produces timestamped contact sheets and an unreviewed audit manifest. Extraction
success is never a visual QA pass. Outputs are bound to the video's SHA-256.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess


def sample_times(duration, fps):
    if not math.isfinite(duration) or duration <= 0 or fps <= 0:
        raise ValueError('Positive duration and frame rate required')
    last = max(0, duration - 1 / fps)
    times = [float(t) for t in range(0, math.ceil(duration), 3) if t <= last]
    if not times or abs(times[-1] - last) > 1 / fps / 2:
        times.append(last)
    return times


def extract(video):
    from PIL import Image, ImageDraw
    video = video.resolve(strict=True)
    if video.suffix.lower() != '.mp4':
        raise ValueError('Provide the actual exported MP4')
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format',
                     '-show_streams', '-of', 'json', str(video)], text=True))
    stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
    duration = float(stream.get('duration') or info['format']['duration'])
    fps = float(Fraction(stream['avg_frame_rate']))
    with video.open('rb') as f:
        sha = hashlib.file_digest(f, 'sha256').hexdigest()
    folder = video.parent / 'qa' / 'frames-every-3s' / sha
    folder.mkdir(parents=True, exist_ok=True)
    frames = []
    for i, t in enumerate(sample_times(duration, fps)):
        name = f'frame-{i:04d}-{t:010.3f}s.png'
        target = folder / name
        # Decode accurately at the requested timestamp; omit -skip_frame/keyframe
        # shortcuts because they can silently move the inspection time.
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{t:.6f}',
                        '-i', str(video), '-map', '0:v:0', '-frames:v', '1',
                        '-update', '1', str(target)], check=True)
        if not target.is_file() or not target.stat().st_size:
            raise ValueError(f'No frame decoded at {t:.3f}s')
        frames.append({'id': f'F{i:04d}', 'requested_seconds': t, 'file': name,
                       'review_status': 'not_reviewed', 'findings': []})
    sheets = []
    for start in range(0, len(frames), 12):
        sheet = Image.new('RGB', (4 * 480, 3 * 302), '#e9ece6')
        draw = ImageDraw.Draw(sheet)
        for j, frame in enumerate(frames[start:start + 12]):
            x, y = j % 4 * 480, j // 4 * 302
            with Image.open(folder / frame['file']) as image:
                image = image.convert('RGB')
                image.thumbnail((480, 270))
                sheet.paste(image, (x + (480-image.width)//2, y))
            draw.text((x + 12, y + 280), f"{frame['id']} | {frame['requested_seconds']:.3f}s", fill='#17291c')
        name = f'sheet-{start//12+1:02d}.jpg'
        sheet.save(folder / name, quality=93)
        sheets.append(name)
    manifest = {'video': str(video), 'video_sha256': sha, 'duration': duration,
                'fps': fps, 'interval_seconds': 3, 'includes_final_frame': True,
                'status': 'not_reviewed', 'sheets': sheets, 'frames': frames,
                'animation_review': 'not_verified',
                'note': 'Every frame needs actual inspection. Stills cannot establish animation or audio synchronization.'}
    # Do not overwrite a reviewer's findings on a repeated extraction.
    path = folder / 'manifest.json'
    if not path.exists(): path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'frames': len(frames), 'sheets': len(sheets), 'directory': str(folder),
                      'status': 'extracted; visual and motion review required'}, indent=2))
    return folder


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    args = parser.parse_args()
    extract(args.video)
