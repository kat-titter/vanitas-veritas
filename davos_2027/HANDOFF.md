# veri+as ii — handoff prompt

Paste everything below the line into a new chat.

---

I'm Kat (macrofluidic, @KatTitterton), SF neuroscience/AI scientist and generative artist. I'm making an interactive web artwork called **veri+as** with my friend Olive Allen (NYC new-media/NFT artist) as a seed for a Davos 2027 piece (WEF, 18–22 Jan 2027). It grew out of my tiat sink installation: a screen where the drain should be.

**Repo:** `/Users/kat_titter/Claude/Projects/tiat_slop_2026` (GitHub `kat-titter/vanitas-veritas`, Pages at kat-titter.github.io/vanitas-veritas/). Everything lives in `davos_2027/`.

- `veritas2.src.html` → `veritas2.html` is the live piece (version ii). Edit the `.src`, then run `python3 davos_2027/build.py davos_2027/veritas2.src.html davos_2027/veritas2.html` (inlines 24 stills from `video/veritas_loop_v45_4k.mp4` as data URIs, ~2 MB). Then commit the built file too; it's committed on purpose so the link works.
- `veritas.src.html` → `veritas.html` is version i, kept as is.
- `proposal.html` is the public proposal (outline, references, tech spec, Davos art history, questions for Olive). Its section 00 outline still shows my older draft lines; it should be updated to the eight lines in `OUTLINE` in veritas2.src.html.
- `HANDOFF.md` is this file. Memory notes are in `~/.claude/projects/-Users-kat-titter/memory/project_davos_2027_olive.md`.
- Preview: `~/.claude/launch.json` has a server named `vanitas-veritas` (python http.server on port 4188). Open `http://localhost:4188/davos_2027/veritas2.html`. Add `?probe` to expose `window.__veritas` (ms, tick(clock), pause, read, loss, end, held, holdAmt, whole, dyeAt(x,y)) for driving tests with a synthetic clock. Keep synthetic runs ≤ ~1500 ticks. `?day=N` previews the loss clock.

**What the piece is** (single-file WebGL2, no libraries): a basin of fluid (stable-fluids solver) carrying my video stills from a tap to a drain. Fluted glass covers it; holding the pointer still flattens the glass, and finding the hidden clear spot keeps a composed still (two stills merged, never the same twice) for one heartbeat and reads one line. Around the basin a living lace (Gray-Scott reaction-diffusion in polar coordinates) creeps, breathes on a six-beat waltz, and can be wiped by the hand. What drains comes back as copies of copies (loss). One clock runs from launch 2026-09-29 to Davos 2027-01-18: less pour, more fade, dimmer returns, thicker lace. After all eight lines are read, the piece ends over 25 s: the lace blooms over the basin and the pupil follows the hand like a spotlight. The drain is an eye; once the piece is ready it looks toward the hand, and hovering shows "look back · one frame, never sent". Clicking takes one camera frame (never stored or sent), holds a clear composite of viewer + still for three breaths, then pours it into the loop. Live code poem: `sink = drain(sink) / n -> ∞ / sink == sync // 0.xx|True`, and draggable `culture(f, k)` knobs feed the lace. Eight finds make a sign and a `?p=` share link. Progress persists in localStorage `veritas.ii`.

**My words in the piece (keep verbatim):** we need a new biology. / merge. / resistance is futile. / it's all ok. / it shall be ok. / beautiful even. great even. / you can't hide. / the spotlight.

**Hard rules:** no audio, ever (assume silence). 3–4 colours (ink, bone, gold, ice), colour-blind legible, high contrast. Minimal text; show, don't tell. No straight rays. Text must never overlap plot elements. Repo stays lightweight HTML; no new binaries. Pushing to the public repo is fine. Plain tone in replies, no sass or self-praise. The words should be mine; offer drafts, don't ship your own as mine.

**Taste:** 2000s retro-future, hieroglyphic, shamanistic, foggy, textured, intense; mushy-merge with soft edges; slow, smooth, dance-like, harmonious; beacon / iris / marble / bloom / robot / metallic all at once. References: Signalis, Tunic, Kentucky Route Zero, Voyager Golden Record, my code-poem tweets.

**Where I left off (commit c3b6387):** the eye-as-ask was just built and pushed. Open items: update proposal.html 00 outline to my eight lines; decide the credit line (`// macrofluidic × …`); test on phone and touch; look at the real camera grade; judge motion feel (my collaborator before could only see stills). Ideas offered but not built: pupil follows for a full minute before asking; the meeting composed on the clear window you must find; a second ask after all eight lines where the frame becomes the sign; shared basin store / two-basin live link; og:image; quality step-down for slow GPUs.

Start by opening the local preview and reading veritas2.src.html before changing anything.
