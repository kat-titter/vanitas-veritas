#!/usr/bin/env python3
"""
order_preview — FAST iteration on loop ORDER (no img2img diffusion).

Morphs the real source frames via VAE latent Catmull-spline (smooth dissolve) at
low res, with a light palette grade so it reads on-brand. ~1 min per candidate
ordering vs ~50 min for the full render. Use this to judge flow / arc / surprise;
the gooey dream quality is identical across orderings, so order is all that varies.

Usage:  python3 order_preview.py            # renders all CANDIDATES
        python3 order_preview.py 1 0 4 3 2 7 6 5   # render one custom order
"""
import os, sys, glob, math, subprocess, torch, numpy as np
from PIL import Image
from diffusers import AutoencoderKL

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,"source","veritas")
OUTDIR=os.path.join(ROOT,"_order_tests"); os.makedirs(OUTDIR,exist_ok=True)
MODEL="stable-diffusion-v1-5/stable-diffusion-v1-5"
W,H=512,384; M=14; FPS=12; device="mps"

# palette-lite (cool mono + gold accent + deep blacks) so previews look on-theme
COOL=(0.94,0.99,1.07); GOLD_TONE=(1.20,0.80,0.34); WARM=42.0

CANDIDATES={
  # smoothest possible (TSP min structural jump)
  "A_smooth":      [0,1,4,7,3,2,6,5],
  # vanitas narrative: serene life -> dissolution -> death -> the trinity pivot (7) -> bloom/vanity -> back
  "B_vanitas_arc": [1,0,4,3,2,7,6,5],
  # bloom finale: keep the 3 flower/bloom frames (7,6,5) clustered as a climax
  "C_bloom_climax":[1,0,3,4,2,7,6,5],
}

def slerp(t,a,b,eps=1e-6):
    af,bf=a.flatten(),b.flatten()
    om=torch.acos(torch.clamp(torch.dot(af/af.norm(),bf/bf.norm()),-1+eps,1-eps));so=torch.sin(om)
    if so.abs()<eps:return (1-t)*a+t*b
    return (torch.sin((1-t)*om)/so)*a+(torch.sin(t*om)/so)*b
def catmull(u,p0,p1,p2,p3):
    u2,u3=u*u,u*u*u
    return 0.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u2+(-p0+3*p1-3*p2+p3)*u3)

_yy,_xx=np.mgrid[0:H,0:W]; _r=np.sqrt(((_xx-W/2)/(W/2))**2+((_yy-H/2)/(H/2))**2)
VIG=(1-0.26*np.clip(_r-0.55,0,None)/0.65)[...,None]
def grade(x):
    warm=np.clip((x[...,0:1]-x[...,2:3])/WARM,0,1)
    lum=0.299*x[...,0:1]+0.587*x[...,1:2]+0.114*x[...,2:3]
    x=(1-warm)*(lum*np.array(COOL))+warm*(lum*np.array(GOLD_TONE))
    x=np.clip((x/255)**1.22*1.05,0,1)*255*VIG
    return np.clip(x,0,255).astype(np.uint8)

print("loading VAE…")
vae=AutoencoderKL.from_pretrained(MODEL,subfolder="vae",torch_dtype=torch.float32).to(device)
vae.enable_slicing(); SCALE=vae.config.scaling_factor
@torch.no_grad()
def enc(p):
    im=Image.open(p).convert("RGB").resize((W,H),Image.LANCZOS)
    a=torch.from_numpy(np.asarray(im,np.float32)/127.5-1).permute(2,0,1).unsqueeze(0)
    return vae.encode(a.to(device)).latent_dist.mean*SCALE
@torch.no_grad()
def dec(l):
    im=((vae.decode(l/SCALE).sample.clamp(-1,1)+1)/2)[0].permute(1,2,0).cpu().numpy()
    return (im*255)

srcs=sorted(glob.glob(os.path.join(SRC,"*.png")))
print("source frames:",len(srcs))
src_lat=[enc(p) for p in srcs]
D=np.load("/tmp/distmat.npy") if os.path.exists("/tmp/distmat.npy") else None

def render(order,name):
    lat=[src_lat[i] for i in order]; K=len(lat)
    ff=__import__("imageio_ffmpeg").get_ffmpeg_exe()
    out=os.path.join(OUTDIR,f"order_{name}.mp4")
    proc=subprocess.Popen([ff,"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
        "-framerate",str(FPS),"-i","-","-vf","scale=768:576:flags=lanczos","-c:v","libx264",
        "-profile:v","main","-pix_fmt","yuv420p","-crf","20","-movflags","+faststart",out],stdin=subprocess.PIPE)
    for i in range(K):
        p0,p1,p2,p3=lat[(i-1)%K],lat[i],lat[(i+1)%K],lat[(i+2)%K]
        for j in range(M):
            fr=grade(dec(catmull(j/M,p0,p1,p2,p3)))
            proc.stdin.write(fr.tobytes())
            if device=="mps":torch.mps.empty_cache()
    proc.stdin.close();proc.wait()
    cost=sum(D[order[k],order[(k+1)%K]] for k in range(K)) if D is not None else -1
    print(f"  wrote {out}  | order {order} | smoothness-cost {cost:.0f} (lower=smoother)")

if len(sys.argv)>1:
    order=[int(x) for x in sys.argv[1:]]; render(order,"custom")
else:
    for name,order in CANDIDATES.items(): render(order,name)
print("done ->",OUTDIR)
