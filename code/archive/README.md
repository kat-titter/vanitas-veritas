# code/archive

Earlier experiments, kept as they were for the record. They are not maintained and are not meant to run from here (their paths
assume `code/`). What runs today is one level up: `sink.py` (the live water), `morph_v44.py` and `morph_v45_sr.py` (the loop's
render), `order_preview.py` (loop-order previews), with `latent.py`, `upscale.py` and `harmonize.py` shared between them.

| file | what it was | replaced by |
|---|---|---|
| `morph_loop.py` | the earliest per-frame engine | `morph_v44.py` |
| `morph_v3.py` | the v4 engine with an earlier grade | `morph_v44.py` |
| `preview_recipe.py` | one transition with an early recipe, for fast iteration | `order_preview.py` |
| `dream_test.py` | the 3 x 3 style grid search | its result, `dream_styles_grid.png` |
| `dream_styles_grid.png` | the grid search's result image | |
| `liquify.py` | the rejected displacement experiment | |
