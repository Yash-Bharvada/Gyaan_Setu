# PROMPT FOR ANTIGRAVITY: "Gyaan Setu" scroll-driven animation

Paste everything below this line into Antigravity, with this whole folder (layers/, manifest.json, reference images) attached to the workspace.

---

## Goal
Build a stunning, buttery-smooth **scroll-driven animation** (no video) from the layered illustration in `layers/`. The page shows a red textured book-cover stage with a gold border and a cream circle. As the user scrolls, characters and props fly in from both sides, settle into the composition, and finally the title word **"Scroll"** is replaced by **"Gyaan Setu"**. The finished still composition must match `reference_final_composite.jpg` / `preview_assembled_final_pose.jpg`.

## Tech
- Next.js (App Router) + TypeScript + Tailwind, **GSAP + ScrollTrigger** (pinned stage, `scrub`), optional **Lenis** for smooth scroll. No `<video>`, no canvas frame sequences: animate the PNG layers directly with GPU transforms (`x`, `y`, `rotation`, `scale`, `opacity` only).
- Create a single reusable component `GyaanSetuScrollHero` and use it as the home page.

## Stage (very important)
- Design canvas is **2752 x 1536 px** (16:9). Build a stage div with `aspect-ratio: 2752/1536` that is scaled to fit the viewport (letterbox with the same red colour, `object-fit: contain` behaviour). On portrait/mobile keep the same 16:9 stage scaled to fit width and centred vertically; do not re-layout.
- Position every layer **absolutely using percentages of the stage** from `manifest.json` (`left_pct`, `top_pct`, `width_pct`; height auto). This keeps everything pixel-aligned at any size.
- Z-order, bottom to top: `background_empty` > `brush_stand` > `girl_chair` > `dog` > `parchment` > `ink_on_parchment` > `floating_ink` > title layers.
- Layer coordinates (px on the 2752x1536 canvas):

| z | file | x | y | w | h | left | top | width |
|---|------|---|---|---|---|------|-----|-------|
| 1 | `layers/background_empty.png` | 0 | 0 | 2752 | 1536 | 0% | 0% | 100% |
| 2 | `layers/brush_stand.png` | 1745 | 630 | 199 | 351 | 63.41% | 41.02% | 7.23% |
| 3 | `layers/girl_chair.png` | 1062 | 457 | 827 | 773 | 38.59% | 29.75% | 30.05% |
| 4 | `layers/dog.png` | 579 | 758 | 567 | 284 | 21.04% | 49.35% | 20.60% |
| 5 | `layers/parchment.png` | 915 | 923 | 1670 | 613 | 33.25% | 60.09% | 60.68% |
| 6 | `layers/ink_on_parchment.png` | 1234 | 1046 | 1110 | 438 | 44.84% | 68.10% | 40.33% |
| 7 | `layers/floating_ink.png` | 1782 | 819 | 640 | 672 | 64.75% | 53.32% | 23.26% |
| 8 | `layers/title_gyaan_setu.png` | 585 | 92 | 1604 | 365 | 21.26% | 5.99% | 58.28% |

