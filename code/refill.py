#!/usr/bin/env python3
# the daily refill: one allocation of dream a day, for the hours no spring is awake. The reservoir veritas pours when the spring
# sleeps (?reservoir in verse/sync.html; filled by hand from a banked walk of the spring by verse/reservoir.py) is dreamed again
# here, on a CPU with no Mac near it: .github/workflows/refill.yml in the built-pages repo runs this once a day on a GitHub runner.
#
# The loop (--from): today's water is dreamed out of yesterday's. The spring keeps its taste by pulling every dream back toward one
# of Kat's own pictures; those stay private, so here yesterday's stored frames stand where her pictures stand: eight of them, the
# grade taken back off (ungrade), are the taste. Everything else is the spring's own, imported from code/sink.py (the prompt
# grammar, the sizes, the strengths, the waypoints), code/latent.py (the Catmull-Rom walk) and code/harmonize.py (the grade), so a
# change there changes the refill.
# Text only (no --from): every dream from its words alone, out of noise. A day also falls back to it when yesterday's water is
# missing, or fewer than three of its frames are still in the light and warmth of her pictures.
#
# One walk a day: --dreams new dreams, three waypoints on the way to each, --per frames a stretch; cut into --passages passages,
# which the page pours in a fresh order each visit. Each frame is graded once, enlarged plainly to --width (the spring's Real-ESRGAN
# would take about a minute a frame on a CPU) and packed the way verse/reservoir.py packs: a00.jpg ... and index.json, 6 MB at most.
# No face from the sink can be in it: there is no camera here, the omni reference (IP-Adapter) is never loaded, and a reservoir
# whose prompts carry --oref is never dreamed from.
#
#   python3 code/refill.py --from <yesterday's reservoir> --out <folder>     the loop
#   python3 code/refill.py --out <folder>                                    text only
#   --days N       a test: N days in a row, each out of the last, in <folder>/day01 ..., with drift.jpg and drift.jsonl
#   --selftest     no model: the grade and its undoing on a ramp; with --from, the look of that water
import argparse, datetime, json, math, os, pathlib, random, secrets, shutil, sys, time
from types import SimpleNamespace as Knot
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sink import prompts, sd_prompt, W, H, STEPS, GUID, DREAM_S, WORDS_MIX, WP_F, WP_STR, WP_STEPS, NEG
from harmonize import harmonize, COOL, GOLD_TONE, CONTRAST, BLACK_GAMMA, GAIN

HERS_LIGHT, HERS_WARM = (88.0, 157.7), (0.0039, 0.1214)   # the light and warmth of her eight moodboard pictures, by look() (measured
TASTE_N = 8                                               # 2026-11-17; the pictures themselves stay private). The spring leans on eight
LUM = np.array([0.299, 0.587, 0.114], np.float32)
T0 = time.time()
def say(*a): print(f'{time.time() - T0:7.1f}s ', *a, flush=True)

def look(im):                                           # mean light, and how much of the picture is warm: the spring's own measure
    x = np.asarray(im.convert('RGB'), np.float32)
    return float((x @ LUM).mean()), float(((x[..., 0] - x[..., 2]) > 40).mean())
def hers(l, w):                                         # inside the range of her pictures, as the spring's watch() reads it
    return HERS_LIGHT[0] - 8 <= l <= HERS_LIGHT[1] + 8 and HERS_WARM[0] <= w <= HERS_WARM[1]
def fill(im):                                           # crop to the dream's 4:3, never stretch
    im = im.convert('RGB'); s = max(W/im.width, H/im.height); im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    l, t = (im.width - W)//2, (im.height - H)//2; return im.crop((l, t, l + W, t + H))

def ungrade(im):
    """harmonize() taken back off a stored frame, so it can be dreamed from and graded once more without the grade piling up day
    on day: the S-curve and the black gamma run backwards, then the light the tint took is given back (red over blue says how
    much of a pixel was turned gold). The colour stays the grade's own; the light is the dream's again."""
    n = np.asarray(im.convert('RGB'), np.float32)/255
    lo, hi = 1/(1 + math.exp(2*CONTRAST)), 1/(1 + math.exp(-2*CONTRAST))      # what the S-curve makes of black, and of white
    n = np.clip((n/GAIN)**(1/BLACK_GAMMA), lo, hi)
    n = 0.5 + np.log(n/(1 - n))/(4*CONTRAST)
    c, g = np.array(COOL, np.float32), np.array(GOLD_TONE, np.float32)
    rho = n[..., 0]/np.maximum(n[..., 2], 1e-3)
    gold = np.clip((c[2]*rho - c[0])/((g[0] - c[0]) + (c[2] - g[2])*rho), 0, 1)[..., None]
    n = n/((1 - gold)*float(c @ LUM) + gold*float(g @ LUM))
    return Image.fromarray((np.clip(n, 0, 1)*255).round().astype(np.uint8))

