"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { useHeroPast } from "@/lib/useHeroPast";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { lang, setLang, t } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const heroPast = useHeroPast();

  // Close menu automatically on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Close menu when route changes
  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  // Prevent background scrolling while the side menu drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const navItems = [
    {
      href: "/",
      label: t("navHome"),
      desc: lang === "hi" ? "कवर एवं अवलोकन" : "Overview & Cover",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      ),
    },
    {
      href: "/library",
      label: t("navLibrary"),
      desc: lang === "hi" ? "अध्ययन सामग्री व फाइलें" : "Uploads & Source Units",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
          <path d="M6 6h10M6 10h10" />
        </svg>
      ),
    },
    {
      href: "/tutor",
      label: t("navTutor"),
      desc: lang === "hi" ? "सटीक संदर्भों सहित प्रश्न-उत्तर" : "Grounded Socratic Dialogue",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      ),
    },
    {
      href: "/practice",
      label: t("navPractice"),
      desc: lang === "hi" ? "अनुकूली प्रश्नोत्तरी व मूल्यांकन" : "Bloom's Taxonomy Quizzes",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="9 11 12 14 22 4" />
          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
        </svg>
      ),
    },
    {
      href: "/revise",
      label: t("navRevise"),
      desc: lang === "hi" ? "स्मृति फ्लैशकार्ड व ऑडियो संक्षेप" : "SM-2 Cards & Audio Brief",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
          <path d="M21 3v5h-5" />
          <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
          <path d="M8 16H3v5" />
        </svg>
      ),
    },
    {
      href: "/progress",
      label: t("navProgress"),
      desc: lang === "hi" ? "ज्ञान आरेख व निपुणता मापक" : "Prerequisite DAG Mastery",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 3v18h18" />
          <path d="m19 9-5 5-4-4-3 3" />
        </svg>
      ),
    },
  ];

  return (
    <>
      {/* ===================================================================
          FLOATING CONTROLLER BAR (NON-INTRUSIVE CORNER DOCK)
          Does not span across the center of the viewport, eliminating overlap!
          Respects heroPast: Hidden during scroll hero animation on home page.
          =================================================================== */}
      <div
        className={`fixed top-4 left-0 right-0 z-50 pointer-events-none transition-all duration-500 ease-out px-4 md:px-8 ${
          heroPast
            ? "opacity-100 translate-y-0 visible"
            : "opacity-0 -translate-y-20 invisible"
        }`}
      >
        <div className="w-full max-w-7xl mx-auto flex items-center justify-between">
          {/* LEFT: Collapsible Side Menu Trigger Button */}
          <button
            onClick={() => setIsOpen(true)}
            aria-label="Open navigation menu"
            aria-expanded={isOpen}
            className="pointer-events-auto flex items-center gap-3 px-4 py-2.5 rounded-full bg-[#F7EDCF] text-[#1A1210] border-[2.5px] border-[#E2A63A] transition-all duration-200 hover:scale-105 active:scale-95 group focus:outline-none focus:ring-2 focus:ring-[#E2A63A]"
            style={{
              boxShadow:
                "0 0 0 2px #F7EDCF, 0 0 0 4px #E2A63A, 0 8px 24px rgba(0,0,0,0.35)",
            }}
          >
            {/* Animated Hamburger Icon */}
            <div className="w-5 h-4 flex flex-col justify-between py-0.5">
              <span className="w-5 h-[2.5px] bg-[#1A1210] group-hover:bg-[#8C5D0D] transition-colors rounded-full" />
              <span className="w-3.5 h-[2.5px] bg-[#1A1210] group-hover:bg-[#8C5D0D] transition-colors rounded-full" />
              <span className="w-5 h-[2.5px] bg-[#1A1210] group-hover:bg-[#8C5D0D] transition-colors rounded-full" />
            </div>

            {/* Brand Logo Text */}
            <span className="font-display text-xl text-[#1A1210] tracking-wide group-hover:text-[#8C5D0D] transition-colors">
              {t("brandName")}
            </span>
            <span className="w-2 h-2 rounded-full bg-[#D4211C]" />

            {/* Menu Label Tag */}
            <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded-full bg-[#1A1210]/10 text-[#8C5D0D] text-xs font-bold uppercase tracking-wider">
              {lang === "hi" ? "मेन्यू" : "Menu"}
            </span>
          </button>

          {/* RIGHT: Quick Language Switcher Pill */}
          <div
            className="pointer-events-auto flex items-center bg-[#F7EDCF] rounded-full p-1 border-[2.5px] border-[#E2A63A] transition-all hover:scale-105"
            style={{
              boxShadow:
                "0 0 0 2px #F7EDCF, 0 0 0 4px #E2A63A, 0 8px 20px rgba(0,0,0,0.3)",
            }}
          >
            <button
              onClick={() => setLang("en")}
              className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                lang === "en"
                  ? "bg-[#1A1210] text-[#F7EDCF] shadow-sm"
                  : "text-[#1A1210] hover:text-[#8C5D0D]"
              }`}
              aria-label="Switch to English"
            >
              EN
            </button>
            <span className="text-[#8C5D0D] text-xs font-bold px-1">|</span>
            <button
              onClick={() => setLang("hi")}
              className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                lang === "hi"
                  ? "bg-[#1A1210] text-[#F7EDCF] shadow-sm"
                  : "text-[#1A1210] hover:text-[#8C5D0D]"
              }`}
              aria-label="Switch to Hindi"
            >
              हिं
            </button>
          </div>
        </div>
      </div>

      {/* ===================================================================
          BACKDROP OVERLAY
          =================================================================== */}
      <div
        onClick={() => setIsOpen(false)}
        className={`fixed inset-0 z-50 bg-black/65 backdrop-blur-sm transition-opacity duration-300 ${
          isOpen
            ? "opacity-100 pointer-events-auto"
            : "opacity-0 pointer-events-none"
        }`}
        aria-hidden="true"
      />

      {/* ===================================================================
          COLLAPSIBLE SIDE MENU DRAWER
          =================================================================== */}
      <aside
        aria-label="Navigation drawer"
        className={`fixed inset-y-0 left-0 z-50 w-84 sm:w-96 bg-[#F7EDCF] text-[#1A1210] border-r-[3.5px] border-[#E2A63A] flex flex-col justify-between shadow-[15px_0_45px_rgba(0,0,0,0.6)] transition-transform duration-300 ease-out ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* TOP: Drawer Header */}
        <div className="p-6 pb-4 border-b border-[#E2A63A]/30">
          <div className="flex items-center justify-between">
            <Link
              href="/"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2 group"
            >
              <span className="font-display text-3xl text-[#1A1210] tracking-wide group-hover:text-[#8C5D0D] transition-colors">
                {t("brandName")}
              </span>
              <span className="w-2.5 h-2.5 rounded-full bg-[#D4211C]" />
            </Link>

            {/* Close Button */}
            <button
              onClick={() => setIsOpen(false)}
              aria-label="Close navigation menu"
              className="w-9 h-9 rounded-full bg-[#1A1210]/10 hover:bg-[#1A1210] text-[#1A1210] hover:text-[#F7EDCF] border border-[#E2A63A] flex items-center justify-center transition-all hover:rotate-90"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <p className="mt-1 text-xs text-[#8C5D0D] font-bold tracking-wider">
            {t("brandTagline")}
          </p>

          <div className="mt-4 pt-2">
            <GreekKeyDivider />
          </div>
        </div>

        {/* MIDDLE: Scrollable Navigation Links */}
        <nav
          className="flex-1 overflow-y-auto px-4 py-4 space-y-1.5"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
        >
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={`flex items-center gap-3.5 px-4 py-3 rounded-2xl transition-all duration-200 group ${
                  isActive
                    ? "bg-[#1A1210] text-[#F7EDCF] shadow-md border-l-4 border-[#E2A63A]"
                    : "text-[#1A1210] hover:bg-[#E2A63A]/20 hover:text-[#8C5D0D]"
                }`}
              >
                {/* Icon Container */}
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110 ${
                    isActive
                      ? "bg-[#E2A63A] text-[#1A1210] shadow-sm"
                      : "bg-[#1A1210]/10 text-[#1A1210]"
                  }`}
                >
                  {item.icon}
                </div>

                {/* Text Labels */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-base tracking-wide">
                      {item.label}
                    </span>
                    {isActive && (
                      <span className="w-2 h-2 rounded-full bg-[#E2A63A] animate-pulse" />
                    )}
                  </div>
                  <p
                    className={`text-xs truncate ${
                      isActive ? "text-[#F7EDCF]/75" : "text-[#8C5D0D]/90"
                    }`}
                  >
                    {item.desc}
                  </p>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* BOTTOM: Academic Integrity Badge & Quick CTA */}
        <div className="p-5 border-t border-[#E2A63A]/30 bg-[#F7EDCF]/80 space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-[#8C5D0D]">
            <span>{lang === "hi" ? "भाषा चयन:" : "Language:"}</span>
            <div className="flex items-center bg-[#E2A63A]/20 rounded-full p-0.5 border border-[#E2A63A]">
              <button
                onClick={() => setLang("en")}
                className={`px-2.5 py-0.5 rounded-full text-xs font-bold transition-all ${
                  lang === "en"
                    ? "bg-[#1A1210] text-[#F7EDCF]"
                    : "text-[#1A1210] hover:text-[#8C5D0D]"
                }`}
              >
                EN
              </button>
              <button
                onClick={() => setLang("hi")}
                className={`px-2.5 py-0.5 rounded-full text-xs font-bold transition-all ${
                  lang === "hi"
                    ? "bg-[#1A1210] text-[#F7EDCF]"
                    : "text-[#1A1210] hover:text-[#8C5D0D]"
                }`}
              >
                हिं
              </button>
            </div>
          </div>

          <Link
            href="/tutor"
            onClick={() => setIsOpen(false)}
            className="w-full flex items-center justify-center gap-2 py-3 rounded-full bg-[#1A1210] hover:bg-[#8C5D0D] text-[#F7EDCF] font-bold text-sm transition-all shadow-md active:scale-95 border border-[#E2A63A]"
          >
            <span>{t("btnAskTutor")}</span>
            <span>→</span>
          </Link>

          <p className="text-[10px] text-center text-[#8C5D0D]/80 uppercase tracking-widest font-bold">
            100% Free-Tier & Local-Stack Architecture
          </p>
        </div>
      </aside>
    </>
  );
};
