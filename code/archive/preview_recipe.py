#!/usr/bin/env python3
"""
preview_recipe — render ONE transition with the current 'gooey hazy dream'
recipe and post-treatment, output a short motion clip + a still. Fast iteration
loop: tweak the constants at top, re-run, watch.
"""
import os, glob, math, subprocess, torch, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
from diffusers import StableDiffusionImg2ImgPipeline, LCMScheduler

HERE  = os.path.dirname(os.path.abspath(__file__))
SRC   = os.path.join(HERE, "veritas")
MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
LCM   = "latent-consistency/lcm-lora-sdv1-5"
W, H, INFER, GUID, device = 640, 480, 8, 1.5, "mps"

KEY_A, KEY_B = 2, 3          # transition to preview
N_STEPS      = 24           # rendered frames in the transition
MAX_STR      = 0.58         # peak gooey strength mid-transition
SEED         = 7
FPS          = 12
SLOW         = 2.5          # languid slowdown (frame-blend)

# ---- gooey hazy dream prompt ----
PROMPT = ("vanitas, a face and skull slowly melting like molten wax and pearl, "
          "soft gooey dripping forms, hazy foggy dream, gauzy soft focus, diffuse "
          "glow, oneiric, weird gentle surreal, dark baroque, ethereal smoke, "
          "luminous monochrome with soft gold flecks, blurred, veiled")
NEG = ("text, watermark, signature, frame, border, grid, sharp, crisp, "
       "high contrast, sculpture, marble statue, ocean, sea, waves, water, puddle")

# ---- haze treatment ----
SOFT_W   = 0.38   # soft-focus mix (dreamy blur)
SOFT_SIG = 5.0
BLOOM_W  = 0.30   # highlight bloom
FOG_LIFT = 13.0   # lift blacks -> foggy
FOG_GAIN = 0.93   # gentle contrast drop
GRAIN    = 4.0

# ---- gentle organic drift (NOT periodic ocean) ----
WARP_LO, WARP_HI = 5.0, 1.8
LO_CYC, HI_CYC   = 2, 5

def slerp(t,a,b,eps=1e-6):
    af,bf=a.flatten(),b.flatten()
    om=torch.acos(torch.clamp(torch.dot(af/af.norm(),bf/bf.norm()),-1+eps,1-eps)); so=torch.sin(om)
    if so.abs()<eps: return (1-t)*a+t*b
    return (torch.sin((1-t)*om)/so)*a+(torch.sin(t*om)/so)*b

def haze(img):
    soft = (1-SOFT_W)*img + SOFT_W*gaussian_filter(img, (SOFT_SIG,SOFT_SIG,0))
    hi   = np.clip(soft-175,0,None)
    bloom= BLOOM_W*gaussian_filter(hi,(8,8,0))
    out  = 255 - (255-soft)*(255-bloom)/255          # screen blend bloom
    out  = out*FOG_GAIN + FOG_LIFT                   # foggy lift
    g    = np.random.default_rng(0).normal(0,GRAIN,out.shape)  # fixed grain seed
    return np.clip(out+g,0,255)

def drift(H,W,t):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32); a=2*math.pi
    L1,L2,L3=W/1.3,W/4.0,H/3.5
    dx=WARP_LO*np.sin(a*(yy/L1+LO_CYC*t))+WARP_HI*np.sin(a*(xx/L2+yy/L3+HI_CYC*t*1.03))
    dy=WARP_LO*np.cos(a*(xx/L1+LO_CYC*t*0.79))+WARP_HI*np.cos(a*(yy/L2+xx/L3+HI_CYC*t*1.11))
    return dx,dy

def warp(img,dx,dy):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    cy=np.clip(yy+dy,0,H-1); cx=np.clip(xx+dx,0,W-1)
    o=np.empty_like(img)
    for c in range(3): o[...,c]=map_coordinates(img[...,c],[cy,cx],order=1,mode="reflect")
    return o

print("loading pipe…")
pipe=StableDiffusionImg2ImgPipeline.from_pretrained(MODEL,torch_dtype=torch.float32,
        safety_checker=None,requires_safety_checker=False)
pipe.scheduler=LCMScheduler.from_config(pipe.scheduler.config)
pipe.load_lora_weights(LCM); pipe.fuse_lora(); pipe=pipe.to(device)
pipe.set_progress_bar_config(disable=True)
pipe.enable_attention_slicing(); pipe.enable_vae_slicing()
vae,SCALE=pipe.vae,pipe.vae.config.scaling_factor

@torch.no_grad()
def enc(p):
    im=Image.open(p).convert("RGB").resize((W,H),Image.LANCZOS)
    a=torch.from_numpy(np.asarray(im,np.float32)/127.5-1).permute(2,0,1).unsqueeze(0)
    return vae.encode(a.to(device)).latent_dist.mean*SCALE
@torch.no_grad()
def dec(l):
    im=((vae.decode(l/SCALE).sample.clamp(-1,1)+1)/2)[0].permute(1,2,0).cpu().numpy()
    return Image.fromarray((im*255).round().astype(np.uint8))

srcs=sorted(glob.glob(os.path.join(SRC,"*.png")))
la,lb=enc(srcs[KEY_A]),enc(srcs[KEY_B])
gen=torch.Generator(device=device).manual_seed(SEED)

print("rendering transition…")
rendered=[]
for s in range(N_STEPS):
    u=s/N_STEPS
    base=dec(slerp(u,la,lb))
    strength=MAX_STR*math.sin(math.pi*u)
    if int(INFER*strength)>=1:
        img=pipe(prompt=PROMPT,negative_prompt=NEG,image=base,strength=float(strength),
                 num_inference_steps=INFER,guidance_scale=GUID,generator=gen).images[0]
    else:
        img=base
    if device=="mps": torch.mps.empty_cache()
    rendered.append(np.asarray(img,np.float32))
    print(f"  {s+1}/{N_STEPS}",end="\r",flush=True)
print()

# slow + haze + drift -> clip
import imageio_ffmpeg
ff=imageio_ffmpeg.get_ffmpeg_exe()
n_out=int(round(N_STEPS*SLOW))
proc=subprocess.Popen([ff,"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
    "-framerate",str(FPS),"-i","-","-vf","scale=1280:960:flags=lanczos","-c:v","libx264",
    "-pix_fmt","yuv420p","-crf","19",os.path.join(HERE,"veritas_recipe_preview.mp4")],
    stdin=subprocess.PIPE)
still_saved=False
for k in range(n_out):
    fp=k*(N_STEPS-1)/max(1,n_out-1); i0=int(fp); f=fp-i0; i1=min(i0+1,N_STEPS-1)
    blend=(1-f)*rendered[i0]+f*rendered[i1]
    t=k/n_out
    dx,dy=drift(H,W,t)
    out=haze(warp(blend,dx,dy))
    if not still_saved and k>=n_out//2:
        Image.fromarray(out.astype(np.uint8)).save(os.path.join(HERE,"recipe_still.png")); still_saved=True
    proc.stdin.write(out.astype(np.uint8).tobytes())
proc.stdin.close(); proc.wait()
print("wrote veritas_recipe_preview.mp4 + recipe_still.png")
