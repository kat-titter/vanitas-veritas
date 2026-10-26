# vanitas_veritas

A sink you can't wash your hands in. Its water is a GPU dreaming: a new
vanitas prompt, dreamed and walked into the next, never the same twice,
pouring from the tap to the drain. Reach in and it slips through your fingers.
Switch the GPU off: no water, no dream. One work in two places with one water:
vanitas, the sink (a stone basin, proposed; first designed in 2026 as a
stainless-steel sink for tiat), and veritas, the same basin on the web.

- [the black paper](https://kat-titter.github.io/vanitas_veritas_verse/blackpaper.html)
- [vanitas](https://kat-titter.github.io/vanitas_veritas_verse/sink.html) (proposed)
- [the live web piece](https://kat-titter.github.io/vanitas_veritas_verse/) (iii, the earlier web piece, until veritas is on the web)

Kat Titterton (macrofluidic)

---

## Thesis

no water, no dream: the water in the basin is a GPU dreaming. While it dreams,
the tap runs; switch it off and the basin drains.

you can't wash your hands of it: reach in, and the water under your hand goes
where your hand goes, then slips through your fingers, down the drain.

sink == sync: vanitas and veritas hang from one spring, and a hand in either
moves the water in both. The two names are one swap of letters apart, as
`sink` and `sync` are one sound apart: one water.

## The spring and veritas

`code/spring.py` is the spring: Stable Diffusion 1.5 with LCM-LoRA on a GPU,
for now Kat's Mac. It writes a new prompt in the grammar of the Midjourney
recipe `vanitas [flower, skull, soap bubble]`, never repeating until all 808
are used, and dreams it pulled back toward Kat's vanitas moodboard
(`source/moodboard/`). On the way to the next dream it dreams three more places
and glides through all of them on one Catmull-Rom path (the walk of the v44
loop), so forms melt instead of fading. Every frame is enlarged to 2560×1920 by
Real-ESRGAN on the Mac's Neural Engine while the GPU dreams on, with a 1280×960
copy for phones: a frame every two to three seconds. A picture Kat makes by hand
in Midjourney and saves to `source/mj_inbox/` becomes the next dream, with the
prompt read from its own metadata (nothing here calls Midjourney). Frames land
in `spring_feed/`, outside git, beside the key only vanitas holds.

`verse/sync.html` is veritas: a 4:3 rectangle with rounded corners, like the
frames. Press, and the water under your hand moves
with it, then slips away (`grip = 0.55` after one second). The space bar is
the plug. When the spring stops, the tap closes and the basin drains
(`water = None`). A touch in any basin travels as an anonymous, ephemeral
event over public Nostr relays and moves the water in every other basin.

```bash
caffeinate -i python3 code/spring.py            # then open http://127.0.0.1:8770/
caffeinate -i python3 code/spring.py --public   # and to everyone: a quick tunnel from this Mac, address printed
```

veritas and the spring are built and run together on Kat's Mac, and veritas is
public whenever the spring runs with `--public` (a Cloudflare quick tunnel; the
address changes each time). The published site shows the earlier piece, iii,
until the spring has a lasting address. The earlier web pieces, i, ii and iii,
are kept as they were.

**vanitas (proposed).** A basalt column with the basin as its screen, under
ribbed glass that answers a touch. A small camera where a tap would stand,
woken only when someone holds its eye on the glass for two seconds (touching
the water never wakes it), gives one frame of a face to the next dream, used
once and never written down.
The lever is the tap: down, the spring rests and the water runs out in vanitas
and in every veritas. A QR code cut into the basalt opens veritas. vanitas is
proposed first for San Francisco; nothing physical is built or confirmed, though
its mode in veritas is built. The design is
in [sink.html](https://kat-titter.github.io/vanitas_veritas_verse/sink.html).
The 2026 design of vanitas for tiat's open call, a stainless-steel sink under a
self-portrait, is in `documents/`.

---

## The loop (2026)

Where the work began. The spring is this loop, opened: it no longer comes
back. Its eight source frames are the frames the water leans toward.

### 1. The artifact

- **Form:** a single seamless video loop, designed to play on repeat
  indefinitely (gallery / installation context).
- **Final render:** `video/veritas_loop_v45_4k.mp4`, 8 min 27 s, **2560×1920**
  (Real-ESRGAN 4× super-res), 12 fps, H.264.
  *(Earlier 1920×1440 cut `video/veritas_final_v44.mp4`, 2:51, kept as a fallback. Both renders are local only.)*
- **Loop:** mathematically seamless: the last frame eases back into the first,
  so there is no visible cut or "reset." Watched long enough, the loop point
  dissolves and it reads as endless.
- **Source:** eight AI-generated vanitas frames (`source/veritas/`), 2544×1904, 4:3.

### 2. Concept

**Vanitas** is the classical still-life genre of *memento mori*: skulls, guttering
candles, and **soap bubbles** as emblems of the fragility and transience of life
(*homo bulla*, "man is a bubble"). This piece takes that vocabulary and runs it
through the dream-logic of a diffusion model: a face becomes a skull becomes a
swelling bubble that you worry might pop, becomes gold dust, becomes a face
again. Nothing holds its form; everything is mid-dissolve.

The title pun, **Vanitas / Veritas** (vanity / truth), frames the loop as a
meditation: the "truth" underneath the vanity is that all of it is in flux, a
slow churn of becoming and un-becoming. The aesthetic is deliberately **"slop"**
(the gooey, melty, half-hallucinated texture native to generative models) but
treated with restraint and luxury so it reads as intentional and beautiful
rather than accidental.

**Intended viewing:** ambient and meditative, something you can watch for
minutes at a time, getting lost in.

#### Art-directed feeling (the words that drove the final look)
liquid, gooey, clear (not hazy), endless, lost, *slooow building bubble you
worry might pop*, luxury, simultaneously clean and dirty.

### 3. Source material

Eight vanitas portraits generated in **Midjourney** (`source/veritas/*.png`),
sharing a tight visual language that makes them ideal for morphing: faces and
skull-profiles dissolving into particles, the white flower/bloom frames, and a
*daisy-skull-bubble* frame that holds the whole vanitas trinity (flower + skull +
bubble) in a single image:

- a central face or skull on a deep black ground;
- the figure dissolving into **beaded particles, soap bubbles, and foam**;
- sprays and flecks of **gold** light;
- a luminous, near-monochrome palette with warm gold accents.

Because every frame is *already* a portrait caught mid-dissolution, the
transitions between them feel native rather than forced; the morph is just
continuing a dissolution the source images began.

### 4. How it works: dreamed anchors and smooth drift

The core engine (`code/morph_v44.py`) is built around one idea: **decouple what
the loop looks like from how it moves.**

Naive approaches (re-dreaming every single frame, or warping pixels with a
displacement field) fail in characteristic ways: independent per-frame
diffusion makes fine detail *boil/flicker* (reads as frantic), and periodic
displacement fields read as literal *waves/water*. Both were tried and rejected.

The final architecture instead does this:

1. **Dream a sparse ring of "anchor" frames.** Around the loop, at evenly spaced
   points, a Stable Diffusion **img2img** pass re-imagines a blended source
   image into the target style. Anchors *at* the original source positions are
   only lightly dreamed (so the source remains **discernible**); anchors
   *between* sources are dreamed harder (so they become **gooey, abstract,
   weird**). This rhythm produces the "sometimes recognizable, sometimes lost"
   quality. Anchors are encoded to latent space and **cached** to disk
   (`code/anchors_final.pt`).

2. **Interpolate, don't re-dream.** Between consecutive anchors, the latent
   vectors are blended along a **Catmull-Rom spline** (a smooth curve that
   passes *through* each anchor without stopping or kinking) and simply
   **decoded**. Decoding is deterministic, so the motion is **glassy-smooth with
   zero flicker**, and it is cheap (~1 s/frame), which means many slow frames
   can be packed between anchors. Slowness and length are free.

3. **Grade, don't warp.** A light color/finish pass (no geometric distortion at
   all) gives the final look: a faint dream-softness, a glossy specular bloom
   (wet luxury sheen), deepened blacks, a **palette lock** (cool monochrome base
   with goldish-orange accents isolated to the regions that were warm in the
   source), fine film grain, and a grime vignette. This is where **clear +
   luxurious + "clean and dirty"** come from.

Because the expensive diffusion only happens on 32 cached anchors, the loop's
length, slowness, resolution, and grade can all be re-tuned by re-running only
the cheap decode+grade stage.

#### Pipeline at a glance

```mermaid
flowchart TD
    A["8 source veritas frames"] -->|"VAE encode"| B["source latents"]
    B -->|"apply loop order + blend pairs"| C["blended latents"]
    C -->|"img2img, LCM few-step<br/>low strength at sources (discernible)<br/>high strength between (gooey)"| D[("32 dreamed anchors<br/>cached to disk")]
    D -->|"Catmull-Rom latent spline<br/>+ VAE decode, 190 frames/gap"| E["6080 decoded frames @640×480"]
    E -->|"colour grade: palette lock + contrast<br/>gloss, deep blacks"| F["graded frames"]
    F -->|"Real-ESRGAN 4×"| H["upscaled frames @2560×1920"]
    H -->|"finish: grain + vignette (full-res)"| I["finished frames"]
    I -->|"ffmpeg H.264"| G["seamless 2560×1920 loop, 8:27"]

    subgraph EXPENSIVE [" runs once, cached "]
      C; D
    end
    subgraph CHEAP [" re-tunable cheaply: length, grade, super-res "]
      E; F; H; I; G
    end
```

### 5. Process / evolution (the making-of)

The piece went through a deliberate, feedback-driven iteration:

1. **v1: per-frame melt.** Latent SLERP between the 8 frames with a per-frame
   img2img "re-dream" peaking at each transition midpoint. Beautiful stills, but
   it (a) *paused* on each keyframe (an easing artifact) and (b) boiled/flickered.
2. **Never-still pass.** Replaced the easing with a Catmull-Rom spline through
   the latents so motion never stops, important because, in the intended
   installation, the *only* still moment is a physical pause.
3. **Liquify experiments.** A post-process displacement field was tried for
   "liquid", but periodic waves read as *ocean/puddle*. Rejected. Key
   correction: the desired texture is **bubbly** (rounded, soap-film, foam), not
   **wavy**. No displacement warps in the final.
4. **Grid search on style.** A 3×3 sweep (prompt family × img2img strength)
   established that strength **~0.6** is the gooey sweet spot; higher (~0.78)
   resolves into crisp marble busts/skulls (too hard), lower (~0.45) barely
   departs from the source.
5. **v3: "Dreamed Anchors."** The architecture above; solved the flicker and
   the waviness in one move (smoothness now comes from *interpolation*, not
   warping).
6. **v4: final grade + direction.** Tuned to the art-direction words in §2:
   removed the hazy fog, deepened the blacks for luxury, added gloss + gold +
   grain + grime ("clean and dirty"), pushed the prompt toward liquid, swelling,
   about-to-pop bubbles, then slowed and lengthened the loop for the meditative,
   endless, "lost" feeling.
7. **v4.4: final tuning.** Slowed further (M=64) and made the transitions *more
   uncanny* by densifying and intensifying the dreamed waypoints (D=4, strength
   to 0.70), leaning into emergent hallucination rather than literal morphing.
   Added a **palette lock** to preserve the source's signature colour (a cool
   monochrome base with gold-orange accents) so the diffusion can't drift it.
   Settled here: the speed reads as "uncanny valley," the palette is intact.
8. **Loop ordering.** One source frame was swapped for a new
    *daisy-skull-bubble* image (the literal vanitas trinity: flower + skull +
    bubble in one). The **order** the eight frames cycle in is its own artistic
    variable: it sets the loop's flow, arc, and surprise. Two tools made this
    fast to iterate:
    - a **perceptual distance matrix** (downscaled, blurred luminance + a warm/gold
      map) over the eight frames, with a brute-force search for the smoothest
      Hamiltonian *cycle*, an objective measure of how seamless an ordering is;
    - a **fast preview harness** (`code/order_preview.py`) that morphs the *real*
      frames via VAE latent spline (no diffusion) at low res: ~1 min per candidate
      vs ~50 min for a full render, because the gooey look is identical across
      orderings; only the sequence changes.

    Three philosophies were compared: *smoothest* (pure minimal-jump), *vanitas
    narrative* (life → dissolution → death → bloom), and *bloom-climax* (the three
    flower frames clustered as a crescendo). They were then **combined by
    constrained optimisation**: solve for the smoothest order that is *required*
    to keep the narrative spine (skull → trinity-pivot → blooms) and the bloom
    cluster. The result has a deliberate dramatic shape (a calm, flowing opening
    that builds to a surprising bloom crescendo, then resets) rather than uniform
    smoothness.

9. **Harmonization.** Two **self-portraits** (a photographic "real" selfie and an
   AI-styled "mirror" one) were brought into the body of work as **stills, not
   loop frames**. The moving loop stays the **eight veritas frames**; the
   self-portraits live alongside it as harmonized submission imagery (the artist
   present at the edges of the work, not inside the dream). A single grade
   (`code/harmonize.py`) unifies the whole set (luminance → cool monochrome base,
   gold-orange re-introduced only where the source was warm, plus a contrast
   S-curve), so the warm photographic selfie now sits in the same palette and
   punch as the veritas frames. Full-res harmonized versions live in
   `source/harmonized/`, and the render pipeline's grade was aligned to the same
   constants so the moving loop matches the harmonized stills.

10. **Max-quality super-res (final).** The loop was slowed 3× more (M=190 →
    **6,080 frames, 8:27**) and every frame run through **Real-ESRGAN 4×**
    (`code/morph_v45_sr.py`, spandrel + `RealESRGAN_x4plus`, fp16) for a native
    **2560×1920** output, far cleaner than a lanczos upscale. The colour grade
    is applied *before* super-res and the **grain + vignette are re-added after**,
    at full resolution, so the "clean and dirty" texture survives the upscale
    instead of being smoothed away. The expensive anchors are reused from cache;
    only the decode + super-res stage re-runs (~6 hr overnight render).

### 6. Style notes

- **Palette:** a strict, locked profile: a **cool silver monochrome base** over
  deep velvety black, with **goldish-orange accents** isolated only to the regions
  that were warm in the source (the gold sprays and flecks). The diffusion cannot
  drift the colour; the white forms stay cool-white, the gold stays gold. Jewel-like,
  opulent, restrained.
- **Texture:** "clean and dirty": crisp, glossy, well-defined forms wearing a
  layer of fine grain and a grimy edge vignette. Pristine and decaying at once,
  which is itself a vanitas idea.
- **Motion:** very slow, continuous, smooth. Forms swell and ooze and dissolve;
  bubbles build with a faint tension. No stutter, no waves.
- **Legibility:** rhythmically in and out: a face or skull surfaces clearly,
  then loses itself in gooey abstraction, then re-forms.

### 7. Technical specifications (for caption / colophon)

| | |
|---|---|
| **Models (open-source)** | Stable Diffusion v1.5 + LCM-LoRA (`latent-consistency/lcm-lora-sdv1-5`); Real-ESRGAN x4plus (super-res) |
| **Frameworks** | 🤗 Diffusers, PyTorch (MPS), spandrel, scipy/PIL/NumPy, ffmpeg |
| **Hardware** | Apple M5, 16 GB, fully local (no cloud compute) |
| **Sampler** | LCMScheduler, 8 steps, guidance 1.5, fp32 |
| **Diffusion working resolution** | 640×480 (super-res to 2560×1920) |
| **img2img strength** | 0.42 at source anchors (discernible) → 0.70 between (gooey/uncanny) |
| **Loop order** | `0 → 1 → 4 → 3 → 2 → 7 → 6 → 5` (constrained-optimal: smoothest order keeping the narrative spine + bloom cluster) |
| **Loop structure** | 8 sources × 4 anchors = 32 dreamed anchors; Catmull-Rom interpolation; 190 decoded frames per anchor gap = 6,080 frames |
| **Interpolation** | spherical/Catmull-Rom blend in VAE latent space |
| **Finish** | colour grade (palette lock + contrast S-curve, gloss, deep blacks) → **Real-ESRGAN 4×** → grain + grime vignette (re-added at full res) |
| **Output** | **2560×1920**, 12 fps, 8 min 27 s, H.264 (seamless loop) |
| **Seed** | 7 (reproducible) |

---

## Folder layout

```
vanitas-veritas/
├── README.md, README.html         this document
├── LICENSE
├── index.html                     the loop's landing page (Submission, Web, Build Guide)
├── verse/                         veritas (sync.html), the doc for vanitas (sink.html), the black paper,
│                                  the pitch, the proposal; i, ii and iii, kept as they were
├── documents/                     the tiat submission bundle (Submission, Build Guide, Web; self-contained HTML + assets)
├── code/                          the spring, and the loop's pipeline
├── spring_feed/                   the spring's frames and the key only vanitas holds (local only)
├── video/                         the final render + basin loop
├── research/                      vanitas paper, references, ref images
├── source/                        source artwork (veritas frames + harmonized + self-portraits)
├── _order_tests/                  fast loop-order preview clips
└── _archive/                      superseded versions, frames, logs (kept, not deleted)
```

`video/`, `source/`, `research/`, `_order_tests/`, `_archive/`, `code/models/`,
`spring_feed/` and the cached anchors stay local. They are not in the public repo.

### Key files

| Path | Role |
|---|---|
| `code/spring.py` | **the spring**: dreams without end and serves veritas at http://127.0.0.1:8770/ (`--public` opens a tunnel) |
| `code/latent.py` | the latent toolkit the spring and the render share: slerp, Catmull-Rom, the VAE's way in and out |
| `code/upscale.py` | Real-ESRGAN 4×: on the Neural Engine for the spring (its own process), on the GPU for the render |
| `source/moodboard/` | the spring's taste: eight pictures from Kat's vanitas moodboard (local only) |
| `source/mj_inbox/` | Midjourney pictures Kat saves by hand; each becomes the next dream once (local only) |
| `verse/sync.html` | **veritas**, the basin on the web; inside vanitas, `sync.html?spring=<feed>&sink&camera&key=<spring_feed/key>` |
| `spring_feed/` | the spring's last sixty frames, `now.json`, and `key`, which only vanitas holds (local only) |
| `verse/blackpaper.html` | the black paper |
| `verse/pitch.html` | the pitch kit |
| `verse/sink.html` | the doc for vanitas, redesigned (proposed) |
| `verse/proposal.html` | the first proposal, 29 September, updated |
| `verse/veritas.html`, `veritas2.html`, `veritas3.html` | i, ii and iii, kept as they were; iii is on the site until the spring has a lasting address |
| `index.html` | the loop's landing page |
| `documents/Vanitas Veritas - Submission.dc.html` | the tiat submission (self-contained HTML) |
| `documents/Vanitas Veritas - Build Guide.dc.html` | the 2026 electronics guide (the first design of vanitas; the basalt one is `verse/sink.html`) |
| `documents/Vanitas Veritas - Web.dc.html` | the tiat web doc |
| `documents/assets/` | images/video the docs embed |
| `video/veritas_loop_v45_4k.mp4` | **the final render**, 2560×1920, 8:27 (local only) |
| `video/veritas_final_v44.mp4` | the earlier 1920×1440 cut (local only) |
| `video/Vanitas_Veritas_basin_loop.mp4` | the basin loop variant (local only) |
| `source/veritas/` | 8 source vanitas frames, Midjourney (local only) |
| `research/Vanitas_research_paper.pdf` | art-historical paper on the vanitas tradition (local only) |
| `research/vanitas_references/` | public-domain reference plates (local only) |
| `code/morph_v45_sr.py` | **the final render**: reuses anchors, decodes slow loop, Real-ESRGAN 4× → 2560×1920 |
| `code/morph_v44.py` | the dreamed-anchors engine (dreams and caches the anchors; 1920×1440 path) |
| `code/anchors_final.pt` | cached dreamed anchor latents, the expensive, reusable part (local only) |
| `code/models/RealESRGAN_x4plus.pth` | super-res weights, open-source; `upscale.py` builds the Neural Engine copy beside it (local only) |
| `code/archive/` | earlier experiments kept for the record: morph_loop, morph_v3, preview_recipe, dream_test and its grid, liquify |
| `code/order_preview.py` | **fast loop-order iteration**: VAE-only morph proxy (~1 min/candidate) |
| `code/harmonize.py` | **palette/warmth/contrast harmonizer**: unifies the veritas frames + self-portraits |
| `source/harmonized/` | full-res harmonized versions of the whole set (local only) |
| `source/IMG_6975.jpeg`, `source/…wash_your_hands…png` | the **self-portraits**, real + mirror (local only) |
| `_archive/` | old renders (v1 to v4.4), frame dumps, logs, superseded checkpoints (local only) |

---

## Reproducing it

```bash
pip install --user torch diffusers transformers accelerate safetensors \
                   peft spandrel coremltools imageio imageio-ffmpeg scipy pillow opencv-python
python3 code/morph_v44.py --fresh   # dream anchors + render (omit --fresh to reuse cache)
python3 code/morph_v45_sr.py        # the final render: cached anchors, Real-ESRGAN 4×, 2560×1920
caffeinate -i python3 code/spring.py   # the spring, dreaming without end; veritas at http://127.0.0.1:8770/
```

The loop needs the eight source frames in `source/veritas/`; the spring leans
toward `source/moodboard/` and falls back to them. `--public` needs
`cloudflared` on the path or in `~/.local/bin/`. The
final render needs the cached anchors and the Real-ESRGAN weights in
`code/models/`. None of these are in the public repo.

Tunable knobs at the top of `morph_v44.py`: `D` (anchor density / uniqueness),
`M` (frames per gap → loop length & slowness), `LOW_STR`/`HIGH_STR`
(discernible↔gooey), `SUBSET` (render a 2-frame test instead of all 8), the
prompt, and the grade constants: `GLOSS_W`, `BLACK_GAMMA`, and the palette lock
(`COOL`, `GOLD_TONE`, `WARM_SCALE`), `GRAIN`, `VIG_STR`.

## License

Code in this repository (`code/`, build scripts and page source) is MIT licensed; see [`LICENSE`](LICENSE). The artwork, source images, video and writing are © 2026 Katherine Titterton, all rights reserved. Model weights belong to their authors under their own licenses.
