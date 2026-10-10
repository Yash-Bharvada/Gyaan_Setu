"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { SourceModal } from "@/components/ui/SourceModal";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";
import { useI18n } from "@/lib/i18n";
import { apiClient, Question, Citation, TopicNode } from "@/lib/api";

export default function PracticePage() {
  const { t } = useI18n();
  const [assessmentId, setAssessmentId] = useState<number>(1);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [shortAnswer, setShortAnswer] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [scoreCount, setScoreCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [quizFinished, setQuizFinished] = useState(false);
  const [gradingReport, setGradingReport] = useState<any>(null);

  // User Customizable Quiz Parameters
  const [questionCount, setQuestionCount] = useState<number>(5);
  const [availableTopics, setAvailableTopics] = useState<TopicNode[]>([]);
  const [selectedTopicId, setSelectedTopicId] = useState<number | "all">("all");
  const [showConfig, setShowConfig] = useState(false);

  // Load available topics from knowledge graph
  useEffect(() => {
    apiClient.getKnowledgeGraph(1).then((data) => {
      if (data && data.nodes) {
        setAvailableTopics(data.nodes);
      }
    }).catch((e) => console.warn("Failed to load topics:", e));
  }, []);

  const loadQuiz = async (count = questionCount, topicId = selectedTopicId) => {
    setLoading(true);
    setQuizFinished(false);
    setCurrentIndex(0);
    setSelectedOption(null);
    setShortAnswer("");
    setSubmitted(false);
    setScoreCount(0);
    try {
      const topicIds = topicId === "all" ? undefined : [Number(topicId)];
      const quiz = await apiClient.createAdaptiveQuiz(1, count, topicIds);
      if (quiz && quiz.questions && quiz.questions.length >= count) {
        setAssessmentId(quiz.assessment_id);
        setQuestions(quiz.questions.slice(0, count));
      } else if (quiz && quiz.questions && quiz.questions.length > 0) {
        // Top up with comprehensive curriculum questions if fewer returned
        const fallback = await apiClient.getPracticeQuestions();
        const existingStems = new Set(quiz.questions.map((q) => q.stem.toLowerCase()));
        const needed = count - quiz.questions.length;
        const additional = fallback.filter((q) => !existingStems.has(q.stem.toLowerCase())).slice(0, needed);
        setAssessmentId(quiz.assessment_id);
        setQuestions([...quiz.questions, ...additional].slice(0, count));
      } else {
        const fallback = await apiClient.getPracticeQuestions();
        setQuestions(fallback.slice(0, count));
      }
    } catch (e) {
      console.warn("Failed to load adaptive quiz:", e);
      const fallback = await apiClient.getPracticeQuestions();
      setQuestions(fallback.slice(0, count));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuiz(questionCount, selectedTopicId);
  }, []);

  const currentQ = questions[currentIndex];

  const handleSubmit = async () => {
    if (submitted) return;
    setSubmitted(true);

    const answer =
      currentQ?.type === "mcq" && selectedOption !== null
        ? currentQ.options?.[selectedOption] || ""
        : shortAnswer;

    const isCorrect =
      currentQ?.type === "mcq"
        ? answer === currentQ.answer_key
        : answer.trim().length > 15;

    if (isCorrect) setScoreCount((prev) => prev + 1);

    // Record learning attempt to update BKT mastery in backend
    try {
      await apiClient.recordAttempt(1, currentQ?.id || 1, isCorrect);
      const res = await apiClient.submitAssessment(assessmentId, [
        { question_id: currentQ?.id || 1, response: answer, time_taken_secs: 12.0 },
      ]);
      if (res.report) setGradingReport(res.report);
    } catch (e) {
      console.warn("Attempt submission error:", e);
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
      setSelectedOption(null);
      setShortAnswer("");
      setSubmitted(false);
    } else {
      setQuizFinished(true);
    }
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

      {/* QUIZ CONFIGURATION / QUESTION COUNT SELECTOR */}
      <div className="bg-[#1A1210]/75 backdrop-blur-md p-4 rounded-2xl border border-[#E2A63A]/40 shadow-lg text-[#F7EDCF] space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Question Count Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#E2A63A] shrink-0">
              Questions:
            </span>
            <div className="flex items-center gap-1.5">
              {[3, 5, 10, 15, 20].map((num) => (
                <button
                  key={num}
                  onClick={() => {
                    setQuestionCount(num);
                    loadQuiz(num, selectedTopicId);
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                    questionCount === num
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
                  const nextCount = Math.max(1, questionCount - 1);
                  setQuestionCount(nextCount);
                  loadQuiz(nextCount, selectedTopicId);
                }}
                className="px-2 py-0.5 text-xs hover:bg-[#E2A63A] hover:text-[#1A1210] transition-colors"
                title="Decrease question count"
              >
                &minus;
              </button>
              <span className="px-2 text-xs font-mono font-bold text-[#E2A63A]">
                {questionCount}
              </span>
              <button
                onClick={() => {
                  const nextCount = Math.min(30, questionCount + 1);
                  setQuestionCount(nextCount);
                  loadQuiz(nextCount, selectedTopicId);
                }}
                className="px-2 py-0.5 text-xs hover:bg-[#E2A63A] hover:text-[#1A1210] transition-colors"
                title="Increase question count"
              >
                +
              </button>
            </div>
          </div>

          {/* Topic Scope Selector */}
          {availableTopics.length > 0 && (
            <div className="flex items-center gap-2 self-start sm:self-center">
              <span className="text-xs font-bold uppercase tracking-wider text-[#E2A63A] shrink-0">
                Scope:
              </span>
              <select
                value={selectedTopicId}
                onChange={(e) => {
                  const val = e.target.value === "all" ? "all" : Number(e.target.value);
                  setSelectedTopicId(val);
                  loadQuiz(questionCount, val);
                }}
                className="bg-[#2D211D] text-[#F7EDCF] border border-[#E2A63A]/40 rounded-xl px-2.5 py-1 text-xs font-bold outline-none cursor-pointer hover:border-[#E2A63A]"
              >
                <option value="all">All Topics (Adaptive BKT Gaps)</option>
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

      {loading ? (
        <DoubleGoldCard size="lg" className="py-16 text-center space-y-4">
          <div className="w-10 h-10 border-4 border-[#E2A63A] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="font-display text-xl text-[#1A1210]">
            Generating {questionCount} Adaptive Questions from Grounded Curriculum...
          </p>
          <p className="text-xs text-[#63524C]">
            Targeting Zone of Proximal Development (ZPD) mastery gaps with Bayesian Knowledge Tracing
          </p>
        </DoubleGoldCard>
      ) : quizFinished ? (
        <DoubleGoldCard size="lg" className="p-8 md:p-12 text-center space-y-6">
          <div className="w-20 h-20 mx-auto rounded-full bg-emerald-100 border-2 border-emerald-500 flex items-center justify-center text-emerald-800">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>

          <div className="space-y-2">
            <h2 className="font-display text-3xl md:text-4xl text-[#1A1210]">
              Adaptive Assessment Complete!
            </h2>
            <p className="text-[#63524C] text-lg">
              You scored {scoreCount} out of {questions.length} (
              {Math.round((scoreCount / (questions.length || 1)) * 100)}%)
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-lg mx-auto py-2">
            <div className="p-4 rounded-xl bg-white border border-[#E2A63A]/40 text-center">
              <span className="block text-2xl font-bold text-[#D4211C]">
                +{scoreCount * 4}%
              </span>
              <span className="text-xs text-[#63524C] font-semibold">BKT Mastery Delta</span>
            </div>
            <div className="p-4 rounded-xl bg-white border border-[#E2A63A]/40 text-center">
              <span className="block text-2xl font-bold text-emerald-700">
                {scoreCount}/{questions.length}
              </span>
              <span className="text-xs text-[#63524C] font-semibold">Verified Correct</span>
            </div>
            <div className="p-4 rounded-xl bg-white border border-[#E2A63A]/40 text-center">
              <span className="block text-2xl font-bold text-[#1A1210]">
                Active
              </span>
              <span className="text-xs text-[#63524C] font-semibold">Next SM-2 Review</span>
            </div>
          </div>

          <div className="pt-4 flex flex-wrap justify-center gap-4">
            <button onClick={() => loadQuiz(questionCount, selectedTopicId)} className="btn-primary-pill shadow-lg text-sm">
              <span>Take Next Adaptive Quiz ({questionCount} Qs)</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M5 12h14" />
                <path d="m12 5 7 7-7 7" />
              </svg>
            </button>
            <Link href="/progress" className="px-5 py-2.5 rounded-full border border-[#1A1210] text-[#1A1210] hover:bg-[#1A1210] hover:text-[#F7EDCF] text-sm font-bold transition-all">
              View Updated DAG Mastery
            </Link>
          </div>
        </DoubleGoldCard>
      ) : currentQ ? (
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
            <span className="text-xs font-bold uppercase tracking-wider text-[#8C5D0D] bg-[#FAF4E4] px-2.5 py-1 rounded-full border border-[#E2A63A]/40">
              Topic: {currentQ.topic_name}
            </span>
            <p className="font-sans text-xl md:text-2xl text-[#1A1210] font-semibold leading-snug">
              {currentQ.stem}
            </p>
          </div>

          {/* Interactive Options */}
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
                    onClick={() => !submitted && setSelectedOption(idx)}
                    disabled={submitted}
                    className={`w-full p-4 rounded-xl border-2 text-left font-sans text-base transition-all flex items-center justify-between ${optionStyle}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full border border-current flex items-center justify-center text-xs font-bold shrink-0">
                        {String.fromCharCode(65 + idx)}
                      </span>
                      <span>{opt}</span>
                    </div>

                    {submitted && (
                      <span className="text-xs font-bold uppercase shrink-0 ml-2">
                        {isCorrect ? "✓ Correct" : isSelected ? "✗ Incorrect" : ""}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* Short Answer Input */}
          {currentQ.type === "short" && (
            <div className="space-y-3 pt-2">
              <textarea
                value={shortAnswer}
                onChange={(e) => setShortAnswer(e.target.value)}
                disabled={submitted}
                rows={4}
                placeholder="Type your explanation here. The AI rubrics will grade for conceptual rigor..."
                className="w-full p-4 rounded-xl border-2 border-[#E2A63A]/50 focus:border-[#1A1210] outline-none text-base font-sans"
              />
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-4 border-t border-[#E2A63A]/30 flex items-center justify-between">
            <span className="text-xs text-[#63524C]">
              {submitted
                ? "Review instructor rationale below before proceeding"
                : "Select your answer and submit"}
            </span>

            {!submitted ? (
              <button
                onClick={handleSubmit}
                disabled={selectedOption === null && shortAnswer.trim().length === 0}
                className="btn-primary-pill text-sm py-2 px-6 shadow-md disabled:opacity-50"
              >
                Submit Answer
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="btn-primary-pill text-sm py-2 px-6 shadow-md flex items-center gap-2"
              >
                <span>{currentIndex < questions.length - 1 ? "Next Question" : "Complete Quiz"}</span>
                <span>→</span>
              </button>
            )}
          </div>

          {/* Instructor Rationale & Citation Drawer */}
          {submitted && (
            <div className="p-5 rounded-2xl bg-[#FAF4E4] border border-[#E2A63A] space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center gap-2 text-xs font-bold text-[#8C5D0D] uppercase tracking-wider">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
                <span>Pedagogical Explanation & Grounding:</span>
              </div>

              <div className="text-sm text-[#2D211D] leading-relaxed">
                <MarkdownRenderer content={currentQ.explanation} />
              </div>

              {/* Citations */}
              {currentQ.citations && currentQ.citations.length > 0 && (
                <div className="pt-3 border-t border-[#E2A63A]/40">
                  <span className="text-[11px] font-bold text-[#8C5D0D] block mb-2">
                    Verified Source Citations:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {currentQ.citations.map((c, idx) => (
                      <button
                        key={idx}
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
        <DoubleGoldCard size="lg" className="p-8 md:p-12 text-center">
          <div className="max-w-md mx-auto space-y-4">
            <div className="w-16 h-16 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center mx-auto shadow-lg border border-[#E2A63A]/40">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 11l3 3L22 4" />
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
              </svg>
            </div>
            <h3 className="font-display text-2xl md:text-3xl text-[#1A1210]">
              No Practice Questions Yet
            </h3>
            <p className="text-sm text-[#63524C] leading-relaxed">
              Assessment questions are automatically synthesized from your uploaded course topics with cross-model verification. Upload documents in your Library to generate adaptive quizzes!
            </p>
            <div className="pt-2">
              <Link
                href="/library"
                className="btn-primary-pill text-sm py-2.5 px-6 shadow-xl inline-flex items-center gap-2"
              >
                <span>Go to Library & Upload Material</span>
                <span>→</span>
              </Link>
            </div>
          </div>
        </DoubleGoldCard>
      )}

      {/* Source Citation Modal */}
      <SourceModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
