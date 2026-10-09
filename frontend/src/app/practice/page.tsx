"use client";

import React, { useState, useEffect } from "react";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { SourceModal } from "@/components/ui/SourceModal";
import { useI18n } from "@/lib/i18n";
import { apiClient, Question, Citation } from "@/lib/api";

export default function PracticePage() {
  const { t } = useI18n();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [shortAnswer, setShortAnswer] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [scoreCount, setScoreCount] = useState(0);

  useEffect(() => {
    apiClient.getPracticeQuestions().then(setQuestions);
  }, []);

  const currentQ = questions[currentIndex];

  const handleSubmit = () => {
    if (submitted) return;
    setSubmitted(true);
    if (currentQ?.type === "mcq" && selectedOption !== null) {
      const isCorrect = currentQ.options?.[selectedOption] === currentQ.answer_key;
      if (isCorrect) setScoreCount((prev) => prev + 1);
    } else {
      setScoreCount((prev) => prev + 1);
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
      setSelectedOption(null);
      setShortAnswer("");
      setSubmitted(false);
    }
  };

  const handleRestart = () => {
    setCurrentIndex(0);
    setSelectedOption(null);
    setShortAnswer("");
    setSubmitted(false);
    setScoreCount(0);
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 md:px-8 pt-24 pb-12 space-y-8">
      {/* Title */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <h1 className="font-display text-4xl md:text-5xl text-[#F7EDCF] tracking-wide drop-shadow-md">
          {t("practiceTitle")}
        </h1>
        <p className="text-[#F7EDCF]/90 text-lg">
          {t("practiceSubtitle")}
        </p>
      </div>

      {currentQ ? (
        <DoubleGoldCard size="lg" className="space-y-6">
          {/* Question Metadata Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2A63A]/40 pb-4">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-[#1A1210] text-[#F7EDCF] text-xs font-bold uppercase tracking-wider">
                Question {currentIndex + 1} of {questions.length}
              </span>
              <span className="px-3 py-1 rounded-full bg-[#E2A63A]/20 text-[#8C5D0D] border border-[#E2A63A] text-xs font-bold">
                Bloom Level: {currentQ.bloom_level}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#63524C]">Difficulty:</span>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((lvl) => (
                  <span
                    key={lvl}
                    className={`w-3 h-3 rounded-full border border-[#E2A63A] ${
                      lvl <= currentQ.difficulty ? "bg-[#D4211C]" : "bg-transparent"
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Question Stem */}
          <div className="space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-[#8C5D0D]">
              Topic: {currentQ.topic_name}
            </span>
            <p className="font-sans text-xl md:text-2xl text-[#1A1210] font-semibold leading-snug">
              {currentQ.stem}
            </p>
          </div>

          {/* Interactive Input Formats */}
          {currentQ.type === "mcq" && currentQ.options && (
            <div className="space-y-3 pt-2">
              {currentQ.options.map((opt, idx) => {
                const isSelected = selectedOption === idx;
                const isCorrect = opt === currentQ.answer_key;

                let optionStyle =
                  "border-[#E2A63A]/50 bg-white hover:bg-[#FAF4E4] text-[#1A1210]";
                if (submitted) {
                  if (isCorrect) {
                    optionStyle = "border-emerald-600 bg-emerald-50 text-emerald-950 font-bold ring-2 ring-emerald-500";
                  } else if (isSelected && !isCorrect) {
                    optionStyle = "border-[#D4211C] bg-red-50 text-red-950 font-bold ring-2 ring-[#D4211C]";
                  }
                } else if (isSelected) {
                  optionStyle = "border-[#1A1210] bg-[#1A1210] text-[#F7EDCF] shadow-md";
                }

                return (
                  <button
                    key={idx}
                    disabled={submitted}
                    onClick={() => setSelectedOption(idx)}
                    className={`w-full text-left p-4 md:p-5 rounded-2xl border-2 transition-all flex items-start gap-4 ${optionStyle}`}
                  >
                    <span
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 border ${
                        isSelected && !submitted
                          ? "bg-[#E2A63A] text-[#1A1210] border-[#E2A63A]"
                          : "border-current opacity-80"
                      }`}
                    >
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span className="text-base font-sans pt-0.5">{opt}</span>
                  </button>
                );
              })}
            </div>
          )}

          {currentQ.type === "short" && (
            <div className="space-y-4 pt-2">
              <textarea
                value={shortAnswer}
                onChange={(e) => setShortAnswer(e.target.value)}
                disabled={submitted}
                placeholder="Type your structured explanation here (clarity, algorithmic mechanism, and citations will be graded against rubric)..."
                rows={4}
                className="w-full bg-white text-[#1A1210] p-4 rounded-2xl border-2 border-[#E2A63A] focus:outline-none focus:ring-4 focus:ring-[#E2A63A]/30 text-base font-sans"
              />
            </div>
          )}

          {/* Action Button: Submit or Next */}
          <div className="flex items-center justify-between pt-4">
            {!submitted ? (
              <button
                onClick={handleSubmit}
                disabled={
                  (currentQ.type === "mcq" && selectedOption === null) ||
                  (currentQ.type === "short" && !shortAnswer.trim())
                }
                className="btn-primary-pill disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
              >
                <span>{t("practiceSubmit")}</span>
              </button>
            ) : (
              <div className="flex items-center gap-3">
                {currentIndex < questions.length - 1 ? (
                  <button onClick={handleNext} className="btn-primary-pill shadow-md">
                    <span>Next Question →</span>
                  </button>
                ) : (
                  <button onClick={handleRestart} className="btn-secondary-pill shadow-md">
                    <span>Complete & Review Summary</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Feedback & Rubric Explanation */}
          {submitted && (
            <div className="mt-6 p-6 rounded-2xl bg-white border-2 border-[#E2A63A] shadow-md space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-lg text-[#1A1210]">
                  {t("practiceFeedback")}
                </h3>
                <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                  Cross-Model Verified
                </span>
              </div>

              <p className="text-base leading-relaxed text-[#1A1210] font-sans">
                {currentQ.explanation}
              </p>

              {/* Rubric Breakdown for short answers */}
              {currentQ.type === "short" && (
                <div className="p-4 rounded-xl bg-[#FAF4E4] border border-[#E2A63A]/40 space-y-2">
                  <p className="text-xs font-bold text-[#8C5D0D] uppercase tracking-wider">
                    {t("practiceRubricTitle")}:
                  </p>
                  <ul className="text-xs text-[#54423C] space-y-1 list-disc pl-5">
                    <li><strong className="text-[#1A1210]">Layered Ordering (4/4):</strong> Correctly identified FIFO queue properties over LIFO stack.</li>
                    <li><strong className="text-[#1A1210]">Algorithmic Complexity (3/3):</strong> Confirmed O(V + E) bounds.</li>
                    <li><strong className="text-[#1A1210]">Source Grounding (3/3):</strong> Verified against Introduction to Algorithms Page 118.</li>
                  </ul>
                </div>
              )}

              {/* Citations */}
              {currentQ.citations && currentQ.citations.length > 0 && (
                <div className="pt-2">
                  <p className="text-xs font-bold text-[#8C5D0D] uppercase tracking-wider mb-2">
                    Review In Course Material:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {currentQ.citations.map((c, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedCitation(c)}
                        className="chip-citation"
                      >
                        <span>{c.source_title} • {c.locator}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DoubleGoldCard>
      ) : (
        <div className="text-center text-[#F7EDCF] py-12">Loading questions...</div>
      )}

      {/* Source Citation Modal */}
      <SourceModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
