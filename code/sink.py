#!/usr/bin/env python3
# the spring: the water. A GPU dreams forever, and every basin drinks from it. Stop it, and the water stops.
#
# Each dream: a new prompt in the grammar of the Midjourney recipe (vanitas [flower, skull, soap bubble]), never the same
# words twice until all of them have been dreamed; dreamed out of the last dream, pulled back toward one of her vanitas
# images (her vanitas moodboard, source/moodboard/; her eight stills if it is missing) so the taste stays hers. On the way from
# one dream to the next the spring dreams three more places (waypoints, on a curve bent toward a third of her images), then
# glides through all of them on one smooth latent path (Catmull-Rom, the walk of the morph_v44 loop; the waypoints share the noise
# of the dream they lead to): forms melt and re-form instead of ghosting. Every frame is decoded from that path, graded once with the palette lock
# the sources were graded with (harmonize.py), and made 2560 x 1920 by Real-ESRGAN on the Neural Engine (upscale.py), with a
# 1280 x 960 copy for small screens. Frames are poured at an even pace into spring_feed/ (outside git) beside now.json; the
# basin pours whatever is newest.
#
# Midjourney, by hand: an image Kat makes on midjourney.com and downloads into source/mj_inbox/ becomes the next dream instead
# of one the spring would dream. The walk heads to it, it joins the taste, and the words shown are the prompt in its own
# metadata, before the first --parameter. The spring only reads that folder (Midjourney allows no automation, so nothing here
# calls it): it never moves, renames or deletes a file there, and spring_feed/state.json remembers which ones it has used.
#
#   caffeinate -i python3 code/sink.py        dream forever; veritas, the web basin, is at http://127.0.0.1:8770/
#   python3 code/sink.py --sheet 8            eight dreams on one contact sheet and one walk, timed, then stop
#   python3 code/sink.py --dry                serve veritas with no GPU: the water off
#   --public                                    and open it to everyone: a Cloudflare quick tunnel from this Mac (no account;
#                                               the address is printed, and changes each time); needs cloudflared
#   --lan                                       let the sink on the same network drink (binds 0.0.0.0)
#   --inbox DIR                                 take Midjourney images from DIR instead of source/mj_inbox/
# At vanitas, veritas runs with ?sink&camera&key=<spring_feed/key>. Touching the water never opens the camera: it has its own place on
# the glass, held for two seconds, and then looks once, for under a second. That one frame comes here as the omni reference for the next
# dream (the open-model way to do Midjourney's --oref): the face is found, made silver, used once, and never written to disk; the dream
# made from it goes to every basin.
import argparse, glob, hashlib, html, http.server, io, itertools, json, math, os, queue, random, re, secrets, sys, threading, time
from types import SimpleNamespace as Knot              # a place on the path: a latent, and the words shown on the way to it
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
FEED = os.path.join(ROOT, 'spring_feed')
PAGE = os.path.join(ROOT, 'verse', 'sync.html')
INBOX = os.path.join(ROOT, 'source', 'mj_inbox')
TASTE = [os.path.join(ROOT, 'source', 'moodboard', '*.webp'), os.path.join(ROOT, 'source', 'veritas', '*.png')]  # the first that has any
SHOWN = re.compile(r'^/feed/(now\.json|f\d{6}(?:_s)?\.jpg)$')   # all a basin may fetch: never the key, never state.json
W, H, STEPS, GUID = 640, 480, 10, 1.5                   # frame size; LCM steps of a dream; guidance
DREAM_S = (.34, .44)                                   # how hard a dream pulls toward its words: the subject just surfaces, barely clear (uncanny)
WORDS_MIX = (.08, .25)                                 # each dream's words lie between two prompts, the second a trace: a continuum, the first still names it
WP_F, WP_STR, WP_STEPS = (.25, .5, .75), (.40, .46, .40), 8   # waypoints: where on the way; how hard; steps
WP_STR_MJ = (.55, .5, .4)                               # heading to her own Midjourney picture: dream less near it, so it arrives
SEG = 12                                                # frames from one knot to the next: 48 a dream, about two minutes, so the
                                                        # change is just perceptible (you have to watch closely to see it move)
QMAX, PREROLL, CAD = 6, 3, (2.5, 3.5)                   # frames held for an even pace; held before the first; seconds a frame
MJ_EXT = ('.png', '.jpg', '.jpeg', '.webp')

