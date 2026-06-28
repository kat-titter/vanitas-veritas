---
name: render-loop
description: Render the Vanitas/Veritas video loop — run the diffusion morph pipeline (dream + cache anchors, then decode + Real-ESRGAN 4x super-res) to produce the seamless loop. Use when asked to render, re-render, produce a new version, or change the speed/order/grade of the vanitas loop in this project.
when_to_use: Whenever producing or re-producing the vanitas loop video, or changing M (speed), ORDER (loop order), strength, or grade and re-rendering.
---

## Architecture (decoupled: LOOK vs MOTION)

Two stages, anchors cached so re-renders are cheap:

1. **Dream + cache anchors** — `code/morph_v44.py` dreams a sparse ring of img2img
   anchors from `source/veritas/*.png` and caches them to `code/anchors_final.pt`.
2. **Decode + super-res** — `code/morph_v45_sr.py` reuses the cached anchors,
   Catmull-decodes the slow loop, runs **Real-ESRGAN 4x** → 2560×1920, encodes to
   `video/veritas_loop_v45_*.mp4`.

## Always wrap in `caffeinate` (this is a multi-hour job)

A full 4K render is ~6.7 h *if the Mac stays awake*; if it sleeps it idle-throttles
to a crawl (see the `macos-long-render` skill). So:

```bash
cd code
caffeinate -dimsu python3 morph_v45_sr.py            # full 4K (M=190 default), reuses cache
caffeinate -dimsu python3 morph_v45_sr.py 19 preview # 10% preview (M=19), fast check
```
Keep it plugged in, lid open.

## When to re-dream anchors (`--fresh`)

Re-dream (`python3 morph_v44.py --fresh`) ONLY if the **source frames**, **loop
order**, **strength** (LOW_STR/HIGH_STR), or **D** changed. Otherwise reuse the
cache — just re-run `morph_v45_sr.py`.

## Knobs

- `morph_v44.py`: `ORDER` (loop order, sorted-index list), `M` (frames/gap →
  speed/length), `D` (anchors/segment), `LOW_STR`/`HIGH_STR`, the prompt, palette
  + grade constants (`COOL`, `GOLD_TONE`, `CONTRAST`, …). Current final order:
  `[0,1,4,3,2,7,6,5]`.
- `morph_v45_sr.py`: `M` (default 190 ≈ 8:30 loop), output naming via argv.
- Fast loop-**order** iteration without the full render: `code/order_preview.py`
  (VAE-only proxy, ~1 min/candidate).

## Verify after render

```bash
ffmpeg -v error -i video/veritas_loop_v45_4k.mp4 -f null -   # decode clean?
ffmpeg -i video/veritas_loop_v45_4k.mp4 2>&1 | grep -E "Duration|Stream"
```
Player shows a white box for raw-pipe mp4s on this Mac → the script already encodes
`-profile:v high/main +faststart`; if needed re-encode or make a GIF.
