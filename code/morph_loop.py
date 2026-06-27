#!/usr/bin/env python3
"""
veritas / vanitas slop loop
---------------------------
Dream-like melting loop from 8 vanitas frames using an open-source diffusion model.

Technique (hybrid):
  * Encode each frame into Stable Diffusion's VAE latent space.
  * SLERP-interpolate between consecutive frames around the loop (wraps 7 -> 0),
    so the result is a seamless cycle.
  * Smoothstep easing -> the loop eases into and lingers on each recognizable
    keyframe, then oozes through the blurry in-between.
  * Near the midpoint of every transition, run a light img2img pass so the model
    re-dreams the goo into hallucinated, gooey vanitas texture.

Outputs:
  frames/frame_####.png   (progressive, crash-safe)
  veritas_slop_loop.mp4   (seamless 12fps loop)
"""

import os, sys, math, time, glob, subprocess
import torch
import numpy as np
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline, LCMScheduler

# ---------------------------------------------------------------- config
HERE      = os.path.dirname(os.path.abspath(__file__))
SRC_DIR   = os.path.join(HERE, "veritas")
FRAME_DIR = os.path.join(HERE, "frames")
OUT_MP4   = os.path.join(HERE, "veritas_slop_loop.mp4")
PROG_FILE = os.path.join(HERE, ".progress")

MODEL     = "stable-diffusion-v1-5/stable-diffusion-v1-5"
LCM_LORA  = "latent-consistency/lcm-lora-sdv1-5"   # 6-step consistency model
W, H      = 640, 480           # diffusion working res (4:3, mult of 8)
STEPS_PER_PAIR = 48            # interpolation frames per segment (8 segments)
MAX_STRENGTH   = 0.55          # peak img2img re-dream strength mid-segment
STR_THRESHOLD  = 0.10          # below this, skip img2img (keeps keyframes crisp)
INFER_STEPS    = 8             # LCM denoise steps (few-step)
GUIDANCE       = 1.5           # LCM wants low CFG
FPS            = 12
UPSCALE        = 3             # final mp4 = W*UPSCALE x H*UPSCALE (lanczos)
SEED           = 7

PROMPT = ("vanitas still life, a face dissolving into particles, soap bubbles "
          "and sprays of gold light, baroque, dreamlike, ethereal, soft focus, "
          "luminous monochrome with warm gold accents, fine detail")
NEG    = "text, watermark, signature, frame, border, grid, ugly, deformed, low quality"

SMOKE_TEST = "--smoke" in sys.argv   # render just the first transition (40 frames)

# ---------------------------------------------------------------- helpers
def catmull_rom(u, p0, p1, p2, p3):
    """Uniform Catmull-Rom: smooth curve passing through p1 (u=0) and p2 (u=1).
    Tangents come from neighbours, so motion flows *through* each keyframe with
    no stop and no velocity corner -> always moving, never still."""
    u2, u3 = u * u, u * u * u
    return (0.5 * ((2 * p1) +
                   (-p0 + p2) * u +
                   (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 +
                   (-p0 + 3 * p1 - 3 * p2 + p3) * u3))

def load_keyframe(path):
    im = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 127.5 - 1.0       # [-1,1]
    return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)  # 1,3,H,W

# ---------------------------------------------------------------- setup
device = "mps" if torch.backends.mps.is_available() else "cpu"
os.makedirs(FRAME_DIR, exist_ok=True)
srcs = sorted(glob.glob(os.path.join(SRC_DIR, "*.png")))
assert len(srcs) == 8, f"expected 8 frames, found {len(srcs)}"
print(f"device={device}  frames={len(srcs)}  res={W}x{H}")

print("loading model + LCM-LoRA…")
pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    MODEL, torch_dtype=torch.float32, safety_checker=None, requires_safety_checker=False)
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
pipe.load_lora_weights(LCM_LORA)
pipe.fuse_lora()
pipe = pipe.to(device)
pipe.set_progress_bar_config(disable=True)
pipe.enable_attention_slicing()    # slice UNet attention -> lower peak memory
pipe.enable_vae_slicing()          # decode VAE in slices -> lower peak memory
vae   = pipe.vae
SCALE = vae.config.scaling_factor

