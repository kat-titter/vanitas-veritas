# vanitas_veritas

we need a new biology. A sink you can't wash your hands in: AI-made vanitas
pictures drain and come back as copies of copies. Hold still, and it clears.
Hold together, and it is true. One work in two places: the basin game, live on
the web, and a real sink (proposed) that runs the same page where the drain
should be.

- [the piece](https://kat-titter.github.io/vanitas_veritas_verse/)
- [the macroverse](https://kat-titter.github.io/vanitas_veritas_verse/macroverse.html)
- [the black paper](https://kat-titter.github.io/vanitas_veritas_verse/blackpaper.html)
- [the sink](https://kat-titter.github.io/vanitas_veritas_verse/sink.html) (proposed)

Kat Titterton (macrofluidic)

---

## Thesis

we need a new biology: new forms of life, the uncanny in-between (life and
death, species), emergence, softness.

you can't wash your hands of it: nothing drains away, and everyone stands at
the same sink.

sink == sync: when enough people hold still at once, the title turns from
vanitas to veritas.

## veri+as iii

One web page, no framework, no server of its own. Hold still and the glass
clears. Seven hidden stars each grow a named new form of life from two
pictures, and how you play pushes the culture on the rim. The program is a
primer, then a poem, in Python. At the end your youniverse is read back to
you, kept on your device and sendable as a link that carries no picture. The
camera is optional: one frame, which never leaves the device.

The macroverse is everyone's youniverses on one live map.

**The study.** Each play on the published page leaves one anonymous record on
public Nostr relays (NIP-78), with no picture and no face. `?nostudy` or Global
Privacy Control keeps a play out. `node davos_2027/study/plays.mjs` reads the
records. Details are in
[the black paper](https://kat-titter.github.io/vanitas_veritas_verse/blackpaper.html#keeps).

**Versions.** i and ii (`veritas.html`, `veritas2.html`) are kept as they were.
iii is live. `proposal.html` is archived in favour of the black paper.

**The sink (proposed).** The same page in a real basin: a monolith of stone
with the basin as its screen, under fluted glass. Holding the faucet lever is
the hold; it never runs water. Through the relays, a hold at either place would
be felt at both. A first sink is proposed for San Francisco, then wherever an
open call takes it; nothing is built or confirmed. The design is in
[the sink](https://kat-titter.github.io/vanitas_veritas_verse/sink.html). The 2026 sink for
tiat's open call (`documents/`) is kept as an archive.

---

## The loop (2026)

Where the work began. Its 32 dreamed anchors are the 32 pictures veri+as iii
grows its forms of life from.

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
├── davos_2027/                    veri+as iii (live), i and ii, the black paper, the pitch,
│                                  the macroverse, the sink doc, the study reader
├── documents/                     the 2026 tiat submission bundle, kept as an archive (Submission, Build Guide, Web; self-contained HTML + assets)
├── code/                          the loop's pipeline
├── video/                         the final render + basin loop
├── research/                      vanitas paper, references, ref images
├── source/                        source artwork (veritas frames + harmonized + self-portraits)
├── _order_tests/                  fast loop-order preview clips
└── _archive/                      superseded versions, frames, logs (kept, not deleted)
```

`video/`, `source/`, `research/`, `_order_tests/`, `_archive/`, `code/models/`
and the cached anchors stay local. They are not in the public repo.

### Key files

| Path | Role |
|---|---|
| `davos_2027/veritas3.html` | **veri+as iii**, the live piece |
| `davos_2027/veritas3.src.html` | its source; `davos_2027/build.py` inlines the loop's 32 anchors to make `veritas3.html` |
| `davos_2027/blackpaper.html` | the black paper |
| `davos_2027/pitch.html` | the pitch kit |
| `davos_2027/sink.html` | the sink, redesigned (proposed) |
| `davos_2027/macroverse.html` | the macroverse |
| `davos_2027/study/plays.mjs` | reads the study records |
| `davos_2027/veritas.html`, `veritas2.html` | i and ii, kept as they were |
| `davos_2027/proposal.html` | the first proposal (archived) |
| `index.html` | the loop's landing page |
| `documents/Vanitas Veritas - Submission.dc.html` | the 2026 tiat submission (archive; self-contained HTML) |
| `documents/Vanitas Veritas - Build Guide.dc.html` | the 2026 electronics guide (archive; the sink is now `davos_2027/sink.html`) |
| `documents/Vanitas Veritas - Web.dc.html` | the 2026 web doc (archive) |
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
| `code/models/RealESRGAN_x4plus.pth` | super-res weights, open-source (local only) |
| `code/morph_v3.py` | the v4 engine (earlier grade, superseded by v44) |
| `code/morph_loop.py` | the earliest per-frame engine (superseded; kept for history) |
| `code/preview_recipe.py` | one transition with an early recipe, for fast iteration (kept for history) |
| `code/order_preview.py` | **fast loop-order iteration**: VAE-only morph proxy (~1 min/candidate) |
| `code/harmonize.py` | **palette/warmth/contrast harmonizer**: unifies the veritas frames + self-portraits |
| `source/harmonized/` | full-res harmonized versions of the whole set (local only) |
| `source/IMG_6975.jpeg`, `source/…wash_your_hands…png` | the **self-portraits**, real + mirror (local only) |
| `code/dream_test.py` | the 3×3 style grid-search harness |
| `code/liquify.py` | the rejected displacement experiment (kept for history) |
| `code/dream_styles_grid.png` | the grid-search result image |
| `_archive/` | old renders (v1 to v4.4), frame dumps, logs, superseded checkpoints (local only) |

---

## Reproducing it

```bash
pip install --user torch diffusers transformers accelerate safetensors \
                   peft spandrel imageio imageio-ffmpeg scipy pillow
python3 code/morph_v44.py --fresh   # dream anchors + render (omit --fresh to reuse cache)
python3 code/morph_v45_sr.py        # the final render: cached anchors, Real-ESRGAN 4×, 2560×1920
python3 davos_2027/build.py davos_2027/veritas3.src.html davos_2027/veritas3.html   # veri+as iii
```

The loop needs the eight source frames in `source/veritas/`. The final render
needs the cached anchors and the Real-ESRGAN weights in `code/models/`. The
build takes the 32 anchors from the final render. None of these are in the
public repo.

Tunable knobs at the top of `morph_v44.py`: `D` (anchor density / uniqueness),
`M` (frames per gap → loop length & slowness), `LOW_STR`/`HIGH_STR`
(discernible↔gooey), `SUBSET` (render a 2-frame test instead of all 8), the
prompt, and the grade constants: `GLOSS_W`, `BLACK_GAMMA`, and the palette lock
(`COOL`, `GOLD_TONE`, `WARM_SCALE`), `GRAIN`, `VIG_STR`.

## License

Code in this repository (`code/`, build scripts and page source) is MIT licensed; see [`LICENSE`](LICENSE). The artwork, source images, video and writing are © 2026 Katherine Titterton, all rights reserved. Model weights belong to their authors under their own licenses.
