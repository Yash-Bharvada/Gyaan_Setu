"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import GyaanSetuScrollHero from "@/components/GyaanSetuScrollHero";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { useI18n } from "@/lib/i18n";
import { apiClient, HealthStatus } from "@/lib/api";

export default function Home() {
  const { t } = useI18n();
  const [backendHealthy, setBackendHealthy] = useState<boolean>(true);
  const [healthData, setHealthData] = useState<HealthStatus | null>(null);
  const [sourcesCount, setSourcesCount] = useState<number>(0);
  const [conceptsCount, setConceptsCount] = useState<number>(0);
  const [masteryPct, setMasteryPct] = useState<number>(0);
  const [showTelemetry, setShowTelemetry] = useState<boolean>(false);

  useEffect(() => {
    async function loadTelemetry() {
      try {
        const health = await apiClient.getHealth();
        setHealthData(health);
        setBackendHealthy(health.status === "ok");

        const sources = await apiClient.getSources();
        setSourcesCount(sources ? sources.length : 0);

        const graph = await apiClient.getKnowledgeGraph();
        setConceptsCount(graph && graph.nodes ? graph.nodes.length : 0);

        const mastery = await apiClient.getStudentMastery(1);
        if (mastery && mastery.length) {
          const avg = Math.round(
            (mastery.reduce((acc, m) => acc + (m.p_known ?? 0.5), 0) / mastery.length) * 100
          );
          setMasteryPct(avg);
        } else {
          setMasteryPct(0);
        }
      } catch (err) {
        console.warn("Home telemetry load warning:", err);
      }
    }
    loadTelemetry();
  }, []);

  return (
    <div className="w-full flex flex-col items-center">
      {/* 1. SCROLL ANIMATION HERO (Navbar and Ornate Border hidden while active) */}
      <section id="gyaan-hero-section" className="w-full relative z-10">
        <GyaanSetuScrollHero />
      </section>

      {/* Hero Boundary Sentinel: Hero has scrolled past once this passes top */}
      <div id="hero-end-anchor" className="w-full h-px pointer-events-none" />

      {/* 2. MAIN APPLICATION CONTENT (Navbar and Ornate Border appear here) */}
      <div id="main-content" className="w-full max-w-6xl mx-auto px-4 md:px-8 py-16 space-y-16 relative z-20">
        {/* Core Headline & CTAs */}
        <section className="w-full text-center space-y-6 max-w-4xl mx-auto pt-6">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#1A1210]/70 text-[#E2A63A] border border-[#E2A63A] text-xs md:text-sm font-bold uppercase tracking-widest shadow-md">
            <span className="w-2 h-2 rounded-full bg-[#D4211C]" />
            <span>{t("heroBadge")}</span>
          </div>

          <h1 className="font-display text-4xl sm:text-5xl md:text-6xl text-[#F7EDCF] tracking-wide leading-tight drop-shadow-xl">
            {t("heroHeadline")}
          </h1>

          <p className="text-[#F7EDCF]/90 text-lg md:text-xl leading-relaxed max-w-2xl mx-auto font-sans">
            {t("heroSubtitle")}
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link href="/tutor" className="btn-primary-pill shadow-xl text-lg">
              <span>{t("btnStartLearning")}</span>
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </Link>

            <Link href="/library" className="btn-secondary-pill shadow-xl text-lg">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <span>{t("btnUploadMaterial")}</span>
            </Link>

            <Link
              href="/tutor"
              className="px-6 py-3.5 rounded-full bg-[#E2A63A] hover:bg-[#F4C76D] text-[#1A1210] font-bold text-base transition-transform active:scale-95 shadow-lg"
            >
              <span>{t("btnAskTutor")}</span>
            </Link>
          </div>

          {/* LIVE BACKEND STATUS & LEARNING PULSE HUD */}
          <div className="w-full pt-8 max-w-4xl mx-auto">
            <div className="p-5 md:p-6 rounded-2xl bg-[#1A1210]/90 border-2 border-[#E2A63A]/60 shadow-2xl backdrop-blur-md space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2A63A]/20 pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="relative flex h-3 w-3">
                    <span
                      className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                        backendHealthy ? "bg-emerald-400" : "bg-amber-400"
                      }`}
                    />
                    <span
                      className={`relative inline-flex rounded-full h-3 w-3 ${
                        backendHealthy ? "bg-emerald-500" : "bg-amber-500"
                      }`}
                    />
                  </span>
                  <span className="font-mono text-xs md:text-sm font-semibold tracking-wider text-[#F7EDCF]">
                    {backendHealthy ? "FASTAPI BACKEND CONNECTED" : "CONNECTING TO FASTAPI BACKEND..."}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-[#E2A63A]/15 text-[#E2A63A] border border-[#E2A63A]/30">
                    http://127.0.0.1:8000
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono text-[#F7EDCF]/70">
                  <span className="hidden sm:inline">Learner:</span>
                  <span className="px-2 py-0.5 rounded bg-[#2D211D] text-[#E2A63A] font-bold border border-[#E2A63A]/20">
                    Alex Chen (ID #1)
                  </span>
                  <button
                    onClick={() => setShowTelemetry(!showTelemetry)}
                    className="ml-2 text-[11px] text-[#E2A63A] underline hover:text-[#F4C76D] cursor-pointer"
                  >
                    {showTelemetry ? "Hide Diagnostics" : "Diagnostics"}
                  </button>
                </div>
              </div>

              {/* 4 Real-Time Metrics Counters */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-left">
                <Link
                  href="/library"
                  className="p-3 rounded-xl bg-[#2D211D]/80 border border-[#E2A63A]/20 hover:border-[#E2A63A] hover:bg-[#2D211D] transition-all group"
                >
                  <div className="text-[11px] uppercase tracking-wider text-[#E2A63A]/80 font-mono">
                    Ingested Docs
                  </div>
                  <div className="text-2xl font-bold font-display text-[#F7EDCF] group-hover:text-[#E2A63A] transition-colors">
                    {sourcesCount}
                  </div>
                  <div className="text-[11px] text-[#F7EDCF]/60 flex items-center justify-between mt-1">
                    <span>Course Materials</span>
                    <span>→</span>
                  </div>
                </Link>

                <Link
                  href="/progress"
                  className="p-3 rounded-xl bg-[#2D211D]/80 border border-[#E2A63A]/20 hover:border-[#E2A63A] hover:bg-[#2D211D] transition-all group"
                >
                  <div className="text-[11px] uppercase tracking-wider text-[#E2A63A]/80 font-mono">
                    Curriculum DAG
                  </div>
                  <div className="text-2xl font-bold font-display text-[#F7EDCF] group-hover:text-[#E2A63A] transition-colors">
                    {conceptsCount}
                  </div>
                  <div className="text-[11px] text-[#F7EDCF]/60 flex items-center justify-between mt-1">
                    <span>Concepts Mapped</span>
                    <span>→</span>
                  </div>
                </Link>

                <Link
                  href="/practice"
                  className="p-3 rounded-xl bg-[#2D211D]/80 border border-[#E2A63A]/20 hover:border-[#E2A63A] hover:bg-[#2D211D] transition-all group"
                >
                  <div className="text-[11px] uppercase tracking-wider text-[#E2A63A]/80 font-mono">
                    BKT Mastery
                  </div>
                  <div className="text-2xl font-bold font-display text-[#E2A63A] group-hover:text-[#F4C76D] transition-colors">
                    {masteryPct}%
                  </div>
                  <div className="text-[11px] text-[#F7EDCF]/60 flex items-center justify-between mt-1">
                    <span>Adaptive State</span>
                    <span>→</span>
                  </div>
                </Link>

                <Link
                  href="/revise"
                  className="p-3 rounded-xl bg-[#2D211D]/80 border border-[#E2A63A]/20 hover:border-[#E2A63A] hover:bg-[#2D211D] transition-all group"
                >
                  <div className="text-[11px] uppercase tracking-wider text-[#E2A63A]/80 font-mono">
                    Flashcards
                  </div>
                  <div className="text-2xl font-bold font-display text-[#F7EDCF] group-hover:text-[#E2A63A] transition-colors">
                    SM-2
                  </div>
                  <div className="text-[11px] text-[#F7EDCF]/60 flex items-center justify-between mt-1">
                    <span>Spaced Review</span>
                    <span>→</span>
                  </div>
                </Link>
              </div>

              {/* Collapsible Telemetry JSON */}
              {showTelemetry && (
                <div className="mt-3 p-3 rounded-lg bg-[#0F0A08] border border-[#E2A63A]/30 text-left font-mono text-xs text-[#E2A63A]/90 overflow-x-auto">
                  <div className="text-[10px] text-[#F7EDCF]/50 mb-1">LIVE SYSTEM HEALTH PAYLOAD (/api/v1/health):</div>
                  <pre className="whitespace-pre-wrap">{JSON.stringify(healthData, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </section>

        <GreekKeyDivider />

        {/* 3. FIVE MODULE PILLARS */}
        <section className="w-full space-y-8">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="font-display text-3xl md:text-4xl text-[#F7EDCF] tracking-wide">
              The Gyaan Setu Learning Ecosystem
            </h2>
            <p className="text-[#F7EDCF]/85 text-base">
              Every screen is engineered with source verification, adaptive mastery, and cognitive science.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Card 1: Library */}
            <DoubleGoldCard size="md" className="flex flex-col justify-between hover:scale-[1.02] transition-transform">
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center font-bold text-lg">
                  01
                </div>
                <h3 className="font-display text-2xl text-[#1A1210]">
                  {t("featLibraryTitle")}
                </h3>
                <p className="text-sm text-[#54423C] leading-relaxed">
                  {t("featLibraryDesc")}
                </p>
              </div>
              <div className="pt-6">
                <Link
                  href="/library"
                  className="text-sm font-bold text-[#8C5D0D] hover:underline flex items-center gap-1.5"
                >
                  <span>Open Library</span>
                  <span>→</span>
                </Link>
              </div>
            </DoubleGoldCard>

            {/* Card 2: Tutor */}
            <DoubleGoldCard size="md" className="flex flex-col justify-between hover:scale-[1.02] transition-transform">
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center font-bold text-lg">
                  02
                </div>
                <h3 className="font-display text-2xl text-[#1A1210]">
                  {t("featTutorTitle")}
                </h3>
                <p className="text-sm text-[#54423C] leading-relaxed">
                  {t("featTutorDesc")}
                </p>
              </div>
              <div className="pt-6">
                <Link
                  href="/tutor"
                  className="text-sm font-bold text-[#8C5D0D] hover:underline flex items-center gap-1.5"
                >
                  <span>Ask the Tutor</span>
                  <span>→</span>
                </Link>
              </div>
            </DoubleGoldCard>

            {/* Card 3: Practice */}
            <DoubleGoldCard size="md" className="flex flex-col justify-between hover:scale-[1.02] transition-transform">
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center font-bold text-lg">
                  03
                </div>
                <h3 className="font-display text-2xl text-[#1A1210]">
                  {t("featPracticeTitle")}
                </h3>
                <p className="text-sm text-[#54423C] leading-relaxed">
                  {t("featPracticeDesc")}
                </p>
              </div>
              <div className="pt-6">
                <Link
                  href="/practice"
                  className="text-sm font-bold text-[#8C5D0D] hover:underline flex items-center gap-1.5"
                >
                  <span>Start Practice Quiz</span>
                  <span>→</span>
                </Link>
              </div>
            </DoubleGoldCard>

            {/* Card 4: Revise */}
            <DoubleGoldCard size="md" className="flex flex-col justify-between hover:scale-[1.02] transition-transform">
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center font-bold text-lg">
                  04
                </div>
                <h3 className="font-display text-2xl text-[#1A1210]">
                  {t("featReviseTitle")}
                </h3>
                <p className="text-sm text-[#54423C] leading-relaxed">
                  {t("featReviseDesc")}
                </p>
              </div>
              <div className="pt-6">
                <Link
                  href="/revise"
                  className="text-sm font-bold text-[#8C5D0D] hover:underline flex items-center gap-1.5"
                >
                  <span>Review Flashcards & Brief</span>
                  <span>→</span>
                </Link>
              </div>
            </DoubleGoldCard>

            {/* Card 5: Progress & Knowledge Graph */}
            <DoubleGoldCard
              size="md"
              className="flex flex-col justify-between hover:scale-[1.02] transition-transform md:col-span-2 lg:col-span-2"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center font-bold text-lg">
                  05
                </div>
                <h3 className="font-display text-2xl text-[#1A1210]">
                  {t("featProgressTitle")}
                </h3>
                <p className="text-sm text-[#54423C] leading-relaxed">
                  {t("featProgressDesc")}
                </p>
              </div>
              <div className="pt-6">
                <Link
                  href="/progress"
                  className="text-sm font-bold text-[#8C5D0D] hover:underline flex items-center gap-1.5"
                >
                  <span>Inspect Prerequisite DAG Map</span>
                  <span>→</span>
                </Link>
              </div>
            </DoubleGoldCard>
          </div>
        </section>

        {/* 4. ACADEMIC INTEGRITY & COMPARISON PANEL */}
        <section className="w-full">
          <div className="p-8 md:p-12 rounded-[32px] bg-[#1A1210] border-2 border-[#E2A63A] text-left shadow-2xl space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E2A63A]/30 pb-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-[#E2A63A]">
                  Academic Integrity & Verifiability
                </span>
                <h3 className="font-display text-2xl md:text-3xl text-[#F7EDCF]">
                  Why Gyaan Setu Outperforms Generic AI
                </h3>
              </div>
              <span className="px-4 py-1.5 rounded-full bg-[#D4211C] text-white text-xs font-bold w-fit">
                Zero Unverifiable Claims
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div className="p-6 rounded-2xl bg-[#2D211D] border border-red-500/30 space-y-2">
                <h4 className="font-bold text-red-300 flex items-center gap-2 text-base">
                  <span className="text-red-400">✕</span> Generic Generative AI
                </h4>
                <p className="text-[#F7EDCF]/70 leading-relaxed font-sans">
                  Invent plausible-sounding formulas, hallucinate non-existent chapters, and answer trivia with zero grounding in your syllabus.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-[#2D211D] border border-emerald-500/30 space-y-2">
                <h4 className="font-bold text-emerald-300 flex items-center gap-2 text-base">
                  <span className="text-emerald-400">✓</span> Gyaan Setu Grounded RAG
                </h4>
                <p className="text-[#F7EDCF]/70 leading-relaxed font-sans">
                  Answers with clickable citations pointing to exact textbook pages, slide deck numbers, and video timestamps. Refuses queries when facts are absent from your course materials.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
