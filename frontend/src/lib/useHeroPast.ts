"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";

/**
 * Hook to track whether the scroll animation hero has been scrolled past.
 * 
 * Requirements:
 * - On non-home routes (/library, /tutor, etc.), always returns true
 *   (Navbar and OrnateFrame are permanently visible).
 * - On the home route (/), returns false while the user is anywhere within
 *   the hero animation or while the hero canvas is visible on screen.
 * - Only turns true once the user has scrolled past the scroll animation,
 *   so the navbar and ornate frame never overlap with the hero artwork.
 */
export function useHeroPast(): boolean {
  const pathname = usePathname();
  const isHome = pathname === "/";
  const [heroPast, setHeroPast] = useState(!isHome);

  useEffect(() => {
    if (!isHome) {
      setHeroPast(true);
      return;
    }

    // On home route, default to false immediately
    setHeroPast(false);

    const checkHeroPosition = () => {
      // 1. Check the anchor placed immediately after the hero canvas
      const anchor = document.getElementById("hero-end-anchor");
      if (anchor) {
        const rect = anchor.getBoundingClientRect();
        // The hero canvas has fully exited the viewport when the anchor is at or above top
        const isPast = rect.top <= 20;
        setHeroPast(isPast);
        return;
      }

      // 2. Fallback: check the hero section container's bottom edge
      const heroSection = document.getElementById("gyaan-hero-section");
      if (heroSection) {
        const rect = heroSection.getBoundingClientRect();
        const isPast = rect.bottom <= 20;
        setHeroPast(isPast);
        return;
      }

      // 3. Fallback: window scroll position vs hero height (640vh pin + 100vh stage)
      const scrollY = window.scrollY || document.documentElement.scrollTop;
      const heroDistance = window.innerHeight * 7.0;
      setHeroPast(scrollY >= heroDistance);
    };

    // Check position on mount
    checkHeroPosition();

    // Custom event dispatched from ScrollTrigger (e.g. onEnterBack or while scrubbing)
    const handleHeroCustomEvent = (e: Event) => {
      const custom = e as CustomEvent<{ past: boolean }>;
      if (typeof custom.detail?.past === "boolean") {
        if (!custom.detail.past) {
          // Explicitly forced false (e.g. user is actively inside the animation)
          setHeroPast(false);
        } else {
          checkHeroPosition();
        }
      }
    };

    window.addEventListener("gyaan-hero-past", handleHeroCustomEvent);
    window.addEventListener("gyaan-scroll", checkHeroPosition, { passive: true });
    window.addEventListener("scroll", checkHeroPosition, { passive: true });
    window.addEventListener("resize", checkHeroPosition, { passive: true });

    // Brief settling timeout for initial hydration
    const timeout = setTimeout(checkHeroPosition, 150);

    return () => {
      clearTimeout(timeout);
      window.removeEventListener("gyaan-hero-past", handleHeroCustomEvent);
      window.removeEventListener("gyaan-scroll", checkHeroPosition);
      window.removeEventListener("scroll", checkHeroPosition);
      window.removeEventListener("resize", checkHeroPosition);
    };
  }, [isHome, pathname]);

  return heroPast;
}
