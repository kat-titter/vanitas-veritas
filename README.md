# vanitas_veritas

**No water, no dream.** A sink you can't wash your hands in: its water is a GPU dreaming vanitas still lifes without end, poured from the tap to the drain. By Katherine Titterton, San Francisco, 2026.

Three documents, each linking the others:

- [**the doc**](https://kat-titter.github.io/vanitas-veritas/documents/Vanitas%20Veritas%20-%20Web.dc.html): the piece, [how the water is made](https://kat-titter.github.io/vanitas-veritas/documents/Vanitas%20Veritas%20-%20Web.dc.html#basin), the price; print it for a submission
- [**the build guide**](https://kat-titter.github.io/vanitas-veritas/documents/Vanitas%20Veritas%20-%20Build%20Guide.dc.html): parts, wiring, setup and upkeep
- [**the black paper**](https://kat-titter.github.io/veritas/blackpaper.html): the thesis, where it goes, and texts and a rider for hosts and juries

The water itself, live: [**veritas**](https://kat-titter.github.io/veritas/).

## Two pieces, one water

- **vanitas** is the sink: a freestanding stainless-steel sink with a self-portrait above it, designed and not yet built (first for tiat's *Epistemologies of Slop*, 2026). Real water lies over a screen in its bowl, and the tap runs; an old MacBook Pro under it dreams the picture.
- **veritas** is the same basin on the web, [`verse/sync.html`](verse/sync.html). A hand in either moves the water in both, over public Nostr relays.
- **The faucet handle is the tap.** Hold it and generation stops, and every basin drains.

## Kept small, kept running

Each choice was measured on an Apple M5 with 16 GB.

- **2.3 GB of GPU memory**: the model in half precision; only the decoder in full, which keeps colours clean.
- **Memory handed back** after every dream and stretch: the process went from 10 GB to 5.8 GB.
- **The upscaler in its own process**, on the Neural Engine: Core ML holds Python's lock, so it cannot share one with the dreaming.
- **No black frames**: attention slicing turns fp16 dreams to NaN on Apple GPUs, so it is off, and an empty dream raises instead of pouring.
- **It keeps flowing**: a GPU error restarts from the last dream; a stalled upscaler gives a plainly enlarged frame and restarts; six frames wait in a queue poured every 2.5 to 3.5 s.
- **Little kept**: the last 60 frames on disk; prompts walked by a stride, never stored; the place in them survives a restart.
- **Little shown**: the spring serves only the page, the newest-frame note and the frames, never its key or its state.

## Run it

On any Apple-silicon Mac:

```bash
caffeinate -i python3 code/sink.py            # veritas at http://127.0.0.1:8770/
caffeinate -i python3 code/sink.py --public   # and to everyone, through a Cloudflare quick tunnel
```

On the sink's own MacBook Pro, for good (the build guide walks through it):

```bash
bash code/setup_sink.sh     # packages, models, cloudflared, two test dreams
bash code/sink.sh install   # the spring and the full-screen page, at every login
```

The moodboard lives in `source/moodboard/` and the Real-ESRGAN weights in `code/models/` (both local only). `--public` writes each new tunnel address to `verse/spring.json`, so the plain veritas address finds the water. Midjourney pictures saved by hand to `source/mj_inbox/` become the next dream.

## Files

| path | what it is |
|---|---|
| [`code/sink.py`](code/sink.py) | the spring: dreams, walks, upscales, pours, serves veritas |
| [`code/upscale.py`](code/upscale.py) | Real-ESRGAN x4: Neural Engine for the spring, GPU for the loop |
| [`code/latent.py`](code/latent.py), [`code/harmonize.py`](code/harmonize.py) | slerp, Catmull-Rom and the VAE's way in and out; the palette lock |
| [`code/setup_sink.sh`](code/setup_sink.sh), [`code/sink.sh`](code/sink.sh) | the sink's computer: install once, then run for good |
| [`code/morph_v44.py`](code/morph_v44.py), [`code/morph_v45_sr.py`](code/morph_v45_sr.py), [`code/order_preview.py`](code/order_preview.py) | the 2026 loop the spring grew from (rendered with the `render-loop` skill in `.claude/skills/`) |
| [`verse/sync.html`](verse/sync.html) | veritas: one page, WebGL2, no build step |
| [`verse/blackpaper.html`](verse/blackpaper.html), [`verse/deploy_verse.py`](verse/deploy_verse.py) | the black paper, and the script that publishes it and veritas at their short address |
| [`documents/`](documents/) | the doc and the build guide, with their pictures |

## Colophon

Stable Diffusion 1.5 with LCM-LoRA, Real-ESRGAN, stable fluids (Stam, 1999); Midjourney for the style, by hand. Built with Claude and Claude Code. Code under the [MIT License](LICENSE); the images are the artist's.
