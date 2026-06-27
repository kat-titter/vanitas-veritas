#!/usr/bin/env python3
"""
harmonize — unify warmth/contrast/palette across the whole image set
(8 veritas frames + the 2 self-portraits) so they read as one cohesive body.

Same palette-lock logic as the render grade: luminance -> cool monochrome base,
with goldish-orange re-introduced only where the SOURCE was warm. Plus a contrast
S-curve. Tunables at top. Writes a contact sheet for judging cohesion, and a
before/after for the two portraits (which change most).
"""
import os, glob, numpy as np
from PIL import Image, ImageDraw

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
SRC=os.path.join(ROOT,"source")

# ---- harmonization grade tunables ----
COOL       = (0.93, 0.98, 1.09)   # cool/blue tint of the monochrome base
GOLD_TONE  = (1.22, 0.80, 0.30)   # goldish-orange for warm accents
WARM_SCALE = 40.0                 # source R-B above this => full gold accent
CONTRAST   = 1.30                 # S-curve steepness (>1 = more contrast)
BLACK_GAMMA= 1.18                 # deepen blacks
GAIN       = 1.05

def harmonize(img):
    x=np.asarray(img.convert("RGB"),np.float32)
    warm=np.clip((x[...,0:1]-x[...,2:3])/WARM_SCALE,0,1)          # source warmth -> gold mask
    lum=0.299*x[...,0:1]+0.587*x[...,1:2]+0.114*x[...,2:3]
    x=(1-warm)*(lum*np.array(COOL))+warm*(lum*np.array(GOLD_TONE))# cool base + gold accent
    n=np.clip(x/255,0,1)
    n=1/(1+np.exp(-CONTRAST*4*(n-0.5)))                          # contrast S-curve
    n=n**BLACK_GAMMA*GAIN                                         # deepen blacks
    return Image.fromarray(np.clip(n,0,1).astype(np.float32).__mul__(255).astype(np.uint8))

if __name__=="__main__":
    veritas=sorted(glob.glob(os.path.join(SRC,"veritas","*.png")))
    real=os.path.join(SRC,"IMG_6975.jpeg")
    mirror=glob.glob(os.path.join(SRC,"*wash_your_hands*.png"))[0]
    allimgs=veritas+[real,mirror]
    labels=[f"v{i}" for i in range(len(veritas))]+["SELF real","SELF mirror"]

    # cohesion contact sheet (all harmonized together)
    cell=(240,180); cols=5; rows=2; pad=18
    sheet=Image.new("RGB",(cols*cell[0],rows*(cell[1]+pad)),"black"); d=ImageDraw.Draw(sheet)
    for i,(f,lab) in enumerate(zip(allimgs,labels)):
        h=harmonize(Image.open(f)).resize(cell)
        x=(i%cols)*cell[0]; y=(i//cols)*(cell[1]+pad)+pad
        sheet.paste(h,(x,y)); d.text((x+4,y-15),lab,fill="gold")
    sheet.save("/tmp/harmonized_set.png")

    # before/after for the two portraits
    ba=Image.new("RGB",(cell[0]*2,(cell[1]+pad)*2),"black"); d=ImageDraw.Draw(ba)
    for r,(f,lab) in enumerate([(real,"real"),(mirror,"mirror")]):
        ba.paste(Image.open(f).convert("RGB").resize(cell),(0,r*(cell[1]+pad)+pad))
        ba.paste(harmonize(Image.open(f)).resize(cell),(cell[0],r*(cell[1]+pad)+pad))
        d.text((4,r*(cell[1]+pad)+2),f"{lab}: BEFORE  |  AFTER",fill="gold")
    ba.save("/tmp/harmonize_portraits_ba.png")
    print("wrote /tmp/harmonized_set.png and /tmp/harmonize_portraits_ba.png")

    # --- save FULL-RES harmonized versions (the modification, persisted) ---
    outdir=os.path.join(SRC,"harmonized"); os.makedirs(outdir,exist_ok=True)
    for f in allimgs:
        h=harmonize(Image.open(f))
        base=os.path.splitext(os.path.basename(f))[0]+"_harmonized.png"
        h.save(os.path.join(outdir,base))
    print(f"saved {len(allimgs)} full-res harmonized images -> {outdir}")