## NEVER MOVE (static)
`background_empty.png` contains the red textured paper, gold Chinese border + corner ornaments and the large cream circle with the gold Greek-key ring. It must stay **perfectly still** (no parallax, no scale, no fade) for the entire animation. Characters may overflow the circle (the dog's ears and the parchment do in the original cover); do NOT clip them to the circle.

## Entrance directions
**From the LEFT:** `girl_chair` (girl + chair + brush in hand) and `dog` (dog slightly ahead of the girl).
**From the RIGHT:** `parchment` + `ink_on_parchment` (these two move together as one rigid group, ink inside the parchment), `brush_stand` (the hanging brushes) and `floating_ink` (bird, spiral, smoke, glyphs).
Note: `floating_ink` contains a few marks that rest on the parchment, so during the entrance it must travel at the same x-speed as the parchment (so those marks stay on it), then it may start a tiny independent float after settling.
Layers start fully off-screen (beyond the stage edge, using `xPercent`/`x` based on stage width) and finish at their exact manifest position (x = 0, y = 0 offset).

## Scroll timeline (one pinned ScrollTrigger, ~600vh of scroll, `scrub: 1`, `anticipatePin: 1`)
Use a GSAP timeline of **8 time units** mapped to the full scroll length:

| time | what happens |
|------|--------------|
| 0.0 - 0.5 | Only the static background plus the title **"Scroll"** (centre-top, see below) are visible. Hold. A subtle "scroll to begin" hint at the bottom that fades out as the user scrolls. |
| 0.5 - 4.0 | **Entrances.** Left group (dog first, girl_chair 0.15 later) slides in from the left with `power3.out` and a very slight 1-2 degree rotation settling to 0. Right group (parchment+ink first, then brush_stand and floating_ink 0.2 later) glides in from the right with `power3.out`. All simultaneous, no bounce. The parchment should feel like it unrolls into place (slight scaleX from 0.92 to 1 with transform-origin at its right edge). |
| 4.0 - 5.5 | Everything settled. Add gentle scroll-linked idle motion: the floating ink symbols drift +/-10px and rotate +/-2 degrees, the girl's braids/upper body sway ~0.5 degree (transform-origin near her chair), the dog bobs 4px, the brush stand swings +/-1.5 degree from its top hook. Keep it subtle and smooth. |
| 5.5 - 6.5 | The "Scroll" title lifts up and exits through the top edge (`power2.in`). |
| 6.5 - 8.0 | `title_gyaan_setu.png` drops in from above the top edge and lands exactly at its manifest position (centre-top, same place the "Scroll" word was) with a soft `power3.out` settle and a tiny overshoot of at most 8px. Add an optional quick ink-splash feel: opacity/scale from 1.04 to 1 and a faint black radial blur that fades. It then holds still to the end. |

After the timeline ends keep the pin for an extra ~40vh so the final composition rests on screen before the next section scrolls in.

## The "Scroll" title (no image provided)
Render the word **Scroll** as live text in black, centred horizontally on the canvas, vertically centred on the same box where the Gyaan Setu image sits (use `title_gyaan_setu` manifest box: centre around x=1387px, y=275px, similar cap-height ~ 300px on the 2752 canvas). Use a thick hand-painted brush font from Google Fonts (e.g. **Kaushan Script**, fallback "Yuji Boku" / "Permanent Marker") and add a subtle rough-edge SVG filter (feTurbulence + feDisplacementMap) so it feels like dry brush. Match visual weight and size to the Gyaan Setu image.

## Polish checklist
- Preload all PNGs, `decoding="async"`, convert to WebP/AVIF at build time if you can (keep the transparent PNGs as source), show a minimal loader until images are decoded.
- `will-change: transform` only on animated layers; avoid layout-affecting properties; no filters on big layers during scroll (filters only on the title).
- Respect `prefers-reduced-motion`: show the final composed state with a simple fade, no scroll scrubbing.
- Add a soft drop shadow (`drop-shadow(0 12px 18px rgba(60,10,10,.25))`) on dog, girl_chair and parchment to lift them from the background, applied via a static wrapper, not animated.
- Add an optional debug overlay (press `D`) that shows timeline progress 0-8 so I can tune timings.
- Keep a clean file structure: `components/GyaanSetuScrollHero.tsx`, `lib/timeline.ts`, `public/layers/*`, and expose the timings and distances as constants at the top of the file.
- Next section below the pinned hero: leave a placeholder section so I can build on it.

## Known limits of the assets (handle gracefully)
- The girl's chair legs were trimmed; her lower body is meant to sit hidden behind the parchment, so keep `parchment` above `girl_chair`.
- There is no separate desk/inkstone layer; the parchment overlap covers that area. Do not invent new artwork.
- `brush_stand` edges are slightly rough, so do not scale it above 1.0.
- `ink_on_parchment` and `floating_ink` are pure black ink with alpha, extracted at full resolution from the cover, so they stay crisp. Keep them as-is, do not blur or filter them.
- Do not redraw, recolour or restyle any artwork. Only transform it.

## Deliverables
1. A running Next.js project with the animation working at `npm run dev`.
2. Short README with how to tweak timings, distances and the scroll length.
3. A quick self-check: scroll to 0%, 25%, 50%, 75%, 100% and confirm the final frame matches `preview_assembled_final_pose.jpg`.
