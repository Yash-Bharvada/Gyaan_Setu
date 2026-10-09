# PROMPT: Build the Gyaan Setu frontend

Build the frontend for the attached FastAPI backend (API prefix `/api/v1`, CORS allows `http://localhost:3000`, so run the app on port 3000). Stack: Next.js (App Router) + TypeScript + Tailwind, TanStack Query for data. Keep an `api.ts` client with `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`. Only `/health`, `/admin/*` and `/jobs/{id}` are live today, so build every other screen against typed mock data behind the same client and swap to real routes as modules ship.

## Name and text
- The product is called **Gyaan Setu** everywhere (logo, page titles, metadata, footer, emails). Never write "StudyCompanion".
- Reuse the exact copy from `reference_home_sample` (nav: Library, Tutor, Practice, Revise, Progress; buttons: Start learning, Upload study material, Ask the tutor; headline: "Learn from your own books, slides and lectures."). Language toggle shows `EN | हिं`. Full Hindi translation via i18n.

## Theme: match the cover art exactly
- Page background: red Chinese-paper texture `#D4211C` (use `red_texture.jpg`, tiled, ~560px).
- Gold `#E2A63A`: 3px inner frame inset 18px from the viewport, gold corner ornaments (`corner_gold.png`, mirrored in all 4 corners, 230px), Greek-key dividers.
- Cream `#F7EDCF` surfaces with a double gold outline (3px gold border + 6px cream ring + 3px gold ring). Ink black `#1A1210`. White `#FFFFFF` only for inner chat/cards.
- Radii: pills 999px, cards 20-32px. Primary button: black pill, cream text. Secondary: transparent, 3px gold border, cream text. Citation chips: red pill, white text.
- Hero uses the cover artwork (girl, dog, scroll, brush stand inside the cream circle). Reuse the scroll-animation layers if available.

## Fonts
- Display / logo / section headings: **Kaushan Script** (brush script, fallback "Yuji Boku", cursive), the same hand-painted look as the cover title.
- Body / UI / buttons: **Mukta** 400/600/700 (supports Hindi/Devanagari; fallback "Noto Sans Devanagari").
- Body text at least 17px; no other fonts.

## Screens (one route each)
1. **Home**: nav pill, cover hero, CTAs, feature cards.
2. **Library**: drag-and-drop upload for PDF, PPTX, images and video; ingestion job progress from `/jobs/{id}`; source list with pages, slides and timestamps.
3. **Tutor**: chat with cited answers (chips like "Page 42", "Slide 7", "12:40" open the source), refusal state when the question is not in the material, mic button for voice, language switch.
4. **Practice**: adaptive quiz cards, answer feedback, rubric grading.
5. **Revise**: flashcards (flip), spaced-repetition schedule, slide summary and audio brief player.
6. **Progress**: topic knowledge map (prerequisite graph), per-topic mastery and forgetting curve.

## Quality
- Fully responsive (nav collapses to a menu on mobile), keyboard accessible, text contrast at least 4.5:1, touch targets at least 44px, real buttons/links/labels.
- Subtle motion only (fade/slide, 200-300ms), honor `prefers-reduced-motion`.
- No emoji; icons are inline gold/black stroke SVG.
- Deliver a running project, a README and a `tokens.css` holding the colors, radii and fonts above.
