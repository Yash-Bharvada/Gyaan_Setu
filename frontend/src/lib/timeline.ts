import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

// Ensure ScrollTrigger is registered
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

/* =========================================================================
   CANVAS & STAGE CONSTANTS
   ========================================================================= */
export const CANVAS_WIDTH = 2752;
export const CANVAS_HEIGHT = 1536;
export const CANVAS_ASPECT_RATIO = CANVAS_WIDTH / CANVAS_HEIGHT; // 1.7916667 (16:9)

/* =========================================================================
   TIMELINE TIMINGS (0.0 to 8.0 units)
   ========================================================================= */
export const TIMELINE_TOTAL_DURATION = 8.0;

// Phase 1: Pristine background stage + subtle scroll hint (0.0 - 0.5)
export const T_START = 0.0;
export const T_HINT_FADE_END = 0.5;

// Phase 2: Entrances (0.5 - 4.0)
export const T_ENTRANCE_START = 0.5;
export const T_DOG_START = 0.5;
export const T_DOG_END = 3.85;
export const T_GIRL_START = 0.65; // dog 0.15 ahead
export const T_GIRL_END = 4.0;
export const T_PARCHMENT_START = 0.5; // moves together with ink and floating ink
export const T_PARCHMENT_END = 3.9;
export const T_BRUSH_STAND_START = 0.7; // 0.2 later than parchment
export const T_BRUSH_STAND_END = 4.0;
export const T_ENTRANCES_SETTLE = 4.0;

// Phase 3: Settled & Gentle Idle Motion (4.0 - 5.5)
export const T_IDLE_START = 4.0;
export const T_IDLE_MID = 4.75;
export const T_IDLE_END = 5.5;

// Phase 4: "Gyaan Setu" Title Drop-In & Ink Splash (5.5 - 7.5)
export const T_GYAAN_DROP_START = 5.5;
export const T_GYAAN_DROP_END = 7.5;

/* =========================================================================
   SCROLL LENGTH CONFIGURATION
   ========================================================================= */
export const SCROLL_DISTANCE_VH = 600; // ~600vh of active scroll scrub
export const REST_HOLD_VH = 40;        // ~40vh resting hold on final pose
export const TOTAL_SCROLL_PIN_VH = SCROLL_DISTANCE_VH + REST_HOLD_VH; // 640vh total

/* =========================================================================
   MOTION PARAMETERS & OFFSETS (Exposed for easy tuning)
   ========================================================================= */
// Entrance Offsets (as ratio of current stage width - safely outside viewport)
export const DISTANCE_OFFSCREEN_LEFT_DOG = -1.1;     // dog travels from far left
export const DISTANCE_OFFSCREEN_LEFT_GIRL = -1.25;   // girl & chair completely offscreen
export const DISTANCE_OFFSCREEN_RIGHT_GROUP = 1.25;  // parchment, ink, floating ink
export const DISTANCE_OFFSCREEN_RIGHT_BRUSH = 1.1;   // brush stand

// Rotations and Scales during entrance
export const ENTRANCE_DOG_ROTATION = -1.8;           // slight tilt settling to 0
export const ENTRANCE_GIRL_ROTATION = 1.2;           // slight tilt settling to 0
export const ENTRANCE_BRUSH_ROTATION = 1.5;          // swing settling to 0
export const PARCHMENT_UNROLL_START_SCALE_X = 0.92;  // unrolling effect

// Idle breathing motion (at 4.0 - 5.5)
export const IDLE_INK_DRIFT_PX = 10;                 // +/- 10px
export const IDLE_INK_ROTATION_DEG = 2.0;            // +/- 2 degrees
export const IDLE_GIRL_SWAY_DEG = 0.5;               // sway ~0.5 degree
export const IDLE_DOG_BOB_PX = 4.0;                  // bob 4px
export const IDLE_BRUSH_SWING_DEG = 1.5;             // swing +/-1.5 degree

// Title drop overshoot (<= 8px)
export const TITLE_DROP_OVERSHOOT_PX = 6.0;

/* =========================================================================
   LAYER METADATA (Exact percentages from manifest.json)
   ========================================================================= */
