"use client";

import React, { useState, useEffect } from "react";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { SourceModal } from "@/components/ui/SourceModal";
import { useI18n } from "@/lib/i18n";
import { apiClient, Flashcard, Citation, AudioBrief } from "@/lib/api";

export default function RevisePage() {
  const { t } = useI18n();
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [audioBrief, setAudioBrief] = useState<AudioBrief | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioProgress, setAudioProgress] = useState(25); // percentage
  const [playbackRate, setPlaybackRate] = useState<"1x" | "1.5x">("1x");

  useEffect(() => {
    apiClient.getFlashcards().then(setFlashcards);
    apiClient.getAudioBrief().then(setAudioBrief);
  }, []);

  const currentCard = flashcards[currentIndex];

  const handleRating = (multiplier: number) => {
    setIsFlipped(false);
    setTimeout(() => {
      if (currentIndex < flashcards.length - 1) {
        setCurrentIndex((prev) => prev + 1);
      } else {
        setCurrentIndex(0);
      }
    }, 200);
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-8 pt-24 pb-12 space-y-10">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <h1 className="font-display text-4xl md:text-5xl text-[#F7EDCF] tracking-wide drop-shadow-md">
          {t("reviseTitle")}
        </h1>
        <p className="text-[#F7EDCF]/90 text-lg">
          {t("reviseSubtitle")}
        </p>
      </div>

      {/* FLASHCARD SECTION (Interactive 3D Flip) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-2">
          <span className="text-sm font-bold uppercase tracking-wider text-[#E2A63A]">
            Active Recall Flashcards (SM-2 / FSRS)
          </span>
          <span className="text-xs font-bold text-[#F7EDCF] bg-[#1A1210]/60 px-3 py-1 rounded-full border border-[#E2A63A]/40">
            Card {currentIndex + 1} of {flashcards.length}
          </span>
        </div>

        {currentCard ? (
          <div className="perspective-1000">
            <div
              onClick={() => setIsFlipped(!isFlipped)}
              className="relative w-full min-h-[320px] md:min-h-[360px] cursor-pointer transition-transform duration-500 transform-style-preserve-3d"
            >
              <DoubleGoldCard
                size="lg"
                className={`w-full min-h-[320px] md:min-h-[360px] flex flex-col justify-between select-none transition-all ${
                  isFlipped ? "bg-[#FAF4E4]" : "bg-[#F7EDCF]"
                }`}
              >
                {/* Card Top Metadata */}
                <div className="flex items-center justify-between border-b border-[#E2A63A]/30 pb-3">
                  <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-[#1A1210] text-[#F7EDCF]">
                    {currentCard.topic_name}
                  </span>
                  <span className="text-xs font-medium text-[#63524C]">
                    {isFlipped ? "Explanation & Source" : "Question / Prompt"}
                  </span>
                </div>

                {/* Card Center Content */}
                <div className="py-8 text-center px-4 space-y-4">
                  {!isFlipped ? (
                    <div>
                      <p className="text-2xl md:text-3xl font-serif text-[#1A1210] font-bold leading-relaxed">
                        {currentCard.front}
                      </p>
                      <p className="text-xs text-[#8C5D0D] font-bold mt-4 animate-pulse">
                        {t("reviseFlipPrompt")}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4 text-left">
                      <p className="text-lg md:text-xl font-sans text-[#1A1210] leading-relaxed whitespace-pre-wrap">
                        {currentCard.back}
                      </p>

                      <div className="pt-3 border-t border-[#E2A63A]/30 flex items-center gap-2">
                        <span className="text-xs font-bold text-[#8C5D0D]">Source:</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedCitation(currentCard.citation);
                          }}
                          className="chip-citation"
                        >
                          <span>{currentCard.citation.source_title}</span>
                          <span>•</span>
                          <span>{currentCard.citation.locator}</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Card Bottom: SM-2 Spaced Repetition Buttons when flipped */}
                <div className="pt-3 border-t border-[#E2A63A]/30 flex items-center justify-between">
                  <span className="text-xs text-[#63524C]">
                    Interval: {currentCard.interval_days}d • Stability: {currentCard.stability}
                  </span>

                  {isFlipped ? (
                    <div
                      className="flex items-center gap-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => handleRating(0.5)}
                        className="px-3.5 py-1.5 rounded-full bg-red-100 hover:bg-red-200 text-red-900 text-xs font-bold border border-red-300 transition-colors"
                      >
                        {t("reviseRatingAgain")}
                      </button>
                      <button
                        onClick={() => handleRating(1.0)}
                        className="px-3.5 py-1.5 rounded-full bg-amber-100 hover:bg-amber-200 text-amber-900 text-xs font-bold border border-amber-300 transition-colors"
                      >
                        {t("reviseRatingHard")}
                      </button>
                      <button
                        onClick={() => handleRating(1.5)}
                        className="px-3.5 py-1.5 rounded-full bg-blue-100 hover:bg-blue-200 text-blue-900 text-xs font-bold border border-blue-300 transition-colors"
                      >
                        {t("reviseRatingGood")}
                      </button>
                      <button
                        onClick={() => handleRating(2.0)}
                        className="px-3.5 py-1.5 rounded-full bg-emerald-100 hover:bg-emerald-200 text-emerald-900 text-xs font-bold border border-emerald-300 transition-colors"
                      >
                        {t("reviseRatingEasy")}
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-[#8C5D0D] font-bold">
                      Click card to flip
                    </span>
                  )}
                </div>
              </DoubleGoldCard>
            </div>
          </div>
        ) : null}
      </div>

      <GreekKeyDivider />

      {/* AUDIO REVISION BRIEF PLAYER */}
      {audioBrief && (
        <DoubleGoldCard size="md" className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E2A63A]/30 pb-3">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#D4211C]">
                {t("reviseAudioBrief")}
              </span>
              <h3 className="font-display text-2xl text-[#1A1210]">
                {audioBrief.title}
              </h3>
            </div>
            <span className="text-xs font-bold text-[#8C5D0D] bg-[#E2A63A]/20 px-3 py-1 rounded-full border border-[#E2A63A] w-fit">
              Duration: 5m 12s
            </span>
          </div>

          {/* Interactive Player Controls */}
          <div className="p-4 rounded-2xl bg-white border border-[#E2A63A]/40 shadow-inner flex flex-col md:flex-row items-center gap-6">
            {/* Play/Pause Button */}
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="w-14 h-14 rounded-full bg-[#1A1210] text-[#F7EDCF] hover:bg-[#2E201B] flex items-center justify-center shadow-lg transition-transform active:scale-95 shrink-0"
              aria-label={isPlaying ? "Pause audio brief" : "Play audio brief"}
            >
              {isPlaying ? (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="4" width="4" height="16" />
                  <rect x="14" y="4" width="4" height="16" />
                </svg>
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="ml-1">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
              )}
            </button>

            {/* Progress & Animated Waveform */}
            <div className="flex-1 w-full space-y-2">
              <div className="flex items-center justify-between text-xs text-[#63524C] font-bold">
                <span>{isPlaying ? "01:18" : "00:00"}</span>
                <span>05:12</span>
              </div>

              {/* Simulated Waveform Visualizer */}
              <div className="h-6 flex items-center gap-1 overflow-hidden">
                {[12, 18, 24, 15, 8, 20, 26, 14, 10, 22, 18, 12, 16, 24, 20, 14, 28, 16, 10, 22, 18, 14, 26, 20].map((h, i) => (
                  <span
                    key={i}
                    className={`flex-1 rounded-full transition-all duration-300 ${
                      i < 8
                        ? "bg-[#D4211C]"
                        : "bg-[#E2A63A]/50"
                    }`}
                    style={{
                      height: isPlaying ? `${Math.max(6, (h * (1 + Math.sin(i))) % 28)}px` : `${h}px`,
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Speed Toggle */}
            <button
              onClick={() => setPlaybackRate(playbackRate === "1x" ? "1.5x" : "1x")}
              className="px-3 py-1.5 rounded-full bg-[#FAF4E4] border border-[#E2A63A] text-xs font-bold text-[#1A1210] hover:bg-[#E2A63A]/20 transition-colors shrink-0"
            >
              {playbackRate} Speed
            </button>
          </div>

          {/* Synced Transcript */}
          <div className="p-4 rounded-xl bg-[#FAF4E4] border border-[#E2A63A]/30 text-xs text-[#54423C] space-y-1">
            <p className="font-bold text-[#8C5D0D] uppercase tracking-wider mb-1">
              Live Synced Transcript:
            </p>
            <p className="leading-relaxed font-sans">
              &ldquo;{audioBrief.transcript}&rdquo;
            </p>
          </div>
        </DoubleGoldCard>
      )}

      {/* Citation Inspector Modal */}
      <SourceModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
