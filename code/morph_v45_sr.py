#!/usr/bin/env python3
"""
morph_v45_sr — final render, MAX QUALITY.

Reuses the cached 32 dreamed anchors (no re-dream), Catmull-decodes the slow
loop (M=190 -> 6080 frames, ~8:30), and runs Real-ESRGAN 4x on every frame for
a native 2560x1920 output (vs lanczos upscale).

Grade order is split so the "clean + dirty" texture survives super-res:
    colour grade @640  ->  ESRGAN 4x  ->  grain + vignette @2560
"""
import os, sys, glob, math, time, subprocess, torch, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from diffusers import AutoencoderKL
from spandrel import ModelLoader

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
CACHE=os.path.join(HERE,"anchors_final.pt")
SR_W=os.path.join(HERE,"models","RealESRGAN_x4plus.pth")
OUT=os.path.join(ROOT,"video","veritas_loop_v45_"+( "4k" if len(sys.argv)<=2 else sys.argv[2])+".mp4")
PROG=os.path.join(ROOT,"_archive",".prog_sr")
MODEL="stable-diffusion-v1-5/stable-diffusion-v1-5"
device="mps"
M=int(sys.argv[1]) if len(sys.argv)>1 else 190     # frames/gap (M=19 -> 10% preview)
_TAG=sys.argv[2] if len(sys.argv)>2 else "4k"
FPS=12; DEC_BATCH=4
W,H=640,480; OW,OH=W*4,H*4            # 2560 x 1920

# colour grade (pre-ESRGAN) — matches harmonized look, NO grain/vignette yet
SOFT_W=0.10; GLOSS_W=0.55; BLACK_GAMMA=1.18; GAIN=1.05; CONTRAST=1.30
COOL=(0.93,0.98,1.09); GOLD_TONE=(1.22,0.80,0.30); WARM_SCALE=40.0
# finish (post-ESRGAN, full res)
GRAIN=4.0; VIG_STR=0.28

def catmull(u,p0,p1,p2,p3):
    u2,u3=u*u,u*u*u
    return 0.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u2+(-p0+3*p1-3*p2+p3)*u3)

def grade_color(x):                    # x: HxWx3 float 0..255 (640x480)
    warm=np.clip((x[...,0:1]-x[...,2:3])/WARM_SCALE,0,1)
    x=(1-SOFT_W)*x+SOFT_W*gaussian_filter(x,(2.2,2.2,0))
    hi=np.clip(x-205,0,None); bloom=GLOSS_W*gaussian_filter(hi,(6,6,0))
    x=255-(255-x)*(255-bloom)/255
    n=np.clip(x/255,0,1)**BLACK_GAMMA*GAIN; x=np.clip(n,0,1)*255
    lum=0.299*x[...,0:1]+0.587*x[...,1:2]+0.114*x[...,2:3]
    x=(1-warm)*(lum*np.array(COOL))+warm*(lum*np.array(GOLD_TONE))
    n=np.clip(x/255,0,1); x=(1/(1+np.exp(-CONTRAST*4*(n-0.5))))*255
    return np.clip(x,0,255).astype(np.float32)

# full-res finish layers (precomputed once)
_yy,_xx=np.mgrid[0:OH,0:OW]; _r=np.sqrt(((_xx-OW/2)/(OW/2))**2+((_yy-OH/2)/(OH/2))**2)
VIG=(1-VIG_STR*np.clip(_r-0.55,0,None)/0.65)[...,None]
GRAIN_HI=np.random.default_rng(0).normal(0,GRAIN,(OH,OW,3))
def grade_finish(x):                   # x: OHxOWx3 float 0..255
    return np.clip(x*VIG+GRAIN_HI,0,255).astype(np.uint8)

print("loading VAE + Real-ESRGAN…")
vae=AutoencoderKL.from_pretrained(MODEL,subfolder="vae",torch_dtype=torch.float32).to(device)
vae.enable_slicing(); SCALE=vae.config.scaling_factor
sr=ModelLoader().load_from_file(SR_W).to(device).eval()
sr.model.half()                        # fp16 ESRGAN (2x faster, fits memory)

@torch.no_grad()
def decode_batch(lats):                # list of [1,4,h,w] -> list of HxWx3 float 0..255
    t=torch.cat(lats,0)
    im=((vae.decode(t/SCALE).sample.clamp(-1,1)+1)/2)
    return [(im[i].permute(1,2,0).cpu().numpy()*255) for i in range(im.shape[0])]

@torch.no_grad()
def esrgan(frame640):                  # HxWx3 float 0..255 -> OHxOWx3 float 0..255
    t=torch.from_numpy(frame640/255).permute(2,0,1).unsqueeze(0).to(device,torch.float16)
    o=sr(t)[0].float().clamp(0,1).permute(1,2,0).cpu().numpy()*255
    return o

anchors=[a.to(device) for a in torch.load(CACHE)]; K=len(anchors)
total=K*M
print(f"{K} anchors x {M} = {total} frames -> {total/FPS:.0f}s @ {FPS}fps -> {OW}x{OH}")

ff=__import__("imageio_ffmpeg").get_ffmpeg_exe()
proc=subprocess.Popen([ff,"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{OW}x{OH}",
    "-framerate",str(FPS),"-i","-","-c:v","libx264","-profile:v","high","-pix_fmt","yuv420p",
    "-crf","15","-movflags","+faststart",OUT],stdin=subprocess.PIPE)

# build ordered (anchor, u) spec list
specs=[]
for i in range(K):
    for j in range(M): specs.append((i,j))

t0=time.time(); idx=0
for b0 in range(0,len(specs),DEC_BATCH):
    batch=specs[b0:b0+DEC_BATCH]
    lats=[]
    for (i,j) in batch:
        p0,p1,p2,p3=anchors[(i-1)%K],anchors[i],anchors[(i+1)%K],anchors[(i+2)%K]
        lats.append(catmull(j/M,p0,p1,p2,p3))
    decoded=decode_batch(lats)
    torch.mps.empty_cache()
    for frame640 in decoded:
        col=grade_color(frame640)
        hi=esrgan(col)
        out=grade_finish(hi)
        if idx==0: Image.fromarray(out).save("/tmp/sr_frame0.png")   # debug: inspect first frame
        proc.stdin.write(out.tobytes())
        torch.mps.empty_cache()
        idx+=1
        if idx%20==0:
            el=time.time()-t0; spf=el/idx; eta=spf*(total-idx)
            line=f"{idx}/{total}  {spf:.1f}s/f  eta {eta/3600:.1f}h"
            print("  "+line,flush=True); open(PROG,"w").write(line+"\n")
proc.stdin.close(); proc.wait()
print(f"\nwrote {OUT}  in {(time.time()-t0)/3600:.1f}h")