CORE = ['flower', 'flower in bloom', 'peony', 'daisy', 'skull', 'soap bubble', 'a face, eyes closed', 'a face in profile']   # hers
NOTES = ['pearls', 'a moth', 'an hourglass', 'a glass bottle', 'smoke from a snuffed candle', 'hands under running water',   # at most one
         'a pocket watch', 'a cracked egg', 'a wilting tulip', 'an oyster shell', 'a butterfly', 'a feather', 'a glass of water',
         'a hand mirror', 'a seashell', 'a peeled lemon', 'falling petals', 'a dragonfly', 'melting ice', 'a bee', 'a lit candle',
         'a broken string of pearls', 'spilled wine', 'a snail', 'a burnt match', 'a key', 'a cut pomegranate', 'a sparrow',
         'a wristwatch', 'a fallen petal', 'a cracked mirror', 'a coin', 'a dried rose', 'a glass marble', 'a silk ribbon', 'a wasp nest']
MOODS = ['dissolving into light', 'blooming', 'about to burst', 'half erased', 'in a long exposure', 'melting slowly',
         'scattering into dust', 'reflected in glass', 'drifting apart', 'holding still', 'breathing in', 'caught in a current',
         'fading at the edges', 'rising like steam', 'under water', 'just before waking', 'unravelling', 'turning to glass',
         'coming into focus', 'in slow motion', 'frozen mid-air', 'cracking open', 'pooling', 'overflowing', 'surfacing',
         'losing its color', 'asleep', 'weightless']
LIGHT = ['', 'in moonlight', 'at first light', 'in a single shaft of light', 'backlit', 'in the dark', 'by candlelight',
         'in cold light', 'in silver light', 'through rain', 'in a mirror', 'at dusk', 'in the last light',
         'lit from below', 'in lamplight', 'in a long shadow', 'through frosted glass', 'by a window']        # often none
STYLE = ('silver gelatin photograph, hard light, crisp point cloud of white dots, a few tiny copper sparks, '
         'vertical glitch streaks, deep black background, high contrast, film grain')
NEG = ('text, watermark, signature, frame, border, grid, colorful, pastel, cartoon, illustration, painting, blurry, soft glow, haze, '
       'fog, blue tint, sepia, washed out, low contrast, deformed hands, extra fingers, gold ball')
GLASS = {'soap bubble': 'clear glass soap bubble'}       # her bubbles are clear glass with a few sparks; the model makes gold balls

