#!/usr/bin/env python3
# Real-ESRGAN x4: a graded 640 x 480 frame becomes 2560 x 1920, as the final loop was made (morph_v45_sr.py), from
# code/models/RealESRGAN_x4plus.pth. The spring runs it in a process of its own on the Mac's Neural Engine (Core ML), so the
# GPU keeps dreaming; the render runs it on the GPU (esrgan_gpu).
#   python3 code/upscale.py        build the Neural Engine copy of the model once (code/models/, outside git; ~20 s)
import os, time
HERE = os.path.dirname(os.path.abspath(__file__))
WEIGHTS = os.path.join(HERE, 'models', 'RealESRGAN_x4plus.pth')
PACKAGE = os.path.join(HERE, 'models', 'RealESRGAN_x4plus_640x480.mlpackage')
W, H = 640, 480

def esrgan_gpu(dev):
    """The model on the GPU in fp16: HxWx3 float 0..255 in, 4x the size out (the render's own path)."""
    import torch
    from spandrel import ModelLoader
    net = ModelLoader().load_from_file(WEIGHTS).to(dev).eval(); net.model.half()
    @torch.no_grad()
    def run(x):
        t = torch.from_numpy(x/255).permute(2, 0, 1).unsqueeze(0).to(dev, torch.float16)
        return net(t)[0].float().clamp(0, 1).permute(1, 2, 0).cpu().numpy()*255
    return run

def build():
    """Convert the model for Core ML at the spring's frame size. Traced small with gradients off (a full-size trace keeps every
    activation and runs out of memory); the network is all convolutions, so the size is set at conversion."""
    import torch, coremltools as ct
    from spandrel import ModelLoader
    net = ModelLoader().load_from_file(WEIGHTS).model.eval().float()
    with torch.no_grad(): tr = torch.jit.trace(net, torch.rand(1, 3, 64, 64))
    ml = ct.convert(tr, inputs=[ct.TensorType(name='x', shape=(1, 3, H, W))], outputs=[ct.TensorType(name='y')],
                    convert_to='mlprogram', compute_precision=ct.precision.FLOAT16, minimum_deployment_target=ct.target.macOS15)
    ml.save(PACKAGE)

def _work(conn):
    """The upscaler's own process: Core ML holds Python's lock while it runs, so it cannot share one with the dreaming."""
    import numpy as np
    from PIL import Image
    try:
        import coremltools as ct
        if not os.path.exists(PACKAGE): build()
        m = ct.models.MLModel(PACKAGE, compute_units=ct.ComputeUnit.CPU_AND_NE); how = 'Neural Engine'
        def run(im):
            y = m.predict({'x': (np.asarray(im, np.float32)/255).transpose(2, 0, 1)[None]})['y'][0]
            return np.clip(y.transpose(1, 2, 0), 0, 1)*255
    except Exception as e:                          # no Core ML: the GPU, slower, sharing time with the dreams
        import torch
        gpu = esrgan_gpu('mps' if torch.backends.mps.is_available() else 'cpu'); how = f'GPU ({e.__class__.__name__})'
        def run(im): return gpu(np.asarray(im, np.float32))
    conn.send(how)
    while True:
        try: data, size, big, small = conn.recv()
        except (EOFError, OSError): return          # the spring has stopped
        try:
            out = Image.fromarray(run(Image.frombytes('RGB', size, data)).round().astype(np.uint8))
            out.save(big, quality=86); out.resize((out.width//2, out.height//2), Image.LANCZOS).save(small, quality=86)
            conn.send('ok')
        except Exception as e: conn.send(f'error: {e}')

class Upscaler:
    """write(im, big, small): the 4K frame and its 1280 x 960 copy for small screens. If the upscaler fails, the frame is
    enlarged plainly and the upscaler is started again: the water never stops for it."""
    def __init__(self):
        self.proc = None; self.start()
    def start(self):
        import multiprocessing as mp
        ctx = mp.get_context('spawn'); self.conn, child = ctx.Pipe()
        self.proc = ctx.Process(target=_work, args=(child,), daemon=True); self.proc.start()
        self.how = self.conn.recv() if self.conn.poll(180) else 'not started'
        if self.how == 'not started': self.proc.kill()   # a late reply would be read as the next frame's answer
        print(f'upscale: Real-ESRGAN x4 on the {self.how}', flush=True)
    def write(self, im, big, small):
        from PIL import Image
        im = im.convert('RGB')
        try:
            self.conn.send((im.tobytes(), im.size, big, small))
            if self.conn.poll(20) and self.conn.recv() == 'ok': return
        except Exception: pass
        print('upscale: failed; this frame enlarged plainly, the upscaler restarted', flush=True)
        out = im.resize((im.width*4, im.height*4), Image.LANCZOS); out.save(big, quality=86)
        out.resize((im.width*2, im.height*2), Image.LANCZOS).save(small, quality=86)
        try: self.proc.kill(); self.conn.close()
        except Exception: pass
        self.start()

if __name__ == '__main__':
    t0 = time.time(); build(); print(f'built {PACKAGE} in {time.time() - t0:.0f}s')
