"""Build veritas.html: one file with its images inlined, so it opens from disk or a link.

    python3 davos_2027/build.py

Reads  video/veritas_loop_v45_4k.mp4   (gitignored): 24 stills taken evenly round the loop.
       If the loop is missing, falls back to the eight harmonized stills in source/harmonized/.
Writes davos_2027/veritas.html          (gitignored: it carries the images).
"""
import base64, glob, io, json, os, subprocess, sys, tempfile
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else 'veritas.src.html'      # python3 build.py [veritas2.src.html [veritas2.html]]
OUT = sys.argv[2] if len(sys.argv) > 2 else SRC.replace('.src.html', '.html')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOOP = os.path.join(ROOT, 'video', 'veritas_loop_v45_4k.mp4')
LOOP_SECONDS = 6080 / 12                   # frames / fps
POOL = 24                                  # stills taken round the loop
ORDER = [0, 1, 4, 3, 2, 7, 6, 5]           # fallback: same order as code/morph_v45_sr.py
SIZE = 1024                                # the basin is square; stills are centre-cropped to it


def encode(im):
    w, h = im.size
    s = min(w, h)
    im = im.convert('RGB').crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    buf = io.BytesIO()
    im.resize((SIZE, SIZE), Image.LANCZOS).save(buf, 'WEBP', quality=80, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode(), len(buf.getvalue())


frames, total = [], 0
if os.path.exists(LOOP):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(POOL):
            png = os.path.join(tmp, f'{k:02d}.png')
            subprocess.run([ff, '-y', '-loglevel', 'error', '-ss', f'{k * LOOP_SECONDS / POOL:.3f}',
                            '-i', LOOP, '-frames:v', '1', png], check=True)
            uri, n = encode(Image.open(png))
            frames.append(uri); total += n
    print(f'{POOL} stills from the loop, {total / 1e6:.2f} MB')
else:
    names = sorted(glob.glob(os.path.join(ROOT, 'source', 'veritas', '*.png')))
    for i in ORDER:
        base = os.path.basename(names[i])[:-4]
        uri, n = encode(Image.open(os.path.join(ROOT, 'source', 'harmonized', base + '_harmonized.png')))
        frames.append(uri); total += n
    print(f'loop not found: {len(frames)} harmonized stills, {total / 1e6:.2f} MB')

# the other plays' stills: smaller sets, in files beside the piece, loaded only when a play is near
SERIES = { 2: ('veritas_final_v44.mp4', 16, 800), 3: ('Vanitas_Veritas_basin_loop.mp4', 16, 640) }
if os.path.basename(OUT).startswith('veritas2'):
    import imageio_ffmpeg, re
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    for k, (name, pool, size) in SERIES.items():
        path = os.path.join(ROOT, 'video', name)
        if not os.path.exists(path): print(f'series {k}: {name} missing, skipped'); continue
        info = subprocess.run([ff, '-i', path], capture_output=True, text=True).stderr
        m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', info)
        dur = int(m[1])*3600 + int(m[2])*60 + float(m[3])
        uris, n_total = [], 0
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(pool):
                png = os.path.join(tmp, f'{i:02d}.png')
                subprocess.run([ff, '-y', '-loglevel', 'error', '-ss', f'{(i + 0.5) * dur / pool:.3f}', '-i', path, '-frames:v', '1', png], check=True)
                im = Image.open(png); w, h = im.size; sq = min(w, h)
                im = im.convert('RGB').crop(((w - sq) // 2, (h - sq) // 2, (w - sq) // 2 + sq, (h - sq) // 2 + sq))
                buf = io.BytesIO(); im.resize((size, size), Image.LANCZOS).save(buf, 'WEBP', quality=76, method=6)
                uris.append('data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()); n_total += len(buf.getvalue())
        out = os.path.join(HERE, f'veritas2.s{k}.js')
        open(out, 'w', encoding='utf-8').write(f'window.VERITAS_SERIES=window.VERITAS_SERIES||{{}};window.VERITAS_SERIES[{k}]={json.dumps(uris)};\n')
        print(f'series {k}: {pool} stills from {name}, {n_total / 1e6:.2f} MB -> {os.path.basename(out)}')

SRC = SRC if os.path.exists(SRC) else os.path.join(HERE, SRC)          # paths may be given from anywhere
OUT = OUT if os.path.isabs(OUT) or os.path.dirname(OUT) else os.path.join(HERE, OUT)
src = open(SRC, encoding='utf-8').read()
assert src.count('[/*FRAMES*/]') == 1
out = src.replace('[/*FRAMES*/]', json.dumps(frames))
open(OUT, 'w', encoding='utf-8').write(out)
print(f'{OUT}  {len(out) / 1e6:.2f} MB')
