#!/usr/bin/env python3
"""
liquify — post-process pass that makes the slop loop feel liquid, bubbly, slower.

  * animated flow-displacement field (drifting low + high freq sine warps)
    -> viscous, under-glass, soap-film ripple
  * drifting bubble-lens refractions rising upward -> "bubbly"
  * frame-blend slowdown (SLOW x more frames) -> languid ooze, no choppiness

All numpy/scipy — no diffusion, memory-light. Temporal phases complete an
integer number of cycles over the loop so the result still loops seamlessly.
"""
import os, sys, glob, math, subprocess
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

HERE      = os.path.dirname(os.path.abspath(__file__))
FRAME_DIR = os.path.join(HERE, "frames")

# ---- tunables ----
SLOW       = 2.0     # output this many x the input frames (languid motion)
WARP_LO    = 14.0    # px, big slow surface warp
WARP_HI    = 5.0     # px, fine ripple
LO_CYCLES  = 3       # temporal cycles of the slow warp over the loop
HI_CYCLES  = 7       # temporal cycles of the fine ripple
N_BUBBLES  = 4       # drifting refraction lenses
BUB_STREN  = 0.45    # bubble refraction strength
FPS        = 12

def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)

def flow_field(H, W, t):
    """Displacement (dx,dy) at loop-phase t in [0,1)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    L1, L2, L3 = W / 1.4, W / 5.0, H / 4.5
    a = 2 * math.pi
    dx = (WARP_LO * np.sin(a * (yy / L1 + LO_CYCLES * t)) +
          WARP_HI * np.sin(a * (xx / L2 + yy / L3 + HI_CYCLES * t)))
    dy = (WARP_LO * np.cos(a * (xx / L1 + LO_CYCLES * t * 0.83)) +
          WARP_HI * np.cos(a * (yy / L2 + xx / L3 + HI_CYCLES * t * 1.07)))
    return dx, dy

def bubble_field(H, W, t):
    """Radial refraction from a few bubbles drifting upward (and looping)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = np.zeros((H, W), np.float32); dy = np.zeros((H, W), np.float32)
    for k in range(N_BUBBLES):
        ph = k / N_BUBBLES
        cx = W * (0.15 + 0.7 * ((0.37 * k + 0.5 * math.sin(2*math.pi*(t+ph))) % 1.0))
        cy = H * ((ph - t) % 1.0)                      # rise upward, loop
        r  = W * (0.10 + 0.04 * k / max(1, N_BUBBLES))
        ddx = xx - cx; ddy = yy - cy
        d2 = ddx*ddx + ddy*ddy
        bump = np.exp(-d2 / (2 * (r*0.6)**2))          # smooth lens falloff
        dx += BUB_STREN * bump * ddx / r
        dy += BUB_STREN * bump * ddy / r
    return dx, dy

def warp(img, dx, dy):
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cy = np.clip(yy + dy, 0, H - 1); cx = np.clip(xx + dx, 0, W - 1)
    out = np.empty_like(img)
    for c in range(3):
        out[..., c] = map_coordinates(img[..., c], [cy, cx], order=1, mode="reflect")
    return out

def liquify_sequence(paths, out_mp4, total_for_phase=None, start_phase=0):
    """paths: ordered input frames. Emits SLOW x frames, warped, to out_mp4."""
    imgs = [load(p) for p in paths]
    H, W = imgs[0].shape[:2]
    n_in = len(imgs)
    n_out = int(round(n_in * SLOW))
    span = total_for_phase or n_out
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen(
        [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-framerate", str(FPS), "-i", "-", "-vf", "scale=1280:960:flags=lanczos",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", out_mp4],
        stdin=subprocess.PIPE)
    for k in range(n_out):
        fpos = k * (n_in - 1) / max(1, n_out - 1)      # blended source position
        i0 = int(math.floor(fpos)); f = fpos - i0
        i1 = min(i0 + 1, n_in - 1)
        base = (1 - f) * imgs[i0] + f * imgs[i1]
        t = ((start_phase + k) % span) / span
        dx, dy = flow_field(H, W, t)
        bx, by = bubble_field(H, W, t)
        out = warp(base, dx + bx, dy + by)
        proc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
        print(f"  liquify {k+1}/{n_out}", end="\r", flush=True)
    proc.stdin.close(); proc.wait()
    print(f"\nwrote {out_mp4}")

if __name__ == "__main__":
    # sample mode: liquify a frame range ->  python3 liquify.py 96 143 sample.mp4
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    paths = [os.path.join(FRAME_DIR, f"frame_{i:04d}.png") for i in range(a, b + 1)]
    paths = [p for p in paths if os.path.exists(p)]
    liquify_sequence(paths, os.path.join(HERE, out))
