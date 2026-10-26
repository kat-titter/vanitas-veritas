#!/usr/bin/env python3
# The latent toolkit the dream scripts share: the curves a walk follows through Stable Diffusion's latent space, and the VAE's
# way in and out. Used by sink.py (the live water) and by morph_v44.py and morph_v45_sr.py (the loop's render).
import numpy as np, torch
from PIL import Image

def slerp(t, a, b, eps=1e-6):
    """Along the great circle from a to b; a straight line when the two point the same way."""
    af, bf = a.flatten(), b.flatten()
    om = torch.acos(torch.clamp(torch.dot(af/af.norm(), bf/bf.norm()), -1 + eps, 1 - eps)); so = torch.sin(om)
    if so.abs() < eps: return (1 - t)*a + t*b
    return (torch.sin((1 - t)*om)/so)*a + (torch.sin(t*om)/so)*b

def catmull(u, p0, p1, p2, p3):
    """Catmull-Rom: through p1 at u=0 and p2 at u=1, leaving each knot the way it arrived."""
    u2, u3 = u*u, u*u*u
    return 0.5*((2*p1) + (-p0 + p2)*u + (2*p0 - 5*p1 + 4*p2 - p3)*u2 + (-p0 + 3*p1 - 3*p2 + p3)*u3)

class Vae:
    """The VAE's way in (a picture already at the working size) and out (a picture)."""
    def __init__(self, vae, dev):
        self.vae, self.dev, self.sc = vae, dev, vae.config.scaling_factor
    @torch.no_grad()
    def enc(self, im):
        a = torch.from_numpy(np.asarray(im.convert('RGB'), np.float32)/127.5 - 1)
        return self.vae.encode(a.permute(2, 0, 1).unsqueeze(0).to(self.dev)).latent_dist.mean*self.sc
    @torch.no_grad()
    def dec_array(self, z):                         # HxWx3 float 0..255
        return ((self.vae.decode(z/self.sc).sample.clamp(-1, 1) + 1)/2)[0].permute(1, 2, 0).cpu().numpy()*255
    def dec(self, z):
        return Image.fromarray(self.dec_array(z).round().astype(np.uint8))
