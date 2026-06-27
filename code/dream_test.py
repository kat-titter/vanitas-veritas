#!/usr/bin/env python3
"""
dream_test — fast style comparison for the gooey-dream re-dream.
Loads the pipe ONCE, renders the same morph midpoint under several prompts x
img2img strengths, and writes a single labeled grid for side-by-side judging.
No full render — just a handful of frames.
"""
import os, glob, torch, numpy as np
from PIL import Image, ImageDraw
from diffusers import StableDiffusionImg2ImgPipeline, LCMScheduler

HERE   = os.path.dirname(os.path.abspath(__file__))
SRC    = os.path.join(HERE, "veritas")
MODEL  = "stable-diffusion-v1-5/stable-diffusion-v1-5"
LCM    = "latent-consistency/lcm-lora-sdv1-5"
W, H   = 640, 480
INFER, GUID = 8, 1.5
device = "mps"

# morph point to test on (between two keyframes), and strengths to sweep
U_POINT    = 0.5
STRENGTHS  = [0.45, 0.62, 0.78]
KEY_A, KEY_B = 2, 3        # which two source frames to morph between

NEG = ("text, watermark, signature, frame, border, grid, ugly, deformed, "
       "ocean, sea, waves, water, ripples, puddle, photorealistic")

STYLES = [
    ("molten wax",
     "vanitas, a face slowly melting like molten wax and warm honey, viscous "
     "dripping, soft gooey forms, dreamlike oneiric surreal, baroque, luminous "
     "monochrome with gold, soft focus"),
    ("gooey chrome/glass",
     "vanitas, face and skull dissolving into gooey molten glass and liquid "
     "chrome, iridescent oily sheen, slow viscous morph, surreal weird dream, "
     "ethereal, dark baroque, gold flecks"),
    ("soft dream flesh",
     "vanitas, soft gooey pearl and flesh melting together, slow dripping, hazy "
     "oneiric dream, weird gentle surreal forms, ethereal smoke, monochrome "
     "with gold, very soft focus"),
]

def slerp(t, a, b, eps=1e-6):
    af, bf = a.flatten(), b.flatten()
    om = torch.acos(torch.clamp(torch.dot(af/af.norm(), bf/bf.norm()), -1+eps, 1-eps))
    so = torch.sin(om)
    if so.abs() < eps: return (1-t)*a + t*b
    return (torch.sin((1-t)*om)/so)*a + (torch.sin(t*om)/so)*b

print("loading pipe…")
pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    MODEL, torch_dtype=torch.float32, safety_checker=None, requires_safety_checker=False)
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
pipe.load_lora_weights(LCM); pipe.fuse_lora(); pipe = pipe.to(device)
pipe.set_progress_bar_config(disable=True)
pipe.enable_attention_slicing(); pipe.enable_vae_slicing()
vae, SCALE = pipe.vae, pipe.vae.config.scaling_factor

@torch.no_grad()
def enc(p):
    im = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS)
    a = torch.from_numpy(np.asarray(im,np.float32)/127.5-1).permute(2,0,1).unsqueeze(0)
    return vae.encode(a.to(device)).latent_dist.mean * SCALE
@torch.no_grad()
def dec(l):
    im = ((vae.decode(l/SCALE).sample.clamp(-1,1)+1)/2)[0].permute(1,2,0).cpu().numpy()
    return Image.fromarray((im*255).round().astype(np.uint8))

srcs = sorted(glob.glob(os.path.join(SRC, "*.png")))
la, lb = enc(srcs[KEY_A]), enc(srcs[KEY_B])
base = dec(slerp(U_POINT, la, lb))
base.save(os.path.join(HERE, "dream_base.png"))

cell=(300,225); pad=26
grid=Image.new("RGB",(cell[0]*len(STRENGTHS), (cell[1]+pad)*len(STYLES)+pad),"black")
d=ImageDraw.Draw(grid)
for r,(name,prompt) in enumerate(STYLES):
    d.text((8, r*(cell[1]+pad)+6), f"{r+1}. {name}", fill="white")
    for c,s in enumerate(STRENGTHS):
        g=torch.Generator(device=device).manual_seed(7)
        img=pipe(prompt=prompt, negative_prompt=NEG, image=base, strength=float(s),
                 num_inference_steps=INFER, guidance_scale=GUID, generator=g).images[0]
        if device=="mps": torch.mps.empty_cache()
        grid.paste(img.resize(cell),(c*cell[0], r*(cell[1]+pad)+pad))
        d.text((c*cell[0]+6, r*(cell[1]+pad)+pad+4), f"str {s}", fill="gold")
        print(f"  row{r+1} {name} str{s} done", flush=True)
out=os.path.join(HERE,"dream_styles_grid.png"); grid.save(out)
print("wrote", out)
