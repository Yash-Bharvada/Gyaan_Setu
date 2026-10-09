"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { SourceModal } from "@/components/ui/SourceModal";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";
import { useI18n } from "@/lib/i18n";
import { apiClient, Flashcard, Citation, AudioBrief, TopicNode } from "@/lib/api";

export default function RevisePage() {
  const { t } = useI18n();
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [audioBrief, setAudioBrief] = useState<AudioBrief | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioProgress, setAudioProgress] = useState(0); // seconds
  const [playbackRate, setPlaybackRate] = useState<"1x" | "1.25x" | "1.5x" | "2x">("1x");
  const [audioDuration, setAudioDuration] = useState<number>(120);
  const [isGenerating, setIsGenerating] = useState(false);
  const [reviewCount, setReviewCount] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Audio Synthesis Studio Options
  const [audioTopicId, setAudioTopicId] = useState<number>(1);
  const [audioMode, setAudioMode] = useState<"summary" | "podcast">("summary");
  const [audioLanguage, setAudioLanguage] = useState<"en" | "hi">("en");
  const [isAudioLoading, setIsAudioLoading] = useState(false);
  const [isSynthesizingVoice, setIsSynthesizingVoice] = useState(false);
  const [showFullTranscript, setShowFullTranscript] = useState(false);

  // User Customizable Flashcards Parameters
  const [cardLimit, setCardLimit] = useState<number>(10);
  const [availableTopics, setAvailableTopics] = useState<TopicNode[]>([]);
  const [selectedTopicId, setSelectedTopicId] = useState<number | "all">("all");
  const [loadingCards, setLoadingCards] = useState(false);

  const loadAudioBrief = async (
    topicId = audioTopicId,
    mode = audioMode,
    lang = audioLanguage
  ) => {
    setIsAudioLoading(true);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
      setAudioProgress(0);
    }
    try {
      const brief = await apiClient.getAudioBrief(topicId, mode, lang);
      setAudioBrief(brief);
      setAudioDuration(brief.duration_secs || (mode === "podcast" ? 150 : 120));
      setAudioProgress(0);
    } catch (e) {
      console.warn("loadAudioBrief failed:", e);
    } finally {
      setIsAudioLoading(false);
    }
  };

  // Load available topics and initial audio
  useEffect(() => {
    apiClient
      .getKnowledgeGraph(1)
      .then((data) => {
        if (data && data.nodes && data.nodes.length > 0) {
          setAvailableTopics(data.nodes);
          setAudioTopicId(data.nodes[0].id);
          loadAudioBrief(data.nodes[0].id, "summary", "en");
        }
      })
      .catch((e) => console.warn("Failed to load topics:", e));
  }, []);

  const loadData = async (limit = cardLimit) => {
    setLoadingCards(true);
    try {
      const cards = await apiClient.getFlashcards(1, limit);
      setFlashcards(cards);
      setCurrentIndex(0);
      setIsFlipped(false);
    } catch (e) {
      console.warn("loadData failed:", e);
    } finally {
      setLoadingCards(false);
    }
  };

  useEffect(() => {
    loadData(cardLimit);
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const currentCard = flashcards[currentIndex];

  const handleRating = async (quality: number) => {
    if (currentCard) {
      try {
        await apiClient.reviewFlashcard(currentCard.id, quality);
      } catch (e) {
        console.warn("reviewFlashcard error:", e);
      }
    }
    setReviewCount((prev) => prev + 1);
    setIsFlipped(false);
    setTimeout(() => {
      if (currentIndex < flashcards.length - 1) {
        setCurrentIndex((prev) => prev + 1);
      } else {
        setCurrentIndex(0);
      }
    }, 200);
  };

  const handleGenerateCards = async () => {
    setIsGenerating(true);
    try {
      const targetTopicId = selectedTopicId === "all" ? 1 : Number(selectedTopicId);
      const newCards = await apiClient.generateFlashcards(1, targetTopicId);
      if (newCards.length > 0) {
        await loadData(cardLimit);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleAudioPlayback = async () => {
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      return;
    }

    if (!audioBrief) return;

    if (!audioRef.current) {
      setIsSynthesizingVoice(true);
      try {
        let audioUrl = "";
        if (
          audioBrief.mode === "podcast" &&
          audioBrief.dialogue &&
          audioBrief.dialogue.length > 0
        ) {
          audioUrl = await apiClient.synthesizePodcast(
            audioBrief.dialogue,
            audioLanguage,
            "meera",
            "arvind"
          );
        } else {
          const textToSpeak =
            audioBrief.full_spoken_script ||
            audioBrief.transcript ||
            "Gyaan Setu revision audio brief.";
          audioUrl = await apiClient.synthesizeSpeech(
            textToSpeak.slice(0, 500),
            audioLanguage === "hi" ? "hi-IN" : "en-IN",
            "female",
            "meera"
          );
        }

        if (audioUrl) {
          const audio = new Audio(audioUrl);
          const rateVal = parseFloat(playbackRate.replace("x", "")) || 1.0;
          audio.playbackRate = rateVal;
          audio.ontimeupdate = () => {
            setAudioProgress(Math.floor(audio.currentTime));
            if (audio.duration && !isNaN(audio.duration) && audio.duration > 0) {
              setAudioDuration(Math.floor(audio.duration));
            }
          };
          audio.onended = () => {
            setIsPlaying(false);
            setAudioProgress(0);
          };
          audioRef.current = audio;
          await audio.play();
          setIsPlaying(true);
        }
      } catch (e) {
        console.warn("Audio playback synthesis error:", e);
      } finally {
        setIsSynthesizingVoice(false);
      }
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setAudioProgress(val);
    if (audioRef.current) {
      audioRef.current.currentTime = val;
    }
  };

  const handleSpeedChange = (speed: "1x" | "1.25x" | "1.5x" | "2x") => {
    setPlaybackRate(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = parseFloat(speed.replace("x", "")) || 1.0;
    }
  };

  const handleTopicChange = (newTopicId: number) => {
    setAudioTopicId(newTopicId);
    loadAudioBrief(newTopicId, audioMode, audioLanguage);
  };

  const handleModeChange = (newMode: "summary" | "podcast") => {
    setAudioMode(newMode);
    loadAudioBrief(audioTopicId, newMode, audioLanguage);
  };

  const handleLanguageChange = (newLang: "en" | "hi") => {
    setAudioLanguage(newLang);
    loadAudioBrief(audioTopicId, audioMode, newLang);
  };


  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-8 pt-24 pb-12 space-y-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="space-y-2 text-center md:text-left">
          <h1 className="font-display text-4xl md:text-5xl text-[#F7EDCF] tracking-wide drop-shadow-md">
            {t("reviseTitle")}
          </h1>
          <p className="text-[#F7EDCF]/90 text-lg">
            {t("reviseSubtitle")}
          </p>
        </div>

        <button
          onClick={handleGenerateCards}
          disabled={isGenerating}
          className="btn-primary-pill text-xs py-2 px-5 shadow-lg flex items-center gap-2"
        >
          {isGenerating ? (
            <>
              <span className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
              <span>Generating Cards...</span>
            </>
          ) : (
            <>
              <span>+ Generate Topic Flashcards</span>
            </>
          )}
        </button>
      </div>

      {/* FLASHCARD SESSION CONFIGURATION BAR (How Many Flashcards User Wants) */}
      <div className="bg-[#1A1210]/75 backdrop-blur-md p-4 rounded-2xl border border-[#E2A63A]/40 shadow-lg text-[#F7EDCF] space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Card Count Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#E2A63A] shrink-0">
              Session Cards:
            </span>
            <div className="flex items-center gap-1.5">
              {[5, 10, 15, 25].map((num) => (
                <button
                  key={num}
                  onClick={() => {
                    setCardLimit(num);
                    loadData(num);
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                    cardLimit === num
                      ? "bg-[#E2A63A] text-[#1A1210] shadow-md scale-105"
                      : "bg-[#2D211D] text-[#F7EDCF]/80 hover:bg-[#FAF4E4]/20 hover:text-white"
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>

            {/* Stepper controls */}
            <div className="flex items-center ml-2 border border-[#E2A63A]/40 rounded-lg overflow-hidden bg-[#2D211D]">
              <button
                onClick={() => {
                  const nextLimit = Math.max(1, cardLimit - 1);
                  setCardLimit(nextLimit);
                  loadData(nextLimit);
                }}
                className="px-2 py-0.5 text-xs hover:bg-[#E2A63A] hover:text-[#1A1210] transition-colors"
                title="Decrease card limit"
              >
                &minus;
              </button>
              <span className="px-2 text-xs font-mono font-bold text-[#E2A63A]">
                {cardLimit}
              </span>
              <button
                onClick={() => {
                  const nextLimit = Math.min(50, cardLimit + 1);
                  setCardLimit(nextLimit);
                  loadData(nextLimit);
                }}
                className="px-2 py-0.5 text-xs hover:bg-[#E2A63A] hover:text-[#1A1210] transition-colors"
                title="Increase card limit"
              >
                +
              </button>
            </div>
          </div>

          {/* Topic Scope Selector */}
          {availableTopics.length > 0 && (
            <div className="flex items-center gap-2 self-start sm:self-center">
              <span className="text-xs font-bold uppercase tracking-wider text-[#E2A63A] shrink-0">
                Topic Scope:
              </span>
              <select
                value={selectedTopicId}
                onChange={(e) => {
                  const val = e.target.value === "all" ? "all" : Number(e.target.value);
                  setSelectedTopicId(val);
                }}
                className="bg-[#2D211D] text-[#F7EDCF] border border-[#E2A63A]/40 rounded-xl px-2.5 py-1 text-xs font-bold outline-none cursor-pointer hover:border-[#E2A63A]"
              >
                <option value="all">All Topics (Full Queue)</option>
                {availableTopics.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name.length > 32 ? t.name.slice(0, 30) + "..." : t.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* FLASHCARD SECTION (Interactive 3D Flip) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold uppercase tracking-wider text-[#E2A63A]">
              Active Recall Flashcards (SM-2 Spaced Repetition)
            </span>
            {reviewCount > 0 && (
              <span className="text-xs bg-emerald-900/60 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-600 font-bold">
                {reviewCount} reviewed today
              </span>
            )}
          </div>
          {flashcards.length > 0 && (
            <span className="text-xs font-bold text-[#F7EDCF] bg-[#1A1210]/60 px-3 py-1 rounded-full border border-[#E2A63A]/40">
              Card {currentIndex + 1} of {flashcards.length}
            </span>
          )}
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
                    {isFlipped ? "Answer & Academic Citation" : "Prompt / Question"}
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
                      <div className="text-base md:text-lg font-sans text-[#1A1210] leading-relaxed">
                        <MarkdownRenderer content={currentCard.back} />
                      </div>

                      {currentCard.citation && (
                        <div className="pt-3 border-t border-[#E2A63A]/30 flex items-center gap-2">
                          <span className="text-xs font-bold text-[#8C5D0D]">Source Citation:</span>
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
                      )}
                    </div>
                  )}
                </div>

                {/* Card Bottom: SM-2 Spaced Repetition Buttons when flipped */}
                <div className="pt-3 border-t border-[#E2A63A]/30 flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs text-[#63524C]">
                    Interval: {currentCard.interval_days}d • Ease: {currentCard.ease_factor} • Reviews: {currentCard.reviewed_count}
                  </span>

                  {isFlipped ? (
                    <div
                      className="flex items-center gap-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => handleRating(1)}
                        className="px-3 py-1.5 rounded-full bg-red-100 hover:bg-red-200 text-red-900 text-xs font-bold border border-red-300 transition-colors"
                      >
                        {t("reviseRatingAgain")} (1)
                      </button>
                      <button
                        onClick={() => handleRating(2)}
                        className="px-3 py-1.5 rounded-full bg-amber-100 hover:bg-amber-200 text-amber-900 text-xs font-bold border border-amber-300 transition-colors"
                      >
                        {t("reviseRatingHard")} (2)
                      </button>
                      <button
                        onClick={() => handleRating(3)}
                        className="px-3 py-1.5 rounded-full bg-blue-100 hover:bg-blue-200 text-blue-900 text-xs font-bold border border-blue-300 transition-colors"
                      >
                        {t("reviseRatingGood")} (3)
                      </button>
                      <button
                        onClick={() => handleRating(5)}
                        className="px-3 py-1.5 rounded-full bg-emerald-100 hover:bg-emerald-200 text-emerald-900 text-xs font-bold border border-emerald-300 transition-colors"
                      >
                        {t("reviseRatingEasy")} (5)
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-[#8C5D0D] font-bold">
                      Click anywhere on card to flip
                    </span>
                  )}
                </div>
              </DoubleGoldCard>
            </div>
          </div>
        ) : (
          <DoubleGoldCard size="lg" className="p-8 md:p-12 text-center">
            <div className="max-w-md mx-auto space-y-4">
              <div className="w-16 h-16 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center mx-auto shadow-lg border border-[#E2A63A]/40">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect width="18" height="18" x="3" y="3" rx="2" />
                  <path d="m9 12 2 2 4-4" />
                </svg>
              </div>
              <h3 className="font-display text-2xl md:text-3xl text-[#1A1210]">
                No Flashcards in Queue
              </h3>
              <p className="text-sm text-[#63524C] leading-relaxed">
                Active recall flashcards use the SuperMemo SM-2 algorithm to reinforce your course concepts. Upload study materials in your Library to generate spaced repetition cards!
              </p>
              <div className="pt-2 flex flex-wrap justify-center gap-3">
                <button
                  onClick={handleGenerateCards}
                  disabled={isGenerating}
                  className="btn-primary-pill text-sm py-2.5 px-6 shadow-xl inline-flex items-center gap-2"
                >
                  <span>{isGenerating ? "Synthesizing Cards..." : "Generate Flashcards Now"}</span>
                  <span>+</span>
                </button>
              </div>
            </div>
          </DoubleGoldCard>
        )}
      </div>

      <GreekKeyDivider />

      {/* AUDITORY SYNTHESIS ENGINE & MULTI-VOICE PODCAST STUDIO */}
      {audioBrief && (
        <DoubleGoldCard size="lg" className="space-y-6">
          {/* Top Engine Header */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-[#E2A63A]/30 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#D4211C]">
                  Auditory Synthesis Engine
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#E2A63A]/15 text-[#8C5D0D] border border-[#E2A63A]/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  ElevenLabs Free Tier Neural Voice Engine
                </span>
              </div>
              <h3 className="font-display text-2xl md:text-3xl text-[#1A1210]">
                {audioBrief.title || t("reviseAudioBrief")}
              </h3>
              <p className="text-xs text-[#63524C]">
                {audioMode === "podcast"
                  ? audioLanguage === "hi"
                    ? "प्रिया और कबीर के साथ संवादात्मक ऑडियो पॉडकास्ट (ElevenLabs Free Tier वॉइस मॉडल)"
                    : "Interactive 2-Host AI Podcast with Priya & Kabir (ElevenLabs Free Tier Multilingual Voice)"
                  : audioLanguage === "hi"
                  ? "2-मिनट केंद्रित परीक्षा पूर्व रिवीजन सारांश (ElevenLabs Free Tier)"
                  : "High-yield 2-minute conceptual audio summary with real-world analogies (ElevenLabs Free Tier)"}
              </p>
            </div>

            {/* Quick Action: Regenerate */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => loadAudioBrief(audioTopicId, audioMode, audioLanguage)}
                disabled={isAudioLoading || isSynthesizingVoice}
                className="px-3 py-1.5 rounded-full border border-[#E2A63A] text-xs font-bold text-[#8C5D0D] hover:bg-[#FAF4E4] flex items-center gap-1.5 transition-colors disabled:opacity-50"
                title="Regenerate Script & Audio"
              >
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  className={isAudioLoading ? "animate-spin" : ""}
                >
                  <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
                </svg>
                <span>{isAudioLoading ? "Generating..." : "Regenerate"}</span>
              </button>
            </div>
          </div>

          {/* STUDIO CONTROLS: Topic, Format, Language */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 p-3.5 rounded-xl bg-[#FAF4E4]/70 border border-[#E2A63A]/30">
            {/* 1. Topic Scope Selector */}
            <div className="md:col-span-6 flex flex-col gap-1">
              <label className="text-[11px] font-bold uppercase tracking-wider text-[#8C5D0D] flex items-center justify-between">
                <span>Select Topic:</span>
                {availableTopics.length > 0 && (
                  <span className="text-[10px] text-stone-500 font-normal">
                    {availableTopics.findIndex((t) => t.id === audioTopicId) + 1} of {availableTopics.length}
                  </span>
                )}
              </label>
              <div className="flex items-center gap-1.5">
                {/* Prev Topic Button */}
                <button
                  onClick={() => {
                    const idx = availableTopics.findIndex((t) => t.id === audioTopicId);
                    if (idx > 0) {
                      handleTopicChange(availableTopics[idx - 1].id);
                    }
                  }}
                  disabled={availableTopics.findIndex((t) => t.id === audioTopicId) <= 0}
                  className="p-2 rounded-lg border border-[#E2A63A]/40 bg-white hover:bg-stone-50 disabled:opacity-30 disabled:pointer-events-none text-[#1A1210]"
                  title="Previous Topic"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="15 18 9 12 15 6" />
                  </svg>
                </button>

                <select
                  value={audioTopicId}
                  onChange={(e) => handleTopicChange(Number(e.target.value))}
                  className="flex-1 bg-white text-xs text-[#1A1210] font-medium rounded-lg px-2.5 py-2 border border-[#E2A63A]/40 focus:outline-none focus:ring-2 focus:ring-[#E2A63A]/50 shadow-sm"
                >
                  {availableTopics.map((top) => (
                    <option key={top.id} value={top.id}>
                      {top.name}
                    </option>
                  ))}
                </select>

                {/* Next Topic Button */}
                <button
                  onClick={() => {
                    const idx = availableTopics.findIndex((t) => t.id === audioTopicId);
                    if (idx >= 0 && idx < availableTopics.length - 1) {
                      handleTopicChange(availableTopics[idx + 1].id);
                    }
                  }}
                  disabled={
                    availableTopics.length === 0 ||
                    availableTopics.findIndex((t) => t.id === audioTopicId) >= availableTopics.length - 1
                  }
                  className="p-2 rounded-lg border border-[#E2A63A]/40 bg-white hover:bg-stone-50 disabled:opacity-30 disabled:pointer-events-none text-[#1A1210]"
                  title="Next Topic"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              </div>
            </div>

            {/* 2. Format Selector (Summary vs Podcast) */}
            <div className="md:col-span-3 flex flex-col gap-1">
              <label className="text-[11px] font-bold uppercase tracking-wider text-[#8C5D0D]">
                Audio Format:
              </label>
              <div className="grid grid-cols-2 gap-1 p-0.5 rounded-lg bg-stone-200/80 border border-[#E2A63A]/30">
                <button
                  onClick={() => handleModeChange("summary")}
                  className={`py-1.5 px-2 rounded-md text-xs font-bold transition-all text-center flex items-center justify-center gap-1 ${
                    audioMode === "summary"
                      ? "bg-[#1A1210] text-[#E2A63A] shadow-sm"
                      : "text-[#63524C] hover:text-[#1A1210]"
                  }`}
                >
                  <span>🎙️</span>
                  <span>Summary</span>
                </button>
                <button
                  onClick={() => handleModeChange("podcast")}
                  className={`py-1.5 px-2 rounded-md text-xs font-bold transition-all text-center flex items-center justify-center gap-1 ${
                    audioMode === "podcast"
                      ? "bg-[#1A1210] text-[#E2A63A] shadow-sm"
                      : "text-[#63524C] hover:text-[#1A1210]"
                  }`}
                >
                  <span>👥</span>
                  <span>Podcast</span>
                </button>
              </div>
            </div>

            {/* 3. Language Selector (Hindi vs English) */}
            <div className="md:col-span-3 flex flex-col gap-1">
              <label className="text-[11px] font-bold uppercase tracking-wider text-[#8C5D0D]">
                Language:
              </label>
              <div className="grid grid-cols-2 gap-1 p-0.5 rounded-lg bg-stone-200/80 border border-[#E2A63A]/30">
                <button
                  onClick={() => handleLanguageChange("en")}
                  className={`py-1.5 px-2 rounded-md text-xs font-bold transition-all text-center flex items-center justify-center gap-1 ${
                    audioLanguage === "en"
                      ? "bg-[#1A1210] text-[#E2A63A] shadow-sm"
                      : "text-[#63524C] hover:text-[#1A1210]"
                  }`}
                >
                  <span>🇬🇧</span>
                  <span>English</span>
                </button>
                <button
                  onClick={() => handleLanguageChange("hi")}
                  className={`py-1.5 px-2 rounded-md text-xs font-bold transition-all text-center flex items-center justify-center gap-1 ${
                    audioLanguage === "hi"
                      ? "bg-[#1A1210] text-[#E2A63A] shadow-sm"
                      : "text-[#63524C] hover:text-[#1A1210]"
                  }`}
                >
                  <span>🇮🇳</span>
                  <span>हिंदी</span>
                </button>
              </div>
            </div>
          </div>

          {/* DUAL VOICE BADGE INDICATOR (For Podcast Mode) */}
          {audioMode === "podcast" && (
            <div className="flex flex-wrap items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-[#FAF4E4] via-white to-[#FAF4E4] border border-[#E2A63A]/40 shadow-sm text-xs">
              <span className="font-bold text-[#8C5D0D] flex items-center gap-1 shrink-0">
                <span>🎙️ ElevenLabs Free Tier Personas:</span>
              </span>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-full bg-purple-100 text-purple-900 border border-purple-300 font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-purple-600" />
                  <span>Host 1: {audioLanguage === "hi" ? "प्रिया" : "Priya"} (ElevenLabs Sarah)</span>
                </span>
                <span className="px-2.5 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-600" />
                  <span>Host 2: {audioLanguage === "hi" ? "कबीर" : "Kabir"} (ElevenLabs George)</span>
                </span>
              </div>
            </div>
          )}

          {/* MAIN AUDIO PLAYER BAR */}
          <div className="p-4 sm:p-5 rounded-2xl bg-white border border-[#E2A63A]/50 shadow-md space-y-3">
            <div className="flex items-center gap-4">
              {/* Play / Pause / Synthesizing Button */}
              <button
                onClick={toggleAudioPlayback}
                disabled={isSynthesizingVoice || isAudioLoading}
                className="w-14 h-14 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center hover:scale-105 transition-all shadow-lg shrink-0 border-2 border-[#E2A63A]/50 disabled:opacity-60"
                title={isPlaying ? "Pause" : "Listen Now"}
              >
                {isSynthesizingVoice ? (
                  <div className="w-6 h-6 rounded-full border-2 border-[#E2A63A] border-t-transparent animate-spin" />
                ) : isPlaying ? (
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" />
                    <rect x="14" y="4" width="4" height="16" />
                  </svg>
                ) : (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" className="ml-1">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                )}
              </button>

              {/* Progress Slider and Timing */}
              <div className="flex-1 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono text-[#63524C]">
                  <span className="font-bold text-[#1A1210]">
                    {Math.floor(audioProgress / 60)}:{(audioProgress % 60).toString().padStart(2, "0")}
                  </span>
                  <span className="text-[11px] text-stone-500 italic">
                    {isSynthesizingVoice
                      ? audioMode === "podcast"
                        ? "Synthesizing multi-voice podcast with ElevenLabs Free Tier..."
                        : "Synthesizing speech with ElevenLabs Free Tier..."
                      : isPlaying
                      ? "Now Playing"
                      : "Ready"}
                  </span>
                  <span>
                    {Math.floor(audioDuration / 60)}:{(audioDuration % 60).toString().padStart(2, "0")}
                  </span>
                </div>

                {/* Scrub Slider */}
                <input
                  type="range"
                  min="0"
                  max={Math.max(audioDuration, 1)}
                  value={audioProgress}
                  onChange={handleSeek}
                  className="w-full h-2.5 bg-stone-200 rounded-lg appearance-none cursor-pointer accent-[#D4211C]"
                />
              </div>

              {/* Speed Pills */}
              <div className="hidden sm:flex items-center gap-1 shrink-0">
                {(["1x", "1.25x", "1.5x", "2x"] as const).map((spd) => (
                  <button
                    key={spd}
                    onClick={() => handleSpeedChange(spd)}
                    className={`px-2 py-1 rounded-md text-[11px] font-bold border transition-colors ${
                      playbackRate === spd
                        ? "bg-[#1A1210] text-[#E2A63A] border-[#E2A63A]"
                        : "bg-stone-50 text-stone-600 border-stone-200 hover:bg-stone-100"
                    }`}
                  >
                    {spd}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* PODCAST CONVERSATIONAL DIALOGUE STREAM */}
          {audioMode === "podcast" && audioBrief.dialogue && audioBrief.dialogue.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#8C5D0D] flex items-center gap-1.5">
                  <span>🎙️ Podcast Episode Conversation:</span>
                </h4>
                <span className="text-[11px] text-[#63524C]">
                  {audioBrief.dialogue.length} dialogue turns
                </span>
              </div>

              <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
                {audioBrief.dialogue.map((turn, idx) => {
                  const isHost1 =
                    turn.speaker === "host1" ||
                    turn.speaker_name.includes("प्रिया") ||
                    turn.speaker_name.includes("Priya");

                  return (
                    <div
                      key={idx}
                      className={`flex gap-3 p-3.5 rounded-xl border transition-all ${
                        isHost1
                          ? "bg-purple-50/50 border-purple-200 ml-0 mr-4"
                          : "bg-amber-50/50 border-amber-200 ml-4 mr-0"
                      }`}
                    >
                      {/* Host Avatar Icon */}
                      <div
                        className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs shrink-0 shadow-sm ${
                          isHost1
                            ? "bg-purple-700 text-purple-100"
                            : "bg-amber-600 text-amber-50"
                        }`}
                      >
                        {isHost1 ? "P" : "K"}
                      </div>

                      <div className="space-y-1 flex-1">
                        <div className="flex items-center justify-between">
                          <span
                            className={`text-xs font-bold ${
                              isHost1 ? "text-purple-900" : "text-amber-900"
                            }`}
                          >
                            {turn.speaker_name}
                          </span>
                          <span className="text-[10px] text-stone-400 font-mono">
                            Turn {idx + 1}
                          </span>
                        </div>
                        <p className="text-sm text-[#1A1210] leading-relaxed">
                          {turn.text}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* AUDIO SUMMARY QUADRANT CARDS (When in Summary Mode) */}
          {audioMode === "summary" && audioBrief.sections && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              {audioBrief.sections.intro && (
                <div className="p-3.5 rounded-xl bg-white border border-[#E2A63A]/30 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#D4211C] flex items-center gap-1">
                    <span>🎯</span>
                    <span>15s Hook & Context</span>
                  </div>
                  <p className="text-xs text-[#1A1210] leading-relaxed">
                    {audioBrief.sections.intro}
                  </p>
                </div>
              )}

              {audioBrief.sections.core_concepts && (
                <div className="p-3.5 rounded-xl bg-white border border-[#E2A63A]/30 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-[#8C5D0D] flex items-center gap-1">
                    <span>💡</span>
                    <span>Core Concepts & Analogy</span>
                  </div>
                  <p className="text-xs text-[#1A1210] leading-relaxed">
                    {audioBrief.sections.core_concepts}
                  </p>
                </div>
              )}

              {audioBrief.sections.rapid_check && (
                <div className="p-3.5 rounded-xl bg-white border border-[#E2A63A]/30 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-blue-700 flex items-center gap-1">
                    <span>❓</span>
                    <span>Rapid-Fire Recall Check</span>
                  </div>
                  <p className="text-xs text-[#1A1210] leading-relaxed font-medium">
                    {audioBrief.sections.rapid_check}
                  </p>
                </div>
              )}

              {audioBrief.sections.mnemonic_wrap && (
                <div className="p-3.5 rounded-xl bg-white border border-[#E2A63A]/30 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                    <span>🧠</span>
                    <span>Memory Peg & Takeaway</span>
                  </div>
                  <p className="text-xs text-[#1A1210] leading-relaxed">
                    {audioBrief.sections.mnemonic_wrap}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* COLLAPSIBLE COMPLETE SPOKEN SCRIPT */}
          <div className="pt-2 border-t border-[#E2A63A]/20">
            <button
              onClick={() => setShowFullTranscript(!showFullTranscript)}
              className="text-xs text-[#8C5D0D] font-bold flex items-center gap-1 hover:underline"
            >
              <span>{showFullTranscript ? "Hide Full Spoken Script" : "Show Full Spoken Script"}</span>
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                className={`transition-transform ${showFullTranscript ? "rotate-180" : ""}`}
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {showFullTranscript && (
              <div className="mt-2.5 p-3 rounded-xl bg-stone-50 border border-stone-200 text-xs text-[#63524C] leading-relaxed whitespace-pre-line font-serif italic">
                {audioBrief.full_spoken_script || audioBrief.transcript}
              </div>
            )}
          </div>
        </DoubleGoldCard>
      )}


      {/* Citation Modal */}
      <SourceModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
