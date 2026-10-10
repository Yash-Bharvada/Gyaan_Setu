# Gyaan Setu — Frontend

> **"Learn from your own books, slides and lectures."**  
> Personalized Tutoring & Adaptive Learning companion with verifiable source citations, prerequisite knowledge graphs, and Bayesian knowledge decay tracking.

---

## 🎨 Theme & Art Direction

The UI matches the cover art:
- **Page Background**: Red Chinese-paper texture `#D4211C` (`/red_texture.jpg`, tiled ~560px).
- **Gold Accents** (`#E2A63A`): 3px inner frame inset 18px from the viewport, authentic gold corner ornaments (`corner_gold.png` mirrored in all 4 corners, 230px), and Greek-key meander dividers.
- **Surfaces**: Cream `#F7EDCF` with the signature **double gold outline** (3px gold border + 6px cream ring + 3px gold ring). Ink black `#1A1210` for high-contrast text. Pure white `#FFFFFF` for inner interactive cards/chat bubbles.
- **Buttons**:
  - **Primary**: Black pill (`#1A1210`), cream text (`#F7EDCF`), smooth hover translation.
  - **Secondary**: Transparent, 3px gold border (`#E2A63A`), cream text.
  - **Citation Chips**: Red pill (`#D4211C`), white text, opening the verifiable source excerpt inspector.
- **Fonts**:
  - **Display / Headings**: *Kaushan Script* (brush script, hand-painted aesthetic).
  - **Body / UI**: *Mukta* (400, 600, 700) with complete bilingual Devanagari (Hindi) glyph support.

All design tokens are formalized in [`tokens.css`](file:///d:/Gyaan_Setu/frontend/tokens.css).

---

## 🗺️ Routes & Screen Architecture

Every screen is fully functional with live backend connectivity and realistic typed mock engines:

1. **Home (`/`)**:
   - Hero displaying the cover art (scholar girl, companion dog, scroll, and brush stand).
   - Core headline: *"Learn from your own books, slides and lectures."*
   - Direct CTA buttons: *"Start learning"*, *"Upload study material"*, *"Ask the tutor"*.
   - Feature showcase cards for all 5 learning pillars.
   - Rigor comparison callout: Generic AI vs. Gyaan Setu Verified RAG.

2. **Library (`/library`)**:
   - Drag-and-drop file ingestion zone (PDF textbooks, PPTX slides, MP4 videos, images).
   - Live job progress tracking (`/jobs/{id}`) with stage-by-stage status updates.
   - Filterable indexed course materials list with page numbers, slide counts, and timestamp badges.
   - Clickable citation chips to inspect extracted source units.
   - Quota ledger widget tracking FreeOCR and Sarvam AI usage.

3. **Tutor (`/tutor`)**:
   - Source-grounded AI chat interface.
   - Clickable citation chips (`Page 42`, `Slide 7`, `12:40`) that open the modal excerpt viewer.
   - Authentic **Refusal Gate**: Out-of-scope inquiries are strictly refused to prevent hallucinations.
   - Voice interaction button with animated audio recording indicator.
   - Quick inquiry presets for immediate testing.

4. **Practice (`/practice`)**:
   - Adaptive assessment cards organized by Bloom's Taxonomy levels (Remember, Understand, Apply, Analyze, Evaluate).
   - MCQ cards with immediate option verification and distractor rationales.
   - Short-answer questions with multi-criterion rubric evaluation and source citations.
   - Score tracking and diagnostic summary.

5. **Revise (`/revise`)**:
   - Interactive 3D flip flashcards with SM-2 / FSRS spaced repetition ratings (*Again*, *Hard*, *Good*, *Easy*).
   - 5-Minute Pre-Exam Audio Brief player with audio controls, animated waveform visualizer, 1x/1.5x speed toggle, and live synced transcript.

6. **Progress (`/progress`)**:
   - Interactive SVG Prerequisite Knowledge Graph (Directed Acyclic Graph - DAG) with color-coded mastery nodes (Mastered, In Progress, Needs Attention).
   - Clickable nodes to inspect prerequisite chains, stability in days, and question attempts.
   - Bayesian Knowledge Tracing (BKT) overall mastery gauge.
   - Ebbinghaus Forgetting Curve retention decay visualization with spaced review spikes.

---

## 🌐 Language & Internationalization

Gyaan Setu includes full bilingual English / Hindi support:
- Language toggle (`EN | हिं`) in the sticky navigation header.
- Persistent language selection in `localStorage`.
- Comprehensive i18n dictionary in [`src/lib/i18n.tsx`](file:///d:/Gyaan_Setu/frontend/src/lib/i18n.tsx).

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. Production Build
```bash
npm run build
npm run start
```