def prompts(state):
    """Functionally endless prompts: three subjects (hers, at most one other vanitas object), in an order, a mood and sometimes a
    light. The space is walked by a stride that visits every prompt once, in a scrambled order, without storing it; the place in
    it survives a restart. At a dream every two minutes it would take years to come round (len_prompts() says how many)."""
    trios = [c for c in itertools.combinations(CORE + NOTES, 3) if sum(x in NOTES for x in c) <= 1
             and any(x in c for x in ('skull', 'soap bubble')) and any(x in c for x in CORE[:4] + ['skull'])]
    orders = list(itertools.permutations(range(3)))
    N = len(trios)*len(orders)*len(MOODS)*len(LIGHT)
    def stride(r):                                      # a step coprime to N: i -> (a*i + b) % N visits every index once
        a = r.randrange(N//3, N) | 1
        while math.gcd(a, N) != 1: a += 2
        return a, r.randrange(N)
    if 'stride' not in state:                           # each life draws its own walk from the machine's entropy, kept so a restart
        state['stride'] = stride(random.Random(state.get('life', 7)) if state.get('i') else random.SystemRandom())   # never repeats a prompt
    a, b = state['stride']
    while True:
        if state['i'] and state['i'] % N == 0:
            state['life'] = state.get('life', 7) + 1; state['stride'] = stride(random.SystemRandom()); a, b = state['stride']
        x = (a*(state['i'] % N) + b) % N; state['i'] += 1
        x, li = divmod(x, len(LIGHT)); x, mi = divmod(x, len(MOODS)); ti, oi = divmod(x, len(orders))
        c = [trios[ti][j] for j in orders[oi]]; m = MOODS[mi] + (' ' + LIGHT[li] if LIGHT[li] else '')
        yield f"vanitas [{', '.join(c)}], {m}", f"vanitas, {', '.join(GLASS.get(y, y) for y in c)}, {m}, {STYLE}"

def len_prompts():
    trios = [c for c in itertools.combinations(CORE + NOTES, 3) if sum(x in NOTES for x in c) <= 1
             and any(x in c for x in ('skull', 'soap bubble')) and any(x in c for x in CORE[:4] + ['skull'])]
    return len(trios)*6*len(MOODS)*len(LIGHT)

def mj_words(im):
    """The words of a Midjourney image, from its own metadata: the prompt before the first --parameter, or 'vanitas'."""
    text = im.info.get('Description') or ''                     # PNG: a tEXt chunk, 'prompt --params Job ID: <uuid>'
    if not text:
        try: text = im.getexif().get(270) or ''                 # JPEG, WebP: the EXIF image description
        except Exception: text = ''
    if not text:
        x = im.info.get('xmp') or im.info.get('XML:com.adobe.xmp') or ''
        if isinstance(x, bytes): x = x.decode('utf8', 'ignore')
        m = re.search(r'<dc:description>.*?<rdf:li[^>]*>(.*?)</rdf:li>', x, re.S)
        text = html.unescape(m.group(1)) if m else ''
    if isinstance(text, bytes): text = text.decode('utf8', 'ignore')
    w = ' '.join(str(text).split()).split(' Job ID: ')[0].split(' --')[0].strip()
    w = re.sub(r'^(\S*(https?://|s\.mj\.run/)\S*\s*)+', '', w).strip()    # image prompts lead with links; the basin shows words
    return w[:160] if w and not w.startswith('--') else 'vanitas'

def sd_prompt(words):
    """Midjourney's words in the dream's own grammar: vanitas [a, b] becomes vanitas, a, b, and the style."""
    w = re.sub(r'(\s*[,\[\]]\s*)+', ', ', words).strip(' ,') or 'vanitas'
    for a, b in GLASS.items(): w = w.replace(a, b)
    return w + ', ' + STYLE

class Inbox:
    """Kat's hand-made Midjourney images. Read only: never moved, renamed or deleted. Each picture is taken once, the oldest
    first, whatever its file is called; state.json remembers it (path: size, mtime, sha1), so a restart does not take it again."""
    def __init__(self, path, state, lock):
        self.path, self.state, self.lock, self.bad = path, state, lock, {}
        self.hashes = {u[2] for u in state.get('mj_used', {}).values() if len(u) > 2}
    def used(self, rp):
        return self.state.get('mj_used', {}).get(rp)
    def mark(self, rp, rec):
        with self.lock: self.state.setdefault('mj_used', {})[rp] = rec; self.hashes.add(rec[2])
    def next(self):
        from PIL import Image
        try: names = os.listdir(self.path)
        except OSError: return None
        now, waiting = time.time(), []
        for n in names:
            p = os.path.join(self.path, n)
            if n.startswith('.') or not n.lower().endswith(MJ_EXT): continue
            try: st = os.stat(p)
            except OSError: continue
            sig = [st.st_size, st.st_mtime_ns]
            if now - st.st_mtime < 2 or self.bad.get(p) == sig: continue     # still arriving, or unreadable as it stands
            u = self.used(os.path.realpath(p))
            if u and u[:2] == sig: continue
            waiting.append((st.st_mtime, n, p, sig))
        for _, n, p, sig in sorted(waiting):
            rp = os.path.realpath(p)
            try:
                data = open(p, 'rb').read(); h = hashlib.sha1(data).hexdigest()
                if h in self.hashes: self.mark(rp, sig + [h]); continue         # a picture already taken, under any name
                im = Image.open(io.BytesIO(data)); im.load(); words = mj_words(im); im = im.convert('RGB')
            except Exception: self.bad[p] = sig; continue
            self.mark(rp, sig + [h])
            return n, im, words, h
        return None

# ---- the feed: frames, and one small file that says what is newest
class Feed:
    def __init__(self, keep=60):
        os.makedirs(FEED, exist_ok=True); self.keep, self.seq, self.last, self.every, self.up = keep, 0, None, 2.0, None
        self.lock = threading.Lock()                    # the dreaming thread changes the state while the pouring thread saves it
        try: self.state = json.load(open(os.path.join(FEED, 'state.json')))
        except Exception: self.state = {'i': 0, 'life': 7}
        self.seq = self.state.get('seq', 0)
    def put(self, img, words): self.publish(self.prepare(img, words))
    def prepare(self, img, words):                  # the files first: the 4K frame and its small copy
        self.seq += 1; big, small = f'f{self.seq:06d}.jpg', f'f{self.seq:06d}_s.jpg'
        self.up.write(img, os.path.join(FEED, big), os.path.join(FEED, small))
        return self.seq, big, small, words
    def publish(self, rec):                         # then the one small file that says what is newest
        seq, big, small, words = rec; now = time.time()
        if self.last: self.every = 0.8*self.every + 0.2*(now - self.last)
        self.last = now
        self.last_now = {'t': now, 'seq': seq, 'frame': big, 'small': small, 'prompt': words, 'every': round(self.every, 2)}
        self.write('now.json', dict(self.last_now, tap=True))
        with self.lock: self.state['seq'] = seq; s = json.dumps(self.state)
        self.write('state.json', s)
        for old in (f'f{seq - self.keep:06d}.jpg', f'f{seq - self.keep:06d}_s.jpg'):
            if os.path.exists(os.path.join(FEED, old)): os.remove(os.path.join(FEED, old))
    def rest(self):                                 # the tap closed: say so at once, then make nothing until it opens
        if getattr(self, 'last_now', None): self.write('now.json', dict(self.last_now, tap=False, t=time.time()))
        while not TAP['on']: time.sleep(0.25)
        self.last = None
    def write(self, name, obj):
        tmp = os.path.join(FEED, '.' + name)
        with open(tmp, 'w') as f: f.write(obj if isinstance(obj, str) else json.dumps(obj))
        os.replace(tmp, os.path.join(FEED, name))

FACES = []                                          # at most one face waiting, in memory only
TAP = {'on': True}                                  # the sink's lever: down, generation stops, no data flows, and every basin drains
def face_key():
    os.makedirs(FEED, exist_ok=True); f = os.path.join(FEED, 'key')
    if not os.path.exists(f): open(f, 'w').write(secrets.token_urlsafe(18))
    return open(f).read().strip()

def serve(port, lan):
    key = face_key()
    class H(http.server.SimpleHTTPRequestHandler):
        def do_POST(self):                          # the sink's camera: one frame, with the key
            n = int(self.headers.get('Content-Length') or 0)
            path = self.path.split('?')[0]
            if path not in ('/feed/face', '/feed/tap') or not secrets.compare_digest(self.headers.get('X-Face-Key', ''), key) or not 0 < n < 3_000_000:
                self.send_response(403); self.end_headers(); return
            data = self.rfile.read(n)
            if path == '/feed/face': FACES[:] = [data]
            else: TAP['on'] = data.strip() != b'off'; TAP['changed'] = True
            self.send_response(204); self.end_headers()
        def do_OPTIONS(self):
            self.send_response(204); self.send_header('Access-Control-Allow-Methods', 'POST'); self.send_header('Access-Control-Allow-Headers', 'X-Face-Key'); self.end_headers()
        def translate_path(self, path):
            p = path.split('?')[0]
            if p in ('/', '/index.html', '/sync.html'): return PAGE
            m = SHOWN.match(p)
            return os.path.join(FEED, m.group(1)) if m else os.path.join(FEED, '__none__')
        def do_GET(self):
            if self.path == '/': self.send_response(302); self.send_header('Location', '/sync.html?spring'); self.end_headers(); return
            super().do_GET()
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Private-Network', 'true')
            p = self.path.split('?')[0]
            if p.endswith('.json'): self.send_header('Cache-Control', 'no-store')
            elif p.endswith('.jpg'): self.send_header('Cache-Control', 'public, max-age=86400, immutable')   # a frame never changes
            super().end_headers()
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(('0.0.0.0' if lan else '127.0.0.1', port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f'veritas: http://127.0.0.1:{port}/', flush=True)

def tunnel(port):
    """A Cloudflare quick tunnel from this Mac: veritas, public, for as long as the spring runs. Frames are not cached at the
    edge on a quick tunnel, so every viewer drinks from this Mac's upload."""
    import atexit, shutil, signal, subprocess
    exe = shutil.which('cloudflared') or os.path.expanduser('~/.local/bin/cloudflared')
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))   # a plain kill still closes the tunnel on the way out
    if not os.path.exists(exe): print('public: cloudflared not found, so veritas stays on this Mac', flush=True); return
    pr = subprocess.Popen([exe, 'tunnel', '--no-autoupdate', '--url', f'http://127.0.0.1:{port}'], stdout=subprocess.DEVNULL,
                          stderr=subprocess.PIPE, text=True)
    atexit.register(pr.terminate)
    def read():
        last = None
        for line in pr.stderr:                              # cloudflared repeats its address on every reconnect: point once per address
            m = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
            if m and m.group(0) != last: last = m.group(0); print(f'veritas, public: {last}/', flush=True); point(last + '/feed/')
    threading.Thread(target=read, daemon=True).start()

