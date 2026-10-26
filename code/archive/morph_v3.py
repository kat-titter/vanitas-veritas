#!/usr/bin/env python3
"""
morph_v3 — "Dreamed Anchors + Smooth Drift"

Decouple LOOK from MOTION:
  * Dream a sparse ring of ANCHOR latents around the loop. At source positions
    the anchor is lightly dreamed (discernible); between sources it is dreamed
    hard (gooey / abstract / weird).  -> "sometimes discernible" rhythm.
  * Between anchors DON'T re-dream — Catmull-spline the latents and just decode.
    Decoding is deterministic => glassy-smooth, flicker-free, cheap, so we can
    pack many slow frames between anchors => slow & meditative.
  * No pixel warps (the waviness is gone). Light haze only.

Anchors are cached (anchors_v3.pt) so length / haze can be retuned without
re-dreaming.  Run with --fresh to re-dream.
"""
import os, sys, glob, math, subprocess, torch, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from diffusers import StableDiffusionImg2ImgPipeline, LCMScheduler

HERE  = os.path.dirname(os.path.abspath(__file__))
SRC   = os.path.join(HERE, "veritas")
MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
LCM   = "latent-consistency/lcm-lora-sdv1-5"
CACHE = os.path.join(HERE, "anchors_v4.pt")
W, H, INFER, GUID, device = 640, 480, 8, 1.5, "mps"

# ---- structure ----
D          = 3      # anchors per source segment (incl. the source position)
M          = 40     # decode frames per anchor gap  (FINAL: ~80s sloooow loop)
LOW_STR    = 0.40   # re-dream strength AT source positions (a touch dissolved -> "lost")
HIGH_STR   = 0.66   # re-dream strength BETWEEN sources (gooier / more liquid)
SEED       = 7
FPS        = 12
OUT        = os.path.join(HERE, "veritas_v4_final.mp4")

# liquid, gooey, luxe, clean+dirty, swelling-bubble — NOT hazy
PROMPT = ("vanitas, a face and skull slowly melting into a single swelling "
          "iridescent soap bubble, taut glossy surface tension about to burst, "
          "molten viscous liquid wax and pearl oozing, wet glossy reflections, "
          "clustered droplets and spheres, opulent luxurious gilded, deep black "
          "background, jewel-like, clean elegant forms with grimy organic texture, "
          "oneiric weird surreal, dark baroque, luminous monochrome with rich gold")
NEG = ("text, watermark, signature, frame, border, grid, hazy, foggy, blurry, "
       "washed out, milky, low contrast, flat, sculpture, marble statue, ocean, "
       "sea, waves, water ripples, puddle")

# ---- grade (clearer + luxe + clean/dirty, no warp, no fog-lift) ----
SOFT_W      = 0.10   # barely-there dream softness
GLOSS_W     = 0.55   # specular highlight bloom -> wet luxury sheen
BLACK_GAMMA = 1.25   # deepen blacks (luxe, clear)
GAIN        = 1.06
GOLD        = (1.07, 1.00, 0.80)   # warm gold tint pushed into highlights
GRAIN       = 4.0    # fine grain (dirty)
VIG_STR     = 0.28   # grime vignette (dirty + focus + luxe)

fresh = "--fresh" in sys.argv

def slerp(t,a,b,eps=1e-6):
    af,bf=a.flatten(),b.flatten()
    om=torch.acos(torch.clamp(torch.dot(af/af.norm(),bf/bf.norm()),-1+eps,1-eps)); so=torch.sin(om)
    if so.abs()<eps: return (1-t)*a+t*b
    return (torch.sin((1-t)*om)/so)*a+(torch.sin(t*om)/so)*b

def catmull(u,p0,p1,p2,p3):
    u2,u3=u*u,u*u*u
    return 0.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u2+(-p0+3*p1-3*p2+p3)*u3)

_yy,_xx=np.mgrid[0:H,0:W]
_r=np.sqrt(((_xx-W/2)/(W/2))**2+((_yy-H/2)/(H/2))**2)
VIGNETTE=(1-VIG_STR*np.clip(_r-0.55,0,None)/0.65)[...,None]   # darken edges (grime/luxe)
_GRAIN=np.random.default_rng(0).normal(0,GRAIN,(H,W,3))        # fixed grain (dirty, static)