export interface LayerManifestItem {
  id: string;
  name: string;
  filename: string;
  src: string;
  alt: string;
  zIndex: number;
  left_pct: number;
  top_pct: number;
  width_pct: number;
  height_pct: number;
  x: number;
  y: number;
  w: number;
  h: number;
  hasDropShadow?: boolean;
}

export const LAYERS: LayerManifestItem[] = [
  {
    id: "background_empty",
    name: "Background",
    filename: "background_empty.png",
    src: "/layers/background_empty.png",
    alt: "Gyaan Setu background with gold border and cream circle",
    zIndex: 1,
    left_pct: 0,
    top_pct: 0,
    width_pct: 100,
    height_pct: 100,
    x: 0,
    y: 0,
    w: 2752,
    h: 1536,
  },
  {
    id: "brush_stand",
    name: "Brush Stand",
    filename: "brush_stand.png",
    src: "/layers/brush_stand.png",
    alt: "Hanging calligraphy brush stand",
    zIndex: 2,
    left_pct: 63.408,
    top_pct: 41.016,
    width_pct: 7.231,
    height_pct: 22.852,
    x: 1745,
    y: 630,
    w: 199,
    h: 351,
  },
  {
    id: "girl_chair",
    name: "Scholar Girl on Chair",
    filename: "girl_chair.png",
    src: "/layers/girl_chair.png",
    alt: "Young scholar girl seated on wooden chair with brush",
    zIndex: 3,
    left_pct: 38.59,
    top_pct: 29.753,
    width_pct: 30.051,
    height_pct: 50.326,
    x: 1062,
    y: 457,
    w: 827,
    h: 773,
    hasDropShadow: true,
  },
  {
    id: "dog",
    name: "Companion Dog",
    filename: "dog.png",
    src: "/layers/dog.png",
    alt: "Little companion dog with red scarf bandana",
    zIndex: 4,
    left_pct: 21.039,
    top_pct: 49.349,
    width_pct: 20.603,
    height_pct: 18.49,
    x: 579,
    y: 758,
    w: 567,
    h: 284,
    hasDropShadow: true,
  },
  {
    id: "inkstone",
    name: "Carved Scholar Inkstone",
    filename: "inkstone.png",
    src: "/layers/inkstone.png",
    alt: "Carved stone calligraphy inkstone slab with dark ink well",
    zIndex: 5,
    left_pct: 32.958,
    top_pct: 70.117,
    width_pct: 4.397,
    height_pct: 7.357,
    x: 907,
    y: 1077,
    w: 121,
    h: 113,
    hasDropShadow: true,
  },
  {
    id: "parchment",
    name: "Scroll Parchment",
    filename: "parchment.png",
    src: "/layers/parchment.png",
    alt: "Ancient rolled scroll parchment with orange ends",
    zIndex: 6,
    left_pct: 33.249,
    top_pct: 60.091,
    width_pct: 60.683,
    height_pct: 39.909,
    x: 915,
    y: 923,
    w: 1670,
    h: 613,
    hasDropShadow: true,
  },
  {
    id: "ink_on_parchment",
    name: "Ink on Parchment",
    filename: "ink_on_parchment.png",
    src: "/layers/ink_on_parchment.png",
    alt: "Crisp black calligraphy ink inscription on scroll",
    zIndex: 7,
    left_pct: 44.84,
    top_pct: 68.099,
    width_pct: 40.334,
    height_pct: 28.516,
    x: 1234,
    y: 1046,
    w: 1110,
    h: 438,
  },
  {
    id: "floating_ink",
    name: "Floating Ink & Glyphs",
    filename: "floating_ink.png",
    src: "/layers/floating_ink.png",
    alt: "Magical floating ink bird, swirls, smoke and glyphs",
    zIndex: 8,
    left_pct: 64.753,
    top_pct: 53.32,
    width_pct: 23.256,
    height_pct: 43.75,
    x: 1782,
    y: 819,
    w: 640,
    h: 672,
  },
  {
    id: "title_gyaan_setu",
    name: "Gyaan Setu Title",
    filename: "title_gyaan_setu.png",
    src: "/layers/title_gyaan_setu.png",
    alt: "Grand brush calligraphy title: Gyaan Setu",
    zIndex: 9,
    left_pct: 21.257,
    top_pct: 5.99,
    width_pct: 58.285,
    height_pct: 23.763,
    x: 585,
    y: 92,
    w: 1604,
    h: 365,
  },
];