def yesterday(src, rng):
    """Yesterday's water as today's taste: up to TASTE_N of its frames, ungraded, each still in the light and warmth of her
    pictures. None when there is no water to read, when it was dreamed with a face at the sink, or when fewer than three pass."""
    try:
        m = json.loads((src/'index.json').read_text()); names = [f for r in m['runs'] for f in r]
    except Exception as e: say(f'no water to dream from in {src} ({e!r})'); return None, None
    if any('--oref' in p for p in m.get('prompts', [])): say('that water was dreamed with a face at the sink: never dreamed from'); return None, None
    taste, seen = [], 0
    for f in rng.sample(names, len(names)):
        im = ungrade(fill(Image.open(src/f))); l, w = look(im); seen += 1
        if hers(l, w): taste.append(Knot(name=f, im=im, light=l, warm=w))
        if len(taste) == TASTE_N: break
    say(f'yesterday ({m.get("made")}): {len(taste)} of {seen} frames looked at are in her light and warmth: ' + ', '.join(f'{t.name} {t.light:.0f}/{t.warm:.3f}' for t in taste))
    return (taste, m.get('made')) if len(taste) >= 3 else (None, None)

class Spring:
    """The spring's dreaming on a CPU: Stable Diffusion 1.5 with the LCM-LoRA fused in, loaded as code/sink.py loads it (from the
    half-precision files, half the download, run in full precision), without the omni reference."""
    def __init__(self):
        import torch
        from diffusers import StableDiffusionImg2ImgPipeline, LCMScheduler
        from latent import slerp, catmull, Vae
        torch.set_num_threads(os.cpu_count() or 4)
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained('stable-diffusion-v1-5/stable-diffusion-v1-5', variant='fp16', torch_dtype=torch.float32,
                                                              safety_checker=None, requires_safety_checker=False)
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
        pipe.load_lora_weights('latent-consistency/lcm-lora-sdv1-5', weight_name='pytorch_lora_weights.safetensors'); pipe.fuse_lora(); pipe.unload_lora_weights()
        pipe.set_progress_bar_config(disable=True)
        self.torch, self.pipe, self.slerp, self.catmull, self.V = torch, pipe, slerp, catmull, Vae(pipe.vae, 'cpu')
        self.E0, self.NE = self.embed(sd_prompt('vanitas'))            # the negative is the same for every dream
        say(f'awake: {torch.get_num_threads()} threads')
    def embed(self, prompt):
        with self.torch.no_grad(): return self.pipe.encode_prompt(prompt, 'cpu', 1, True, NEG)
    def dream(self, init, E, s, steps, seed):           # img2img in latent space, as the spring's dream_lat
        t0 = time.time(); g = self.torch.Generator().manual_seed(seed)
        z = self.pipe(prompt_embeds=E, negative_prompt_embeds=self.NE, image=init, strength=s, num_inference_steps=steps,
                      guidance_scale=GUID, generator=g, output_type='latent').images.float()
        if not self.torch.isfinite(z).all(): raise RuntimeError('a dream came out empty')   # never pour black water
        self.spent = getattr(self, 'spent', 0) + time.time() - t0; return z