def grade(img):
    x=img.astype(np.float32)
    x=(1-SOFT_W)*x+SOFT_W*gaussian_filter(x,(2.2,2.2,0))       # faint dream softness
    hi=np.clip(x-205,0,None)                                   # only bright speculars
    bloom=GLOSS_W*gaussian_filter(hi,(6,6,0))
    x=255-(255-x)*(255-bloom)/255                              # wet glossy sheen
    n=np.clip(x/255,0,1)**BLACK_GAMMA*GAIN                     # deep luxe blacks + pop
    x=np.clip(n,0,1)*255
    lum=np.clip((x.mean(2,keepdims=True)/255-0.5)*2,0,1)       # highlight mask
    x=x*(1+(np.array(GOLD)-1)*lum)                             # gold tint in highlights
    x=x*VIGNETTE+_GRAIN                                        # grime vignette + grain
    return np.clip(x,0,255).astype(np.uint8)

print("loading pipe…")
pipe=StableDiffusionImg2ImgPipeline.from_pretrained(MODEL,torch_dtype=torch.float32,
        safety_checker=None,requires_safety_checker=False)
pipe.scheduler=LCMScheduler.from_config(pipe.scheduler.config)
pipe.load_lora_weights(LCM); pipe.fuse_lora(); pipe=pipe.to(device)
pipe.set_progress_bar_config(disable=True)
pipe.enable_attention_slicing(); pipe.vae.enable_slicing()
vae,SCALE=pipe.vae,pipe.vae.config.scaling_factor

@torch.no_grad()
def enc_img(im):
    a=torch.from_numpy(np.asarray(im.convert("RGB").resize((W,H),Image.LANCZOS),np.float32)/127.5-1)
    return vae.encode(a.permute(2,0,1).unsqueeze(0).to(device)).latent_dist.mean*SCALE
@torch.no_grad()
def dec(l):
    im=((vae.decode(l/SCALE).sample.clamp(-1,1)+1)/2)[0].permute(1,2,0).cpu().numpy()
    return Image.fromarray((im*255).round().astype(np.uint8))

srcs=sorted(glob.glob(os.path.join(SRC,"*.png")))
src_lat=[enc_img(Image.open(p)) for p in srcs]
Nsrc=len(src_lat)

# ---------- build / load dreamed anchor ring ----------
if (not fresh) and os.path.exists(CACHE):
    anchors=[a.to(device) for a in torch.load(CACHE)]
    print(f"loaded {len(anchors)} cached anchors")
else:
    print(f"dreaming {Nsrc*D} anchors…")
    anchors=[]
    for p in range(Nsrc):
        a,b=src_lat[p],src_lat[(p+1)%Nsrc]
        for d in range(D):
            f=d/D
            base=dec(slerp(f,a,b))                       # smooth latent blend
            strength=LOW_STR+(HIGH_STR-LOW_STR)*math.sin(math.pi*f)  # low@source, high@mid
            g=torch.Generator(device=device).manual_seed(SEED)
            dream=pipe(prompt=PROMPT,negative_prompt=NEG,image=base,strength=float(strength),
                       num_inference_steps=INFER,guidance_scale=GUID,generator=g).images[0]
            if device=="mps": torch.mps.empty_cache()
            anchors.append(enc_img(dream))
            print(f"  anchor {len(anchors)}/{Nsrc*D}  (seg {p}, f={f:.2f}, str={strength:.2f})",flush=True)
    torch.save([a.cpu() for a in anchors],CACHE)
    anchors=[a.to(device) for a in anchors]

# ---------- smooth Catmull decode between anchors (no flicker) ----------
K=len(anchors); total=K*M
print(f"decoding {total} frames ({K} anchors x {M}) -> {total/FPS:.1f}s @ {FPS}fps")
ff=__import__("imageio_ffmpeg").get_ffmpeg_exe()
proc=subprocess.Popen([ff,"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
    "-framerate",str(FPS),"-i","-","-vf","scale=1920:1440:flags=lanczos","-c:v","libx264",
    "-profile:v","main","-pix_fmt","yuv420p","-crf","16","-movflags","+faststart",OUT],stdin=subprocess.PIPE)
idx=0
for i in range(K):
    p0,p1,p2,p3=anchors[(i-1)%K],anchors[i],anchors[(i+1)%K],anchors[(i+2)%K]
    for j in range(M):
        u=j/M
        frame=np.asarray(dec(catmull(u,p0,p1,p2,p3)),np.float32)
        proc.stdin.write(grade(frame).tobytes())
        if device=="mps": torch.mps.empty_cache()
        idx+=1
        if idx%24==0: print(f"  {idx}/{total}",flush=True)
proc.stdin.close(); proc.wait()
print("wrote",OUT)