/* =========================================================================
   ELEMENTS INTERFACE FOR TIMELINE
   ========================================================================= */
export interface HeroTimelineElements {
  stage: HTMLElement;
  triggerContainer: HTMLElement;
  scrollHint: HTMLElement | null;
  scrollTitle?: HTMLElement | null;
  gyaanTitle: HTMLElement | null;
  gyaanTitleSplash: HTMLElement | null;
  dog: HTMLElement | null;
  girlChair: HTMLElement | null;
  inkstone?: HTMLElement | null;
  parchment: HTMLElement | null;
  inkOnParchment: HTMLElement | null;
  brushStand: HTMLElement | null;
  floatingInk: HTMLElement | null;
}

export interface HeroTimelineOptions {
  onProgress?: (progress: number, time: number) => void;
  reducedMotion?: boolean;
}

/**
 * Builds the GSAP Timeline mapped to ScrollTrigger pinning.
 */
export function buildGyaanSetuTimeline(
  elements: HeroTimelineElements,
  options: HeroTimelineOptions = {}
): gsap.core.Timeline {
  const { stage, triggerContainer } = elements;
  const stageWidth = stage.offsetWidth || CANVAS_WIDTH;
  const stageHeight = stage.offsetHeight || CANVAS_HEIGHT;
  const scaleRatio = stageWidth / CANVAS_WIDTH;

  // Scaled pixel values
  const idleDogBob = IDLE_DOG_BOB_PX * scaleRatio;
  const idleInkDriftX = IDLE_INK_DRIFT_PX * scaleRatio;
  const idleInkDriftY = IDLE_INK_DRIFT_PX * scaleRatio;
  const overshootY = TITLE_DROP_OVERSHOOT_PX * scaleRatio;

  // Master timeline with duration 8.0 units
  const tl = gsap.timeline({
    paused: true,
    defaults: { ease: "none" },
    onUpdate: () => {
      if (options.onProgress) {
        options.onProgress(tl.progress(), tl.time());
      }
    },
  });

  if (options.reducedMotion) {
    // If reduced motion is requested: show final state directly with subtle fade
    if (elements.scrollHint) gsap.set(elements.scrollHint, { opacity: 0 });
    if (elements.scrollTitle) gsap.set(elements.scrollTitle, { opacity: 0 });
    if (elements.gyaanTitle) gsap.set(elements.gyaanTitle, { opacity: 1, y: 0 });
    if (elements.dog) gsap.set(elements.dog, { x: 0, y: 0, rotation: 0 });
    if (elements.girlChair) gsap.set(elements.girlChair, { x: 0, y: 0, rotation: 0 });
    if (elements.inkstone) gsap.set(elements.inkstone, { x: 0, y: 0, rotation: 0 });
    if (elements.parchment) gsap.set(elements.parchment, { x: 0, y: 0, scaleX: 1 });
    if (elements.inkOnParchment) gsap.set(elements.inkOnParchment, { x: 0, y: 0, scaleX: 1 });
    if (elements.brushStand) gsap.set(elements.brushStand, { x: 0, y: 0, rotation: 0 });
    if (elements.floatingInk) gsap.set(elements.floatingInk, { x: 0, y: 0, rotation: 0 });
    return tl;
  }

  // --- INITIAL STATES (Time = 0.0) ---
  const offscreenLeftDog = stageWidth * DISTANCE_OFFSCREEN_LEFT_DOG;
  const offscreenLeftGirl = stageWidth * DISTANCE_OFFSCREEN_LEFT_GIRL;
  const offscreenRightGroup = stageWidth * DISTANCE_OFFSCREEN_RIGHT_GROUP;
  const offscreenRightBrush = stageWidth * DISTANCE_OFFSCREEN_RIGHT_BRUSH;

  if (elements.scrollHint) {
    gsap.set(elements.scrollHint, { opacity: 1 });
  }

  if (elements.scrollTitle) {
    gsap.set(elements.scrollTitle, {
      opacity: 1,
      y: 0,
      scale: 1,
      transformOrigin: "center center",
    });
  }

  if (elements.gyaanTitle) {
    // Title starts hidden above the top canvas edge
    gsap.set(elements.gyaanTitle, {
      opacity: 0,
      y: -stageHeight * 0.45,
      scale: 1.04,
      transformOrigin: "center center",
    });
  }

  if (elements.gyaanTitleSplash) {
    gsap.set(elements.gyaanTitleSplash, {
      opacity: 0,
      scale: 0.8,
    });
  }

  if (elements.dog) {
    gsap.set(elements.dog, {
      x: offscreenLeftDog,
      y: 0,
      rotation: ENTRANCE_DOG_ROTATION,
      transformOrigin: "center bottom",
    });
  }

  if (elements.girlChair) {
    gsap.set(elements.girlChair, {
      x: offscreenLeftGirl,
      y: 0,
      rotation: ENTRANCE_GIRL_ROTATION,
      transformOrigin: "center bottom",
    });
  }

  if (elements.inkstone) {
    gsap.set(elements.inkstone, {
      x: offscreenLeftDog,
      y: 0,
      rotation: 0,
      transformOrigin: "center center",
    });
  }

  if (elements.parchment) {
    gsap.set(elements.parchment, {
      x: offscreenRightGroup,
      y: 0,
      scaleX: PARCHMENT_UNROLL_START_SCALE_X,
      transformOrigin: "right center",
    });
  }

  if (elements.inkOnParchment) {
    gsap.set(elements.inkOnParchment, {
      x: offscreenRightGroup,
      y: 0,
      scaleX: PARCHMENT_UNROLL_START_SCALE_X,
      transformOrigin: "right center",
    });
  }

  if (elements.brushStand) {
    gsap.set(elements.brushStand, {
      x: offscreenRightBrush,
      y: 0,
      rotation: ENTRANCE_BRUSH_ROTATION,
      transformOrigin: "top center",
    });
  }

  if (elements.floatingInk) {
    // Travels with parchment during entrance so resting marks stay aligned
    gsap.set(elements.floatingInk, {
      x: offscreenRightGroup,
      y: 0,
      rotation: 0,
      transformOrigin: "center center",
    });
  }

  /* -----------------------------------------------------------------------
     PHASE 1: 0.0 - 0.5 (Hold cover & fade scroll hint)
     ----------------------------------------------------------------------- */
  if (elements.scrollHint) {
    tl.to(
      elements.scrollHint,
      {
        opacity: 0,
        ease: "power1.out",
        duration: T_HINT_FADE_END,
      },
      0
    );
  }

  /* -----------------------------------------------------------------------
     PHASE 2: 0.5 - 4.0 (Entrances from Left and Right)
     ----------------------------------------------------------------------- */
  // LEFT GROUP: Dog first (0.5 -> 3.85)
  if (elements.dog) {
    tl.to(
      elements.dog,
      {
        x: 0,
        rotation: 0,
        duration: T_DOG_END - T_DOG_START,
        ease: "power3.out",
      },
      T_DOG_START
    );
  }

  // LEFT GROUP: Girl chair (0.65 -> 4.0, dog 0.15 ahead)
  if (elements.girlChair) {
    tl.to(
      elements.girlChair,
      {
        x: 0,
        rotation: 0,
        duration: T_GIRL_END - T_GIRL_START,
        ease: "power3.out",
      },
      T_GIRL_START
    );
  }

  // LEFT GROUP: Inkstone enters with left group (0.65 -> 4.0)
  if (elements.inkstone) {
    tl.to(
      elements.inkstone,
      {
        x: 0,
        y: 0,
        rotation: 0,
        duration: T_GIRL_END - T_GIRL_START,
        ease: "power3.out",
      },
      T_GIRL_START
    );
  }

  // RIGHT GROUP: Parchment + Ink + Floating Ink travel together (0.5 -> 3.9)
  if (elements.parchment) {
    tl.to(
      elements.parchment,
      {
        x: 0,
        scaleX: 1,
        duration: T_PARCHMENT_END - T_PARCHMENT_START,
        ease: "power3.out",
      },
      T_PARCHMENT_START
    );
  }

  if (elements.inkOnParchment) {
    tl.to(
      elements.inkOnParchment,
      {
        x: 0,
        scaleX: 1,
        duration: T_PARCHMENT_END - T_PARCHMENT_START,
        ease: "power3.out",
      },
      T_PARCHMENT_START
    );
  }

  // Floating ink moves at same speed as parchment so marks stay locked on it
  if (elements.floatingInk) {
    tl.to(
      elements.floatingInk,
      {
        x: 0,
        duration: T_PARCHMENT_END - T_PARCHMENT_START,
        ease: "power3.out",
      },
      T_PARCHMENT_START
    );
  }

  // RIGHT GROUP: Brush stand enters 0.2 later (0.7 -> 4.0)
  if (elements.brushStand) {
    tl.to(
      elements.brushStand,
      {
        x: 0,
        rotation: 0,
        duration: T_BRUSH_STAND_END - T_BRUSH_STAND_START,
        ease: "power3.out",
      },
      T_BRUSH_STAND_START
    );
  }

  /* -----------------------------------------------------------------------
     PHASE 3: 4.0 - 5.5 (Settled & Subtle Scroll-Linked Idle Breathing)
     ----------------------------------------------------------------------- */
  // Floating ink: drift +/-10px, rotate +/-2 degrees
  if (elements.floatingInk) {
    tl.to(
      elements.floatingInk,
      {
        x: idleInkDriftX * 0.8,
        y: -idleInkDriftY,
        rotation: IDLE_INK_ROTATION_DEG,
        ease: "sine.inOut",
        duration: T_IDLE_MID - T_IDLE_START,
      },
      T_IDLE_START
    );
    tl.to(
      elements.floatingInk,
      {
        x: -idleInkDriftX * 0.6,
        y: idleInkDriftY * 0.6,
        rotation: -IDLE_INK_ROTATION_DEG * 0.7,
        ease: "sine.inOut",
        duration: T_IDLE_END - T_IDLE_MID,
      },
      T_IDLE_MID
    );
    // Smoothly return to 0 as title transitions
    tl.to(
      elements.floatingInk,
      {
        x: 0,
        y: 0,
        rotation: 0,
        ease: "sine.out",
        duration: 1.0,
      },
      T_IDLE_END
    );
  }

  // Girl sway: ~0.5 degree sway (origin near chair bottom)
  if (elements.girlChair) {
    tl.to(
      elements.girlChair,
      {
        rotation: IDLE_GIRL_SWAY_DEG,
        ease: "sine.inOut",
        duration: T_IDLE_MID - T_IDLE_START,
      },
      T_IDLE_START
    );
    tl.to(
      elements.girlChair,
      {
        rotation: -IDLE_GIRL_SWAY_DEG * 0.6,
        ease: "sine.inOut",
        duration: T_IDLE_END - T_IDLE_MID,
      },
      T_IDLE_MID
    );
    tl.to(
      elements.girlChair,
      {
        rotation: 0,
        ease: "sine.out",
        duration: 1.0,
      },
      T_IDLE_END
    );
  }

  // Dog bob: 4px bob
  if (elements.dog) {
    tl.to(
      elements.dog,
      {
        y: -idleDogBob,
        ease: "sine.inOut",
        duration: (T_IDLE_MID - T_IDLE_START) * 0.5,
      },
      T_IDLE_START
    );
    tl.to(
      elements.dog,
      {
        y: idleDogBob,
        ease: "sine.inOut",
        duration: (T_IDLE_MID - T_IDLE_START) * 0.5,
      },
      T_IDLE_START + (T_IDLE_MID - T_IDLE_START) * 0.5
    );
    tl.to(
      elements.dog,
      {
        y: -idleDogBob * 0.5,
        ease: "sine.inOut",
        duration: (T_IDLE_END - T_IDLE_MID) * 0.5,
      },
      T_IDLE_MID
    );
    tl.to(
      elements.dog,
      {
        y: 0,
        ease: "sine.out",
        duration: 1.0,
      },
      T_IDLE_END
    );
  }

  // Brush stand swing: +/- 1.5 degree from top hook
  if (elements.brushStand) {
    tl.to(
      elements.brushStand,
      {
        rotation: IDLE_BRUSH_SWING_DEG,
        ease: "sine.inOut",
        duration: T_IDLE_MID - T_IDLE_START,
      },
      T_IDLE_START
    );
    tl.to(
      elements.brushStand,
      {
        rotation: -IDLE_BRUSH_SWING_DEG * 0.8,
        ease: "sine.inOut",
        duration: T_IDLE_END - T_IDLE_MID,
      },
      T_IDLE_MID
    );
    tl.to(
      elements.brushStand,
      {
        rotation: 0,
        ease: "sine.out",
        duration: 1.0,
      },
      T_IDLE_END
    );
  }

  /* -----------------------------------------------------------------------
     PHASE 4: 5.5 - 7.5 ("Gyaan Setu" Title Drops In & Lands)
     ----------------------------------------------------------------------- */
  if (elements.gyaanTitle) {
    // Stage 1: Soft fall with overshoot
    tl.to(
      elements.gyaanTitle,
      {
        opacity: 1,
        y: overshootY,
        scale: 1.02,
        duration: (T_GYAAN_DROP_END - T_GYAAN_DROP_START) * 0.7,
        ease: "power3.out",
      },
      T_GYAAN_DROP_START
    );

    // Stage 2: Settle to exact 0 position and scale 1.0
    tl.to(
      elements.gyaanTitle,
      {
        y: 0,
        scale: 1.0,
        duration: (T_GYAAN_DROP_END - T_GYAAN_DROP_START) * 0.3,
        ease: "power2.inOut",
      },
      T_GYAAN_DROP_START + (T_GYAAN_DROP_END - T_GYAAN_DROP_START) * 0.7
    );
  }

  // Optional ink-splash feel: faint radial glow/aura expanding and fading
  if (elements.gyaanTitleSplash) {
    const splashStartTime = T_GYAAN_DROP_START + 0.6;
    tl.to(
      elements.gyaanTitleSplash,
      {
        opacity: 0.5,
        scale: 1.08,
        duration: 0.35,
        ease: "power2.out",
      },
      splashStartTime
    );
    tl.to(
      elements.gyaanTitleSplash,
      {
        opacity: 0,
        scale: 1.35,
        duration: 0.65,
        ease: "power1.out",
      },
      splashStartTime + 0.35
    );
  }

  /* -----------------------------------------------------------------------
     SETUP SCROLLTRIGGER WITH PINNING & 40vh RESTING HOLD
     ----------------------------------------------------------------------- */
  // The total scroll distance includes 600vh active timeline + 40vh resting hold
  const totalPixels = window.innerHeight * (TOTAL_SCROLL_PIN_VH / 100);
  const activeFraction = SCROLL_DISTANCE_VH / TOTAL_SCROLL_PIN_VH;

  ScrollTrigger.create({
    trigger: triggerContainer,
    start: "top top",
    end: `+=${totalPixels}`,
    pin: true,
    anticipatePin: 1,
    scrub: 1,
    onUpdate: (self) => {
      // Map self.progress (0 to 1 over 640vh) so active animation runs over first 600vh,
      // and clamps at 1.0 (final frame hold) for the remaining 40vh!
      const timelineProgress = Math.min(1, self.progress / activeFraction);
      tl.progress(timelineProgress);

      // Hero is active in view while progress < 1.0; ensure heroPast is strictly false
      if (typeof window !== "undefined") {
        if (self.progress < 1.0) {
          window.dispatchEvent(
            new CustomEvent("gyaan-hero-past", { detail: { past: false } })
          );
        }
        window.dispatchEvent(new Event("gyaan-scroll"));
      }
    },
    onLeave: () => {
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("gyaan-scroll"));
      }
    },
    onEnterBack: () => {
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("gyaan-hero-past", { detail: { past: false } })
        );
        window.dispatchEvent(new Event("gyaan-scroll"));
      }
    },
  });

  return tl;
}
