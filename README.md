# vanitas_veritas

**A sink you can't wash your hands in.** Its water is a GPU dreaming vanitas still lifes without end, poured from the tap to the drain: no GPU, no water, no dream. By Katherine Titterton, San Francisco, 2026.

[the tiat doc](https://kat-titter.github.io/vanitas-veritas/documents/Vanitas%20Veritas%20-%20Web.dc.html)&emsp;[how the water is made](https://kat-titter.github.io/vanitas-veritas/documents/Vanitas%20Veritas%20-%20Web.dc.html#basin)&emsp;[the black paper](verse/blackpaper.html)&emsp;[veritas, at sink==sync](https://kat-titter.github.io/vanitas-veritas/sink==sync/)

---

## 1. Two pieces, one water

- **vanitas** is the sink: a stainless-steel sink with a self-portrait above it, designed in 2026 for tiat's *Epistemologies of Slop*, and a stone one, proposed. A touch screen lies in its bowl.
- **veritas** is the same basin on the web, [`verse/sync.html`](verse/sync.html). A hand in either moves the water in both, over public Nostr relays.
- **The handle is the water.** Turn it off and the dream fades away.

## 2. How the water is made

| | step | what runs | time |
|---|---|---|---|
| 01 | historical style | six vanitas paintings, the references for the style | |
| 02 | Midjourney style | the self-portrait as style reference, a profile, an eight-picture moodboard; by hand, never automated | once |
| 03 | the prompt | a grammar, not a language model: 1.3 million prompts, about five years before any repeat | instant |
| 04 | the dream | Stable Diffusion 1.5 + LCM-LoRA, image to image from the last dream, pulled toward a moodboard picture; fp16 on the GPU | about 4 s |
| 05 | the walk | three dreamed waypoints and one Catmull-Rom path; 48 frames from dream to dream | about 2 min |
| 06 | upscaling | Real-ESRGAN x4plus as Core ML on the Neural Engine, 640 × 480 to 2560 × 1920 | 0.76 s |
| 07 | the water | stable fluids in WebGL2 in the viewer's browser; the frame is the dye | a frame every 2.5 to 3.5 s |

## 3. Kept small, kept running

Everything is built to run on one Mac mini with 16 GB, its own, under the sink's bowl. Each choice was measured on an Apple M5 with 16 GB.

- **2.3 GB of GPU memory**: the model in half precision; only the decoder in full, which keeps colours clean.
- **Memory handed back** after every dream and stretch: the process went from 10 GB to 5.8 GB.
- **The upscaler in its own process**, on the Neural Engine: Core ML holds Python's lock, so it cannot share one with the dreaming.
- **No black frames**: attention slicing turns fp16 dreams to NaN on Apple GPUs, so it is off, and an empty dream raises instead of pouring.
- **It keeps flowing**: a GPU error restarts from the last dream; a stalled upscaler gives a plainly enlarged frame and restarts; six frames wait in a queue poured every 2.5 to 3.5 s.
- **Little kept**: the last 60 frames on disk; prompts walked by a stride, never stored; the place in them survives a restart.
- **Little shown**: the spring serves only the page, the newest-frame note and the frames, never its key or its state.

## 4. Run it

```bash
caffeinate -i python3 code/sink.py            # veritas at http://127.0.0.1:8770/
caffeinate -i python3 code/sink.py --public   # and to everyone, through a Cloudflare quick tunnel
```

Needs Python 3 with `torch diffusers transformers peft spandrel coremltools opencv-python pillow`, the Real-ESRGAN weights in `code/models/`, and the moodboard in `source/moodboard/` (both local only). `--public` needs `cloudflared`; its address changes each run. Midjourney pictures saved by hand to `source/mj_inbox/` become the next dream.

## 5. Files

| path | what it is |
|---|---|
| [`code/sink.py`](code/sink.py) | the spring: dreams, walks, upscales, pours, serves veritas |
| [`code/latent.py`](code/latent.py) | slerp, Catmull-Rom and the VAE's way in and out, shared with the loop |
| [`code/upscale.py`](code/upscale.py) | Real-ESRGAN x4: Neural Engine for the spring, GPU for the loop |
| [`code/harmonize.py`](code/harmonize.py) | the palette lock: cool silver, gold only where the picture was warm |
| [`verse/sync.html`](verse/sync.html) | veritas: one page, WebGL2, no build step |
| [`documents/`](documents/) | the tiat submission, web doc and build guide |
| [`verse/`](verse/) | the black paper, pitch, proposal, vanitas, and the earlier pieces i, ii, iii |
| [`code/LOOP.md`](code/LOOP.md) | the loop of 2026 and how it was made (`morph_v44.py`, `morph_v45_sr.py`, `order_preview.py`) |

## 6. Colophon

Stable Diffusion 1.5 with LCM-LoRA, Real-ESRGAN, stable fluids (Stam, 1999); Midjourney for the style, by hand. Built with Claude and Claude Code. Code under the [MIT License](LICENSE); the images are the artist's.