def point(feed):
    """Tell the public basin where the spring is now: verse/spring.json on the site, written through the GitHub API with this Mac's
    gh login, so the plain veritas address finds the water after every restart. Without gh, the address stays in the log."""
    import base64, shutil, subprocess
    gh = shutil.which('gh')
    if not gh or os.environ.get('SPRING_POINTER') == '0': return
    api, body = 'repos/kat-titter/vanitas-veritas/contents/verse/spring.json', json.dumps({'feed': feed}) + '\n'
    try:
        cur = subprocess.run([gh, 'api', api, '--jq', '.sha + " " + .content'], capture_output=True, text=True, timeout=30).stdout.split(' ', 1)
        sha = cur[0].strip() if cur and cur[0] else ''
        if len(cur) > 1 and base64.b64decode(cur[1].replace('\\n', '').strip() or b'').decode(errors='ignore') == body: print('public basin already points here', flush=True); return
        r = subprocess.run([gh, 'api', '-X', 'PUT', api, '-f', 'message=spring: where the water is now', '-f', 'content=' + base64.b64encode(body.encode()).decode()]
                           + (['-f', f'sha={sha}'] if sha else []), capture_output=True, text=True, timeout=30)
        print('public basin points here' if r.returncode == 0 else f'public basin: could not point here ({r.stderr.strip()[:120]})', flush=True)
    except Exception as e: print(f'public basin: could not point here ({e})', flush=True)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--sheet', type=int, default=0)
    ap.add_argument('--out', default=''); ap.add_argument('--inbox', default='')
    ap.add_argument('--dry', action='store_true'); ap.add_argument('--lan', action='store_true'); ap.add_argument('--port', type=int, default=8770)
    ap.add_argument('--public', action='store_true')
    a = ap.parse_args()
    if not a.sheet: serve(a.port, a.lan)
    if a.public and not a.sheet: tunnel(a.port)
    if a.dry:
        print('no GPU: the water is off', flush=True)
        while True: time.sleep(3600)

    t_wake = time.time()
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    import numpy as np, torch
    from PIL import Image
    from diffusers import StableDiffusionImg2ImgPipeline, LCMScheduler
    from harmonize import harmonize                 # the palette lock the sources were graded with
    from latent import slerp, catmull, Vae          # the curves of the walk, and the VAE's way in and out
    from upscale import Upscaler
    dev = 'mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained('stable-diffusion-v1-5/stable-diffusion-v1-5', torch_dtype=torch.float32,
                                                          safety_checker=None, requires_safety_checker=False)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights('latent-consistency/lcm-lora-sdv1-5', weight_name='pytorch_lora_weights.safetensors'); pipe.fuse_lora(); pipe.unload_lora_weights()
    if dev != 'cpu': pipe.unet.to(torch.float16); pipe.text_encoder.to(torch.float16)   # half the time for a dream; the VAE stays fp32 (fp16 decodes go black)
    pipe = pipe.to(dev)
    pipe.set_progress_bar_config(disable=True)     # no attention slicing: in fp16 on the Mac's GPU it turns a dream to NaN
    V = Vae(pipe.vae, dev); dec = V.dec

    def fill(im):                                   # crop to 4:3, never stretch
        im = im.convert('RGB'); w, h = im.size; s = max(W/w, H/h); im = im.resize((round(w*s), round(h*s)), Image.LANCZOS)
        l, t = (im.width - W)//2, (im.height - H)//2; return im.crop((l, t, l + W, t + H))
    def enc(im): return V.enc(fill(im))
    def along(win, s):                              # the point s knots past win[1] on the path through win
        m = min(int(s), len(win) - 4); return catmull(s - m, *win[m:m + 4])
    @torch.no_grad()
    def embed(prompt): return pipe.encode_prompt(prompt, dev, 1, True, NEG)
    E0, NE = embed(sd_prompt('vanitas'))            # the negative is the same for every dream
    def look(im):                                   # mean light, and how much of the picture is warm (R - B > 40)
        x = np.asarray(im.convert('RGB'), np.float32)
        return float((0.299*x[..., 0] + 0.587*x[..., 1] + 0.114*x[..., 2]).mean()), float(((x[..., 0] - x[..., 2]) > 40).mean())

    taste, taste_h, looks = [], {}, []              # her images as latents, ungraded; the grade comes once, when a frame is shown
    def add_taste(im, h):
        im = fill(im); taste_h[h] = len(taste); taste.append(enc(im)); looks.append(look(im)); return taste_h[h]
    for f in next((fs for fs in (sorted(glob.glob(g)) for g in TASTE) if fs), []):
        data = open(f, 'rb').read(); add_taste(Image.open(io.BytesIO(data)), hashlib.sha1(data).hexdigest())
    print(f'taste: {len(taste)} of her images', flush=True)
    feed = Feed(); words_of = prompts(feed.state); rng = random.SystemRandom()   # weights and picks from the machine's entropy: no two runs alike
    if not a.sheet:                                 # her Midjourney images from earlier runs stay in the taste
        for rp, u in list(feed.state.get('mj_used', {}).items())[-32:]:
            try:
                st = os.stat(rp)
                if u[2] not in taste_h and [st.st_size, st.st_mtime_ns] == u[:2]: add_taste(Image.open(rp), u[2])
            except Exception: pass
    import cv2
    finder = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    def face_of(data):                              # the largest face, with room round it, as a 4:3 picture; the middle if none is found
        im = Image.open(io.BytesIO(data)).convert('RGB'); a = np.asarray(im)
        f = finder.detectMultiScale(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY), 1.1, 5, minSize=(60, 60))
        if len(f):
            x, y, w, h = max(f, key=lambda b: b[2]*b[3]); cx, cy, hh = x + w/2, y + h*0.55, h*2.1
            im = im.crop((int(cx - hh*2/3), int(cy - hh/2), int(cx + hh*2/3), int(cy + hh/2)))
        return fill(im).convert('L').convert('RGB')  # silver: skin would turn the whole frame gold
    pending = []                                    # a face from the sink, encoded, waiting for its dream; in memory only
    def take_face():
        if FACES:
            data = FACES.pop()
            try: pending[:] = [enc(face_of(data))]
            except Exception: pass
        return pending[0] if pending else None
    drift = [0]                                     # dreams in a row whose light or warmth left the range of her images
    def watch(im):                                  # too dark, too bright, too gold or no copper at all: pull harder toward hers
        l, w = look(im)
        far = not (min(x[0] for x in looks) - 8 <= l <= max(x[0] for x in looks) + 8 and min(x[1] for x in looks) <= w <= max(x[1] for x in looks))
        drift[0] = drift[0] + 1 if far else 0; return l, w

    def seed_of(k): return secrets.randbits(62)    # a noise of its own for every dream, drawn fresh (one shared noise imprints one picture on all)
    def dream_lat(init, E, s, steps, seed):         # img2img in latent space: no encode on the way in, no decode on the way out
        g = torch.Generator(device=dev).manual_seed(seed)
        z = pipe(prompt_embeds=E, negative_prompt_embeds=NE, image=init, strength=s, num_inference_steps=steps,
                 guidance_scale=GUID, generator=g, output_type='latent').images.float()
        if dev == 'mps': torch.mps.empty_cache()
        if not torch.isfinite(z).all(): raise RuntimeError('a dream came out empty')   # never pour black water
        return z
    def keyframe(K, k, inbox=None):
        """Where the walk heads next: the face at the sink if one is waiting, else her newest Midjourney image, else a new dream."""
        ref = take_face()
        if ref is None and inbox is not None:
            got = inbox.next()
            if got:
                name, im, words, h = got
                pull = taste_h[h] if h in taste_h else add_taste(im, h)
                print(f'midjourney: {name}: {words}', flush=True)
                p = sd_prompt(words)
                return Knot(z=taste[pull], words=words, E=embed(p)[0], pull=pull, seed=seed_of(k), key=True, mj=True, prompt=p)
        with feed.lock: words, prompt = next(words_of); words2, prompt2 = next(words_of)
        mix = rng.uniform(*WORDS_MIX)                # between two prompts, at a weight of its own: the words never repeat
        pull, s = None, rng.uniform(*DREAM_S)
        if ref is not None:                         # someone at the sink: their face is the reference for this dream, once
            pending.clear()
            if 'a face' not in prompt: prompt = prompt.replace('vanitas, ', 'vanitas, a face, eyes closed, ', 1)
            words += ' --oref you'; init = slerp(rng.uniform(0.5, 0.65), K.z, ref); s = rng.uniform(0.52, 0.62)
        else:                                       # the last dream, pulled back toward one of hers; harder if the light has drifted
            pull = rng.randrange(len(taste))
            init = slerp(rng.uniform(0.5, 0.7) if drift[0] >= 3 else rng.uniform(0.35, 0.6), K.z, taste[pull])   # one of hers: a blend of two blurs
        E = torch.lerp(embed(prompt)[0], embed(prompt2)[0], mix)
        words = f"{words} ~ {words2.replace('vanitas ', '', 1)}"
        sd = seed_of(k); return Knot(z=dream_lat(init, E, s, STEPS, sd), words=words, E=E, pull=pull, seed=sd, key=True, mj=False, prompt=prompt)
    def detour(A, B, target=None):
        """The bend of the way from A to B: their middle, pulled toward a third of her images (or the face at the sink)."""
        j = None
        if target is None:
            j = rng.choice([i for i in range(len(taste)) if i not in (A.pull, B.pull)] or list(range(len(taste)))); target = taste[j]
        t = rng.uniform(0.2, 0.4); return slerp(t, slerp(0.5, A.z, B.z), target), t, j
    def waypoint(A, B, det, n):
        """A place on the way, dreamed: from the bent curve at WP_F[n], with the words halfway between and the noise of the dream ahead."""
        f = WP_F[n]; init = slerp(f, slerp(f, A.z, det), slerp(f, det, B.z))
        z = dream_lat(init, torch.lerp(A.E, B.E, f), (WP_STR_MJ if B.mj else WP_STR)[n], WP_STEPS, B.seed)
        return Knot(z=z, words=B.words, key=False, mj=False)
    k = feed.state['i']; pull0 = rng.randrange(len(taste))
    K0 = Knot(z=taste[pull0], words='vanitas', E=E0, pull=pull0, seed=seed_of(k - 1), key=True, mj=False, prompt=sd_prompt('vanitas'))
    print(f'awake in {time.time() - t_wake:.0f}s', flush=True)
    if a.sheet:
        out = a.out or FEED; os.makedirs(out, exist_ok=True); keys, tt = [K0], []
        for j in range(a.sheet):
            t0 = time.time(); keys.append(keyframe(keys[-1], k + j)); tt.append(time.time() - t0); l, w = look(dec(keys[-1].z))
            print(f'{tt[-1]:.1f}s  {keys[-1].words}   (light {l:.0f}, warm {w:.3f})', flush=True)
        print(f'hers: light {min(x[0] for x in looks):.0f} to {max(x[0] for x in looks):.0f}, warm {min(x[1] for x in looks):.3f} to '
              f'{max(x[1] for x in looks):.3f}, mean {sum(x[1] for x in looks)/len(looks):.3f}', flush=True)
        A, B = keys[0], keys[1]; det, tw, ws, dt, strip = detour(A, B)[0], [], [], [], []
        for n in range(3): t0 = time.time(); ws.append(waypoint(A, B, det, n).z); tw.append(time.time() - t0)
        after = waypoint(B, keys[2], detour(B, keys[2])[0], 0).z if len(keys) > 2 else B.z
        win = [A.z, A.z] + ws + [B.z, after]                # one walk, to judge the in-between: the first still to the first dream
        for i in range(4*SEG + 1): t0 = time.time(); strip.append(harmonize(dec(along(win, i/SEG)))); dt.append(time.time() - t0)
        every = (sum(tt)/len(tt) + sum(tw) + 4*SEG*sum(dt)/len(dt))/(4*SEG)
        print(f'waypoints {" ".join(f"{x:.1f}" for x in tw)}s, decode {sum(dt)/len(dt):.2f}s: {every:.2f}s a frame; light at the dream '
              f'{look(strip[-1])[0]:.0f}, the frame before {look(strip[-2])[0]:.0f}', flush=True)
        s = Image.new('RGB', (len(strip)*240, 180)); [s.paste(f.resize((240, 180)), (i*240, 0)) for i, f in enumerate(strip)]; s.save(os.path.join(out, 'walk.jpg'), quality=85)
        cols = 4; sh = Image.new('RGB', (cols*320, -(-a.sheet//cols)*240))
        for i, K in enumerate(keys[1:]): sh.paste(harmonize(dec(K.z)).resize((320, 240)), ((i % cols)*320, (i//cols)*240))
        sh.save(os.path.join(out, 'sheet.jpg'), quality=85); print(f'dream: {sum(tt)/len(tt):.1f}s on average; sheet in {out}', flush=True); return

    inbox = Inbox(os.path.abspath(a.inbox) if a.inbox else INBOX, feed.state, feed.lock); os.makedirs(inbox.path, exist_ok=True)
    feed.up = Upscaler()
    frames, ema = queue.Queue(QMAX), [2.3]            # ema: GPU seconds per frame, measured each dream
    def cadence(): return min(CAD[1], max(CAD[0], 1.05*ema[0]))
    def pour():                                     # one frame every cadence seconds, so the basin's crossfade ends as the next lands
        while frames.qsize() < PREROLL:
            if not TAP['on']: feed.rest()
            time.sleep(0.1)
        feed.last, feed.every, due = None, cadence(), 0.0
        while True:
            try:
                if not TAP['on']: feed.rest(); due = 0.0
                try: im, words = frames.get(timeout=0.25)
                except queue.Empty: continue
                rec = feed.prepare(harmonize(im), words)  # upscaled while the last frame is still on show
                while TAP['on'] and time.time() < due: time.sleep(min(0.1, max(0.0, due - time.time())))
                if not TAP['on']: feed.rest()
                feed.publish(rec); due = time.time() + cadence()
            except Exception as e: print(f'pour: {e}', flush=True); time.sleep(1)
    def wait_tap():
        while not TAP['on']: time.sleep(0.25)

    feed.every = CAD[1]                             # the first frames take ~18 s to come: a slow first beat keeps the basin from draining
    K = K0; feed.put(harmonize(dec(K.z)), 'vanitas'); print(f'the water is on; Midjourney images from {inbox.path}', flush=True)
    threading.Thread(target=pour, daemon=True).start()
    knots, seg, first, cycle, measured = [K], 0, True, 0, False   # knots in path order: ... w3, K, w1, w2, w3, K' ...; stretch seg: knots[seg] to [seg+1]
    while True:
        try:
            wait_tap(); t0 = time.time(); B = keyframe(K, k, inbox); k += 1; t_key = time.time() - t0; busy, made, seen = t_key, 0, None
            det = detour(K, B)[0]
            for n in range(3):
                wait_tap()
                if n == 1 and FACES:                    # someone at the sink just now: the face surfaces on the way, then gets its dream
                    ref = take_face()
                    if ref is not None: det = detour(K, B, ref)[0]
                t0 = time.time(); knots.append(waypoint(K, B, det, n)); busy += time.time() - t0
                if n == 2: knots.append(B)
                while len(knots) > seg + 2:             # a stretch is drawn once the knot after its end exists
                    win = [knots[max(seg - 1, 0)]] + knots[seg:seg + 3]
                    for i in range(SEG):
                        if first and i == 0: continue   # the first still was poured at once
                        wait_tap(); t0 = time.time(); im = dec(catmull(i/SEG, *[x.z for x in win])); busy += time.time() - t0
                        if i == 0 and win[1].key and not win[1].mj: seen = watch(im)
                        frames.put((im, (win[2] if i else win[1]).words)); made += 1
                    seg += 1; first = False
                    if dev == 'mps': torch.mps.empty_cache()
            d = max(seg - 1, 0); del knots[:d]; seg -= d
            if cycle and made and not B.mj:             # paced by dreamed stretches; her images cost no dream, and would pour too fast
                ema[0] = 0.6*ema[0] + 0.4*busy/made if measured else busy/made; measured = True
            cycle += 1
            lw = f'   last dream light {seen[0]:.0f}, warm {seen[1]:.3f}' if seen else ''
            if dev == 'mps': lw += f'   GPU memory {torch.mps.driver_allocated_memory()/2**30:.1f} GB'
            print(f'{t_key:.1f}s  {B.words}   {busy/max(made, 1):.2f}s a frame, pouring every {cadence():.2f}s{lw}', flush=True)
            K = B
        except Exception as e:                      # one GPU error must not stop the water: start again from the last dream
            print(f'the spring stumbled ({e!r}); on again from the last dream', flush=True)
            if dev == 'mps': torch.mps.empty_cache()
            time.sleep(1); knots, seg, first = [K], 0, True


if __name__ == '__main__':
    main()