def walk(S, taste, dreams, per, rng):
    """One walk of the spring: from a first place (one of yesterday's frames; in text only, a first dream) through `dreams` new
    dreams, three dreamed waypoints on the way to each, drawn as `per` frames a stretch on one Catmull-Rom path through them all.
    Returns the frames as dreamed (ungraded), the words of each dream, and the look of each."""
    torch, words_of = S.torch, prompts({'i': 0})        # a walk of its own through her grammar each day, from the machine's entropy
    zs = [S.V.enc(t.im) for t in taste] if taste else []
    def key(K):                                         # a new dream: out of the last one pulled toward yesterday's water, or out of noise
        (w1, p1), (w2, p2) = next(words_of), next(words_of)
        E = torch.lerp(S.embed(p1)[0], S.embed(p2)[0], rng.uniform(*WORDS_MIX)); seed = secrets.randbits(62)
        if zs: pull = rng.randrange(len(zs)); init, s = S.slerp(rng.uniform(0.35, 0.6), K.z, zs[pull]), rng.uniform(*DREAM_S)
        else: pull, init, s = None, torch.zeros(1, 4, H//8, W//8), 1.0
        z = S.dream(init, E, s, STEPS, seed); l, w = look(S.V.dec(z))
        words = f"{w1} ~ {w2.replace('vanitas ', '', 1)}"; say(f'dream: {words}   (light {l:.0f}, warm {w:.3f}{"" if hers(l, w) else ", outside hers"})')
        return Knot(z=z, E=E, seed=seed, pull=pull, words=words, look=(l, w))
    def bend(A, B):                                     # the middle of the way, pulled toward a third of yesterday's frames
        mid = S.slerp(0.5, A.z, B.z)
        if not zs: return mid
        return S.slerp(rng.uniform(0.2, 0.4), mid, zs[rng.choice([i for i in range(len(zs)) if i not in (A.pull, B.pull)] or list(range(len(zs))))])
    def way(A, B, det, n):                              # a place on the way, dreamed with the words halfway between and the noise of the dream ahead
        f = WP_F[n]; init = S.slerp(f, S.slerp(f, A.z, det), S.slerp(f, det, B.z))
        return Knot(z=S.dream(init, torch.lerp(A.E, B.E, f), WP_STR[n], WP_STEPS, B.seed))
    if zs: pull = rng.randrange(len(zs)); K = Knot(z=zs[pull], E=S.E0, seed=secrets.randbits(62), pull=pull, words=None)
    else: K = key(None)
    knots, keys = [K], [K] if K.words else []
    for _ in range(dreams):
        B = key(K); det = bend(K, B); knots += [way(K, B, det, n) for n in range(3)] + [B]; keys.append(B); K = B
    z, frames, t0 = [k.z for k in knots], [], time.time()
    for seg in range(len(z) - 1):
        win = [z[max(seg - 1, 0)], z[seg], z[seg + 1], z[min(seg + 2, len(z) - 1)]]
        frames += [S.V.dec(S.catmull(i/per, *win)) for i in range(1, per + 1)]      # each stretch ends on its knot: the last frame is the last dream
    say(f'{len(frames)} frames drawn, {(time.time() - t0)/len(frames):.1f}s each; dreaming took {S.spent:.0f}s so far')
    return frames, [k.words for k in keys], [k.look for k in keys]

def pack(frames, out, passages, width, budget, index):
    """The reservoir as verse/reservoir.py writes it: a00.jpg ... (a, b, c: the passages; 00, 01: their frames in order) and
    index.json, the quality walked down, then the width, until it fits. Written beside `out` and swapped in whole."""
    n, tmp, q = len(frames)//passages, out.with_name(out.name + '.new'), 84
    while True:
        if tmp.exists(): shutil.rmtree(tmp)
        tmp.mkdir(parents=True); runs = [[f'{chr(97 + p)}{i:02d}.jpg' for i in range(n)] for p in range(passages)]
        for p, run in enumerate(runs):
            for i, name in enumerate(run):
                im = frames[p*n + i]; im.resize((width, round(width*im.height/im.width)), Image.LANCZOS).save(tmp/name, quality=q, optimize=True, progressive=True)
        (tmp/'index.json').write_text(json.dumps({'every': index.pop('every', 5), 'runs': runs, **index}, indent=1) + '\n')
        total = sum(f.stat().st_size for f in tmp.iterdir())
        if total <= budget: break
        index['every'] = json.loads((tmp/'index.json').read_text())['every']
        if q > 56: q -= 4
        else: width = round(width*0.88/16)*16
    if out.exists(): shutil.rmtree(out)
    tmp.rename(out); return width, q, total

def day(S, src, out, a, rng):
    taste, made = yesterday(src, rng) if src else (None, None)
    if src and not taste: say('today is dreamed from the words alone')
    frames, words, looks = walk(S, taste, a.dreams, a.per, rng)
    if not any(HERS_LIGHT[0] - 8 <= l <= HERS_LIGHT[1] + 8 for l, _ in looks):          # black or blown water is never poured; warmth only picks the taste
        sys.exit('none of today\'s dreams is in the light of her pictures: nothing written, yesterday\'s water stays')
    how = (f'out of the water of {made}: its frames stand where her pictures stand in the spring' if taste else 'from the words alone')
    index = {'every': a.every, 'made': datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
             'from': f'one walk of {len(words)} dreams, dreamed on a CPU {how} (code/refill.py), {a.per} frames a stretch',
             'prompts': words, 'frames_without_a_logged_prompt': 0, 'note': 'no frame was dreamed with a face at the sink'}
    shown = [harmonize(f) for f in frames]
    width, q, total = pack(shown, out, a.passages, a.width, a.budget, index)
    say(f'wrote {out}: {a.passages} passages of {len(frames)//a.passages} frames, {"loop" if taste else "text"}, {width} px wide, quality {q}, {total} bytes ({total/1e6:.2f} MB)')
    return {'mode': 'loop' if taste else 'text', 'looks': looks, 'shown_light': round(float(np.mean([look(f)[0] for f in shown])), 1), 'bytes': total, 'thumb': shown[-1].resize((240, 180), Image.LANCZOS)}

def selftest(src):
    """The grade, then its undoing, gives the light back: on a grey ramp within 3 of 255, on a warm one within 8 (gold keeps
    little blue, so its 8-bit steps are coarse; gold is a few sparks in a frame, and each day dreams them again)."""
    ramp = np.linspace(24, 230, 256, dtype=np.float32)[None].repeat(4, 0)
    for name, tint, top, tol in [('grey', (1, 1, 1), 230, 3), ('warm', (1.25, 1.0, 0.55), 190, 8)]:
        x = np.clip(ramp[..., None]*np.array(tint, np.float32), 0, 255)[:, ramp[0] <= top]
        back = np.asarray(ungrade(harmonize(Image.fromarray(x.round().astype(np.uint8)))), np.float32)
        err = float(np.abs(back @ LUM - x.round() @ LUM).max()); print(f'selftest {name}: light comes back within {err:.2f} of 255')
        if err > tol: sys.exit('selftest failed: ungrade() no longer undoes harmonize()')
    if src:
        m = json.loads((src/'index.json').read_text()); L = [look(ungrade(fill(Image.open(src/f)))) for r in m['runs'] for f in r]
        print(f'{src}: {sum(hers(*x) for x in L)} of {len(L)} frames in her light and warmth; light {min(x[0] for x in L):.0f} to {max(x[0] for x in L):.0f}, '
              f'warm {min(x[1] for x in L):.4f} to {max(x[1] for x in L):.4f} (hers: {HERS_LIGHT[0]:.0f} to {HERS_LIGHT[1]:.0f}, {HERS_WARM[0]:.4f} to {HERS_WARM[1]:.4f})')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--from', dest='src', default=''); ap.add_argument('--out', default='reservoir')
    ap.add_argument('--dreams', type=int, default=3); ap.add_argument('--per', type=int, default=5); ap.add_argument('--passages', type=int, default=6)
    ap.add_argument('--width', type=int, default=1024); ap.add_argument('--every', type=float, default=5); ap.add_argument('--budget', type=int, default=5_900_000)
    ap.add_argument('--days', type=int, default=1); ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(); src, out, rng = pathlib.Path(a.src) if a.src else None, pathlib.Path(a.out), random.SystemRandom()
    if a.selftest: return selftest(src)
    if (4*a.dreams*a.per) % a.passages: sys.exit(f'{4*a.dreams*a.per} frames do not cut into {a.passages} equal passages')
    S = Spring()
    if a.days == 1: day(S, src, out, a, rng); say('done'); return
    thumbs = []                                          # the test: does the loop hold its look, day on day?
    with open(out.with_name(out.name + '_drift.jsonl'), 'w') as log:
        for d in range(1, a.days + 1):
            r = day(S, src, out/f'day{d:02d}', a, rng); src = out/f'day{d:02d}'; thumbs.append(r.pop('thumb'))
            log.write(json.dumps(dict(r, day=d)) + '\n'); log.flush(); say(f'day {d} of {a.days}: {r}')
    cols = 10; sheet = Image.new('RGB', (cols*240, -(-len(thumbs)//cols)*180))
    for i, t in enumerate(thumbs): sheet.paste(t, ((i % cols)*240, (i//cols)*180))
    sheet.save(out.with_name(out.name + '_drift.jpg'), quality=85); say('done')

if __name__ == '__main__':
    main()