@torch.no_grad()
def encode(img):
    img = img.to(device, dtype=torch.float32)
    return vae.encode(img).latent_dist.mean * SCALE

@torch.no_grad()
def decode(lat):
    img = vae.decode(lat / SCALE).sample
    img = (img.clamp(-1, 1) + 1) / 2
    arr = (img[0].permute(1, 2, 0).cpu().numpy() * 255).round().astype(np.uint8)
    return Image.fromarray(arr)

print("encoding keyframes…")
latents = [encode(load_keyframe(p)) for p in srcs]

# warm up the MPS graph once so the first real frame isn't a stall
print("warming up img2img graph…")
_warm = decode(catmull_rom(0.5, latents[0], latents[1], latents[2], latents[3]))
_ = pipe(prompt=PROMPT, negative_prompt=NEG, image=_warm, strength=0.4,
         num_inference_steps=INFER_STEPS, guidance_scale=GUIDANCE).images[0]
print("warm.")

# ---------------------------------------------------------------- render
gen = torch.Generator(device=device).manual_seed(SEED)
pairs = 1 if SMOKE_TEST else len(latents)
total = pairs * STEPS_PER_PAIR
idx = 0
t0 = time.time()

N = len(latents)
for p in range(pairs):
    # four looped control points -> smooth Catmull-Rom segment from p to p+1
    p0, p1, p2, p3 = (latents[(p - 1) % N], latents[p],
                      latents[(p + 1) % N], latents[(p + 2) % N])
    for s in range(STEPS_PER_PAIR):
        fpath = os.path.join(FRAME_DIR, f"frame_{idx:04d}.png")
        if os.path.exists(fpath):           # resume: keep already-rendered frames
            idx += 1
            continue
        u = s / STEPS_PER_PAIR                  # [0,1)  endpoint excluded -> clean loop
        base = decode(catmull_rom(u, p0, p1, p2, p3))   # constant-speed, never still

        strength = MAX_STRENGTH * math.sin(math.pi * u)   # peak mid-segment
        # img2img needs >=1 effective denoise step (int(steps*strength)); below
        # that the pipeline builds an empty schedule -> skip, keep crisp keyframe
        if int(INFER_STEPS * strength) >= 1:
            frame = pipe(prompt=PROMPT, negative_prompt=NEG, image=base,
                         strength=float(strength), num_inference_steps=INFER_STEPS,
                         guidance_scale=GUIDANCE, generator=gen).images[0]
            tag = f"melt s={strength:.2f}"
        else:
            frame = base
            tag = "keyframe"

        frame.save(fpath)
        del base, frame
        if device == "mps":                 # bound MPS cache growth -> stop swap thrash
            torch.mps.empty_cache()
        el = time.time() - t0
        spf = el / (idx + 1)
        eta = spf * (total - idx - 1)
        done = idx + 1
        bar = "█" * (done * 24 // total) + "░" * (24 - done * 24 // total)
        line = (f"[{bar}] {done}/{total}  {spf:.1f}s/f  eta {eta/60:.1f}m  "
                f"(pair {p}, {tag})")
        print("  " + line, flush=True)
        with open(PROG_FILE, "w") as f:
            f.write(line + "\n")
        idx += 1

# ---------------------------------------------------------------- assemble
import imageio_ffmpeg
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
ow, oh = W * UPSCALE, H * UPSCALE
print(f"\nencoding mp4 {ow}x{oh} @ {FPS}fps -> {OUT_MP4}")
subprocess.run([
    ffmpeg, "-y", "-framerate", str(FPS), "-i",
    os.path.join(FRAME_DIR, "frame_%04d.png"),
    "-vf", f"scale={ow}:{oh}:flags=lanczos", "-c:v", "libx264",
    "-pix_fmt", "yuv420p", "-crf", "18", OUT_MP4], check=True)
print(f"done in {(time.time()-t0)/60:.1f} min  ->  {OUT_MP4}")
