"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import {
  CANVAS_WIDTH,
  CANVAS_HEIGHT,
  CANVAS_ASPECT_RATIO,
  TOTAL_SCROLL_PIN_VH,
  SCROLL_DISTANCE_VH,
  REST_HOLD_VH,
  LAYERS,
  buildGyaanSetuTimeline,
  HeroTimelineElements,
} from "@/lib/timeline";

// Register ScrollTrigger client-side
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

export default function GyaanSetuScrollHero() {
  // Container & Stage Refs
  const triggerContainerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  // Element Refs for GSAP
  const scrollHintRef = useRef<HTMLDivElement>(null);
  const gyaanTitleRef = useRef<HTMLDivElement>(null);
  const gyaanSplashRef = useRef<HTMLDivElement>(null);
  const dogRef = useRef<HTMLDivElement>(null);
  const girlChairRef = useRef<HTMLDivElement>(null);
  const inkstoneRef = useRef<HTMLDivElement>(null);
  const parchmentRef = useRef<HTMLDivElement>(null);
  const inkOnParchmentRef = useRef<HTMLDivElement>(null);
  const brushStandRef = useRef<HTMLDivElement>(null);
  const floatingInkRef = useRef<HTMLDivElement>(null);

  // Lenis & Timeline references
  const lenisRef = useRef<Lenis | null>(null);
  const masterTimelineRef = useRef<gsap.core.Timeline | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [loadProgress, setLoadProgress] = useState(0);
  const [showDebug, setShowDebug] = useState(false);
  const [debugData, setDebugData] = useState({
    time: 0,
    progress: 0,
    scrollPct: 0,
    phase: "Opening Cover (0.0 - 0.5)",
  });

  // Calculate current animation phase description
  const getPhaseName = (t: number) => {
    if (t < 0.5) return "1. Pristine Cover & Scroll Hint (0.0 - 0.5)";
    if (t < 4.0) return "2. Character Entrances from Left & Right (0.5 - 4.0)";
    if (t < 5.5) return "3. Settled & Gentle Idle Breathing (4.0 - 5.5)";
    if (t < 7.5) return "4. 'Gyaan Setu' Grand Title Arrival (5.5 - 7.5)";
    return "5. Final Masterpiece Cover Pose (7.5 - 8.0)";
  };

  // Keyboard shortcut to toggle debug overlay (press 'D')
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "d" || e.key === "D") {
        setShowDebug((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Preload and decode all PNG layer assets before starting animation
  useEffect(() => {
    let isCancelled = false;
    const layerImages = LAYERS.map((l) => l.src);
    let loadedCount = 0;

    const promises = layerImages.map((src) => {
      return new Promise<void>((resolve) => {
        const img = new Image();
        img.src = src;
        img.decoding = "async";

        const onDone = () => {
          if (!isCancelled) {
            loadedCount++;
            setLoadProgress(Math.round((loadedCount / layerImages.length) * 100));
            resolve();
          }
        };

        if (img.complete) {
          if ("decode" in img) {
            img.decode().then(onDone).catch(onDone);
          } else {
            onDone();
          }
        } else {
          img.onload = () => {
            if ("decode" in img) {
              img.decode().then(onDone).catch(onDone);
            } else {
              onDone();
            }
          };
          img.onerror = onDone;
        }
      });
    });

    Promise.all(promises).then(() => {
      if (!isCancelled) {
        // Small delay for smooth loader fadeout
        setTimeout(() => {
          setIsLoading(false);
        }, 300);
      }
    });

    return () => {
      isCancelled = true;
    };
  }, []);

  // Initialize Lenis, GSAP, and ScrollTrigger once assets are loaded
  useEffect(() => {
    if (isLoading) return;

    // Check prefers-reduced-motion
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Initialize Lenis smooth scroll
    const lenis = new Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 1.0,
      touchMultiplier: 1.5,
    });
    lenisRef.current = lenis;

    // Connect Lenis to ScrollTrigger and dispatch gyaan-scroll event
    lenis.on("scroll", () => {
      ScrollTrigger.update();
      window.dispatchEvent(new Event("gyaan-scroll"));
    });
    const tickerCallback = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(tickerCallback);
    gsap.ticker.lagSmoothing(0);

    // Build timeline in GSAP context for clean garbage collection
    const ctx = gsap.context(() => {
      if (!stageRef.current || !triggerContainerRef.current) return;

      const elements: HeroTimelineElements = {
        stage: stageRef.current,
        triggerContainer: triggerContainerRef.current,
        scrollHint: scrollHintRef.current,
        gyaanTitle: gyaanTitleRef.current,
        gyaanTitleSplash: gyaanSplashRef.current,
        dog: dogRef.current,
        girlChair: girlChairRef.current,
        inkstone: inkstoneRef.current,
        parchment: parchmentRef.current,
        inkOnParchment: inkOnParchmentRef.current,
        brushStand: brushStandRef.current,
        floatingInk: floatingInkRef.current,
      };

      const tl = buildGyaanSetuTimeline(elements, {
        reducedMotion,
        onProgress: (progress, time) => {
          setDebugData({
            progress,
            time: parseFloat(time.toFixed(2)),
            scrollPct: Math.round(progress * 100),
            phase: getPhaseName(time),
          });
        },
      });

      masterTimelineRef.current = tl;
    });

    // Handle window resize cleanly
    const handleResize = () => {
      ScrollTrigger.refresh();
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      gsap.ticker.remove(tickerCallback);
      lenis.destroy();
      ctx.revert();
    };
  }, [isLoading]);

  // Jump to specific timeline progress (used by Debug Panel)
  const jumpToProgress = useCallback((prog: number) => {
    if (!triggerContainerRef.current) return;
    const totalPixels = window.innerHeight * (TOTAL_SCROLL_PIN_VH / 100);
    const activeFraction = SCROLL_DISTANCE_VH / TOTAL_SCROLL_PIN_VH;
    const targetScrollY =
      triggerContainerRef.current.offsetTop + prog * activeFraction * totalPixels;

    if (lenisRef.current) {
      lenisRef.current.scrollTo(targetScrollY, { immediate: false, duration: 1 });
    } else {
      window.scrollTo({ top: targetScrollY, behavior: "smooth" });
    }
  }, []);

  return (
    <>
      {/* ===================================================================
          PRELOADER
          =================================================================== */}
      {isLoading && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#DA231D] text-white transition-opacity duration-500">
          <div className="relative flex flex-col items-center gap-6">
            {/* Pulsing ornate gold circle */}
            <div className="relative w-24 h-24 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-2 border-[#E5C158]/30 animate-ping" />
              <div className="w-16 h-16 rounded-full border-2 border-[#E5C158] flex items-center justify-center shadow-[0_0_20px_rgba(229,193,88,0.4)]">
                <span className="font-serif text-xl text-[#FDE68A] font-bold">ज्ञान</span>
              </div>
            </div>

            <div className="text-center">
              <h2 className="font-serif text-2xl tracking-[0.25em] uppercase text-[#FDE68A] font-semibold">
                Gyaan Setu
              </h2>
              <p className="mt-2 text-sm text-[#FDE68A]/70 font-sans tracking-widest uppercase">
                Loading Illustrated Scroll Canvas ({loadProgress}%)
              </p>
            </div>

            {/* Progress Bar */}
            <div className="w-48 h-1 bg-black/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#FDE68A] to-[#E5C158] transition-all duration-200"
                style={{ width: `${loadProgress}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* ===================================================================
          PINNED SCROLL HERO WRAPPER
          =================================================================== */}
      <section
        ref={triggerContainerRef}
        className="relative w-full bg-[#DA231D] overflow-hidden"
        style={{
          // Height of stage container during pinning
          height: "100vh",
        }}
      >
        {/* Fullscreen Letterbox Stage Container */}
        <div className="relative w-full h-full flex items-center justify-center overflow-hidden bg-[#DA231D]">
          {/* 
            THE 16:9 STAGE CANVAS (2752 x 1536 px)
            Scaled to fit viewport using aspect-ratio with object-fit: contain behavior.
            Portrait/mobile keeps 16:9 ratio centered vertically.
          */}
          <div
            ref={stageRef}
            className="relative select-none overflow-hidden"
            style={{
              aspectRatio: `${CANVAS_WIDTH} / ${CANVAS_HEIGHT}`,
              width: "100%",
              maxWidth: `calc(100vh * (${CANVAS_WIDTH} / ${CANVAS_HEIGHT}))`,
              maxHeight: `calc(100vw * (${CANVAS_HEIGHT} / ${CANVAS_WIDTH}))`,
              height: "auto",
            }}
          >
            {/* SVG Filter for Dry Brush Rough Edges */}
            <svg className="absolute w-0 h-0 pointer-events-none" aria-hidden="true">
              <defs>
                <filter id="dry-brush-filter" x="-20%" y="-20%" width="140%" height="140%">
                  <feTurbulence
                    type="fractalNoise"
                    baseFrequency="0.045"
                    numOctaves="3"
                    result="noise"
                  />
                  <feDisplacementMap
                    in="SourceGraphic"
                    in2="noise"
                    scale="5"
                    xChannelSelector="R"
                    yChannelSelector="G"
                  />
                </filter>
              </defs>
            </svg>

            {/* ---------------------------------------------------------------
                LAYER 1: BACKGROUND (NEVER MOVES - STATIC)
                --------------------------------------------------------------- */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{ zIndex: 1 }}
            >
              <img
                src="/layers/background_empty.png"
                alt="Gyaan Setu background stage"
                className="w-full h-full object-cover block"
                decoding="async"
              />
            </div>

            {/* ---------------------------------------------------------------
                LAYER 2: BRUSH STAND (z: 2)
                Coordinates: left 63.408%, top 41.016%, width 7.231%
                --------------------------------------------------------------- */}
            <div
              className="absolute pointer-events-none"
              style={{
                zIndex: 2,
                left: "63.408%",
                top: "41.016%",
                width: "7.231%",
              }}
            >
              <div
                ref={brushStandRef}
                className="w-full h-auto will-change-transform"
                style={{ transformOrigin: "top center" }}
              >
                <img
                  src="/layers/brush_stand.png"
                  alt="Hanging calligraphy brushes"
                  className="w-full h-auto block select-none"
                  decoding="async"
                />
              </div>
            </div>

            {/* ---------------------------------------------------------------
                LAYER 3: SCHOLAR GIRL ON CHAIR (z: 3)
                Coordinates: left 38.59%, top 29.753%, width 30.051%
                Static wrapper has soft drop shadow; inner ref animates GPU transform.
                Clean original artwork with natural white sleeves and hands!
                --------------------------------------------------------------- */}
            <div
              className="absolute pointer-events-none"
              style={{
                zIndex: 3,
                left: "38.59%",
                top: "29.753%",
                width: "30.051%",
                filter: "drop-shadow(0 12px 18px rgba(60,10,10,.25))",
              }}
            >
              <div
                ref={girlChairRef}
                className="w-full h-auto will-change-transform"
                style={{ transformOrigin: "center bottom" }}
              >
                <img
                  src="/layers/girl_chair.png"
                  alt="Scholar girl with calligraphy brush seated on wooden chair"
                  className="w-full h-auto block select-none"
                  decoding="async"
                />
              </div>
            </div>

            {/* ---------------------------------------------------------------
                LAYER 4: COMPANION DOG (z: 4)
                Coordinates: left 21.039%, top 49.349%, width 20.603%
                Static wrapper has soft drop shadow; inner ref animates GPU transform.
                --------------------------------------------------------------- */}
            <div
              className="absolute pointer-events-none"
              style={{
                zIndex: 4,
                left: "21.039%",
                top: "49.349%",
                width: "20.603%",
                filter: "drop-shadow(0 12px 18px rgba(60,10,10,.25))",
              }}
            >
              <div
                ref={dogRef}
                className="w-full h-auto will-change-transform"
                style={{ transformOrigin: "center bottom" }}
              >
                <img
                  src="/layers/dog.png"
                  alt="Companion dog with red bandana"
                  className="w-full h-auto block select-none"
                  decoding="async"
                />
              </div>
            </div>

            {/* ---------------------------------------------------------------
                LAYER 5: CARVED SCHOLAR INKSTONE (z: 5)
                Coordinates: left 32.958%, top 70.117%, width 4.397%
                Discrete individual prop: carved stone inkwell with dark ink.
                --------------------------------------------------------------- */}
            <div
              className="absolute pointer-events-none"
              style={{
                zIndex: 5,
                left: "32.958%",
                top: "70.117%",
                width: "4.397%",
                filter: "drop-shadow(0 8px 12px rgba(40,10,10,.3))",
              }}
            >
              <div
                ref={inkstoneRef}
                className="w-full h-auto will-change-transform"
                style={{ transformOrigin: "center center" }}
              >
                <img
                  src="/layers/inkstone.png"
                  alt="Carved calligraphy inkstone with dark ink well"
                  className="w-full h-auto block select-none"
                  decoding="async"
                />
              </div>
            </div>

            {/* ---------------------------------------------------------------
                LAYER 6: PARCHMENT SCROLL (z: 6)
                Coordinates: left 33.249%, top 60.091%, width 60.683%
                Static wrapper has soft drop shadow; inner ref animates GPU transform.
                --------------------------------------------------------------- */}
            <div
              className="absolute pointer-events-none"
              style={{
                zIndex: 6,
                left: "33.249%",
                top: "60.091%",
                width: "60.683%",
                filter: "drop-shadow(0 12px 18px rgba(60,10,10,.25))",
              }}
            >
              <div
                ref={parchmentRef}
                className="w-full h-auto will-change-transform"
                style={{ transformOrigin: "right center" }}
              >
                <img
                  src="/layers/parchment.png"
                  alt="Ancient rolled scroll parchment"
                  className="w-full h-auto block select-none"
                  decoding="async"
                />
              </div>
            </div>

            {/* ---------------------------------------------------------------
                LAYER 7: INK ON PARCHMENT (z: 7)
                Coordinates: left 44.84%, top 68.099%, width 40.334%
                Crisp calligraphy ink alpha; travels locked with parchment.
                --------------------------------------------------------------- */}
            <div
              className="absolute pointer-events-none"
              style={{
                zIndex: 7,
                left: "44.84%",
                top: "68.099%",
                width: "40.334%",
              }}
            >
              <div
                ref={inkOnParchmentRef}
                className="w-full h-auto will-change-transform"
                style={{ transformOrigin: "right center" }}
              >
                <img
                  src="/layers/ink_on_parchment.png"
                  alt="Calligraphic inscription on parchment"
                  className="w-full h-auto block select-none"
                  decoding="async"
                />
              </div>
            </div>

            {/* ---------------------------------------------------------------
                LAYER 8: FLOATING INK & GLYPHS (z: 8)
                Coordinates: left 64.753%, top 53.32%, width 23.256%
                Travels with parchment entrance, then subtle independent drift.
                --------------------------------------------------------------- */}
            <div
              className="absolute pointer-events-none"
              style={{
                zIndex: 8,
                left: "64.753%",
                top: "53.32%",
                width: "23.256%",
              }}
            >
              <div
                ref={floatingInkRef}
                className="w-full h-auto will-change-transform"
                style={{ transformOrigin: "center center" }}
              >
                <img
                  src="/layers/floating_ink.png"
                  alt="Floating ink swirls, bird, and mystical glyphs"
                  className="w-full h-auto block select-none"
                  decoding="async"
                />
              </div>
            </div>

            {/* ---------------------------------------------------------------
                LAYER 9: GYAAN SETU CALLIGRAPHY TITLE (z: 9)
                Manifest box: left 21.257%, top 5.99%, width 58.285%, height 23.763%
                Drops in at 5.5 - 7.5, lands at manifest position.
                --------------------------------------------------------------- */}
            <div
              className="absolute pointer-events-none"
              style={{
                zIndex: 9,
                left: "21.257%",
                top: "5.99%",
                width: "58.285%",
                height: "23.763%",
              }}
            >
              {/* Optional radial ink blur splash behind title */}
              <div
                ref={gyaanSplashRef}
                className="absolute inset-0 pointer-events-none rounded-full blur-2xl opacity-0"
                style={{
                  background:
                    "radial-gradient(circle, rgba(20,8,8,0.5) 0%, rgba(20,8,8,0.2) 50%, transparent 75%)",
                  transformOrigin: "center center",
                }}
              />

              <div
                ref={gyaanTitleRef}
                className="w-full h-auto will-change-transform opacity-0"
                style={{ transformOrigin: "center center" }}
              >
                <img
                  src="/layers/title_gyaan_setu.png"
                  alt="Gyaan Setu brush calligraphy title"
                  className="w-full h-auto block select-none"
                  decoding="async"
                />
              </div>
            </div>

            {/* ---------------------------------------------------------------
                SCROLL TO BEGIN HINT (Fades out 0.0 - 0.5)
                --------------------------------------------------------------- */}
            <div
              ref={scrollHintRef}
              className="absolute left-1/2 -translate-x-1/2 bottom-[4%] z-20 flex flex-col items-center gap-1.5 pointer-events-none transition-opacity duration-300"
            >
              <span className="text-[#FDE68A] text-xs uppercase tracking-[0.3em] font-sans drop-shadow-md">
                Scroll to Begin
              </span>
              <div className="w-5 h-8 rounded-full border border-[#FDE68A]/60 flex items-start justify-center p-1 shadow-sm">
                <div className="w-1.5 h-2 bg-[#FDE68A] rounded-full animate-bounce" />
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
