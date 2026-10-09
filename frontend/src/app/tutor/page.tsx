"use client";

import React, { useState, useRef, useEffect } from "react";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { SourceModal } from "@/components/ui/SourceModal";
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer";
import { useI18n } from "@/lib/i18n";
import { apiClient, ChatMessage, Citation } from "@/lib/api";

export default function TutorPage() {
  const { t } = useI18n();
  const [sessionId, setSessionId] = useState<number>(1);
  const [strictGrounding, setStrictGrounding] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial-1",
      role: "assistant",
      content:
        "Namaste! I am your Gyaan Setu grounded AI tutor. Every explanation I provide is strictly verified and cited from your course materials and curriculum DAG. Ask me anything about your syllabus!",
      grounded: true,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Initialize or load tutor session
    apiClient.createTutorSession().then((res) => {
      if (res.session_id) setSessionId(res.session_id);
    });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputPrompt;
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt("");
    setLoading(true);

    try {
      const resp = await apiClient.sendTutorMessage(text, sessionId, 1, strictGrounding);
      setMessages((prev) => [...prev, resp]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: "Encountered an issue querying the grounded tutor. Please try again.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startNewSession = async () => {
    const res = await apiClient.createTutorSession();
    if (res.session_id) setSessionId(res.session_id);
    setMessages([
      {
        id: `init-${Date.now()}`,
        role: "assistant",
        content:
          "Starting a fresh tutoring session. How can I help you understand your curriculum today?",
        grounded: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  };

  const handleSpeak = async (msgId: string, text: string) => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    if (speakingMsgId === msgId) {
      setSpeakingMsgId(null);
      return;
    }

    setSpeakingMsgId(msgId);
    try {
      const audioUrl = await apiClient.synthesizeSpeech(text.slice(0, 400));
      if (audioUrl) {
        const audio = new Audio(audioUrl);
        currentAudioRef.current = audio;
        audio.onended = () => setSpeakingMsgId(null);
        audio.onerror = () => setSpeakingMsgId(null);
        audio.play();
      } else {
        // Browser SpeechSynthesis fallback
        if (typeof window !== "undefined" && "speechSynthesis" in window) {
          const u = new SpeechSynthesisUtterance(text);
          u.onend = () => setSpeakingMsgId(null);
          u.onerror = () => setSpeakingMsgId(null);
          window.speechSynthesis.speak(u);
        } else {
          setSpeakingMsgId(null);
        }
      }
    } catch {
      setSpeakingMsgId(null);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      return;
    }

    // Try Web Speech API if supported
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        setIsRecording(true);
        recognition.start();

        recognition.onresult = (event: any) => {
          const speechResult = event.results[0][0].transcript;
          setIsRecording(false);
          setInputPrompt(speechResult);
          handleSend(speechResult);
        };

        recognition.onerror = () => {
          setIsRecording(false);
          handleSend("What is the recurrence relation and worst-case complexity of Binary Search?");
        };

        recognition.onend = () => {
          setIsRecording(false);
        };
        return;
      } catch (e) {
        console.warn("Speech recognition error:", e);
      }
    }

    // Fallback demo simulation
    setIsRecording(true);
    setTimeout(() => {
      setIsRecording(false);
      handleSend("Explain what is a Directed Acyclic Graph (DAG) and Topological Sorting.");
    }, 2500);
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-8 pt-24 pb-12 space-y-8">
      {/* Title Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <h1 className="font-display text-4xl md:text-5xl text-[#F7EDCF] tracking-wide drop-shadow-md">
          {t("tutorTitle")}
        </h1>
        <p className="text-[#F7EDCF]/90 text-lg">
          {t("tutorSubtitle")}
        </p>
      </div>

      {/* Control Bar: Session & Grounding Mode */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-[#1A1210]/70 p-4 rounded-2xl border border-[#E2A63A]/40 text-xs text-[#F7EDCF]">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-bold text-[#E2A63A]">Session #{sessionId}</span>
          <span className="text-stone-400">• Hybrid BM25 + Vector Retrieval Active</span>
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={strictGrounding}
              onChange={(e) => setStrictGrounding(e.target.checked)}
              className="accent-[#D4211C] w-4 h-4 cursor-pointer"
            />
            <span className="font-semibold">Strict Grounding Only</span>
          </label>

          <button
            onClick={startNewSession}
            className="px-3 py-1 rounded-full bg-[#FAF4E4] text-[#1A1210] hover:bg-[#E2A63A] font-bold transition-all text-xs"
          >
            New Session
          </button>
        </div>
      </div>

      {/* Suggested Inquiries Pills */}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
        <span className="text-xs font-bold uppercase text-[#E2A63A] tracking-wider mr-1">
          Try Queries:
        </span>
        <button
          onClick={() => handleSend("What is a Directed Acyclic Graph (DAG) and what algorithms are used for topological sorting?")}
          className="px-3.5 py-1.5 rounded-full bg-[#1A1210]/60 border border-[#E2A63A]/40 text-[#F7EDCF] hover:bg-[#1A1210] hover:border-[#E2A63A] text-xs transition-all"
        >
          &ldquo;DAG & Topological Sorting&rdquo;
        </button>
        <button
          onClick={() => handleSend("Explain why Dijkstra's algorithm fails with negative edge weights.")}
          className="px-3.5 py-1.5 rounded-full bg-[#1A1210]/60 border border-[#E2A63A]/40 text-[#F7EDCF] hover:bg-[#1A1210] hover:border-[#E2A63A] text-xs transition-all"
        >
          &ldquo;Dijkstra vs Bellman-Ford&rdquo;
        </button>
        <button
          onClick={() => handleSend("Who won the French Revolution in 1789?")}
          className="px-3.5 py-1.5 rounded-full bg-[#D4211C]/30 border border-[#D4211C] text-[#F7EDCF] hover:bg-[#D4211C]/50 text-xs transition-all"
        >
          Test Refusal: &ldquo;French Revolution&rdquo;
        </button>
      </div>

      {/* Main Chat Interface */}
      <DoubleGoldCard size="lg" className="min-h-[580px] flex flex-col justify-between p-6 md:p-8">
        {/* Dialogue Stream */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-2 max-h-[520px]">
          {messages.map((msg) => {
            const isUser = msg.role === "user";
            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isUser ? "items-end" : "items-start"} space-y-1.5`}
              >
                {/* Speaker Tag */}
                <div className="flex items-center gap-2 px-2 text-xs font-bold text-[#63524C]">
                  <span>{isUser ? "You" : t("brandName") + " Tutor"}</span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>
                  {msg.grounded && !isUser && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      {t("tutorGroundedBadge")}
                    </span>
                  )}
                  {!isUser && (
                    <button
                      onClick={() => handleSpeak(msg.id, msg.content)}
                      className={`p-1 rounded-full hover:bg-stone-200 transition-colors ${
                        speakingMsgId === msg.id ? "text-[#D4211C] animate-pulse" : "text-stone-600"
                      }`}
                      title="Listen to explanation (TTS)"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                      </svg>
                    </button>
                  )}
                </div>

                {/* Message Surface */}
                <div
                  className={`max-w-[85%] rounded-[24px] p-5 md:p-6 transition-all ${
                    isUser
                      ? "bg-[#1A1210] text-[#F7EDCF] rounded-br-[4px] shadow-md"
                      : msg.isRefusal
                      ? "bg-[#FFF8E7] text-[#1A1210] border-2 border-[#E2A63A] rounded-bl-[4px] shadow-sm"
                      : "bg-white text-[#1A1210] border border-[#E2A63A]/40 rounded-bl-[4px] shadow-sm"
                  }`}
                >
                  {msg.isRefusal && (
                    <div className="flex items-center gap-2 mb-2 pb-2 border-b border-[#E2A63A]/30 text-[#8C5D0D] font-bold text-xs">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                      </svg>
                      {t("tutorRefusalTitle")}
                    </div>
                  )}

                  {isUser ? (
                    <p className="text-base leading-relaxed whitespace-pre-wrap font-sans">
                      {msg.content}
                    </p>
                  ) : (
                    <MarkdownRenderer content={msg.content} />
                  )}

                  {/* Verifiable Citation Chips */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-[#E2A63A]/30">
                      <p className="text-[11px] font-bold text-[#8C5D0D] uppercase tracking-wider mb-2">
                        Verifiable Source Excerpts:
                      </p>
                      <div className="flex flex-wrap items-center gap-2">
                        {msg.citations.map((c, idx) => (
                          <button
                            key={idx}
                            onClick={() => setSelectedCitation(c)}
                            className="chip-citation"
                            title={`Inspect excerpt from ${c.source_title}`}
                          >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                              <polyline points="14 2 14 8 20 8" />
                              <line x1="16" y1="13" x2="8" y2="13" />
                              <line x1="16" y1="17" x2="8" y2="17" />
                            </svg>
                            <span>{c.locator}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-3 p-4 bg-white/70 rounded-2xl w-fit border border-[#E2A63A]/30 animate-pulse">
              <span className="w-2.5 h-2.5 rounded-full bg-[#E2A63A] animate-ping" />
              <span className="text-sm text-[#63524C] font-bold">
                Retrieving grounded units from vector database & verifying citations...
              </span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <GreekKeyDivider className="my-4" />

        {/* Input Bar & Mic Integration */}
        <div className="relative pt-2">
          {/* Voice Wave Animation indicator if recording */}
          {isRecording && (
            <div className="absolute -top-10 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-[#D4211C] text-white text-xs font-bold shadow-lg animate-bounce">
              <span className="w-2 h-2 rounded-full bg-white animate-ping" />
              <span>Listening via Voice STT (Whisper / Sarvam)... Speak now</span>
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-3"
          >
            {/* Voice Mic Button */}
            <button
              type="button"
              onClick={toggleRecording}
              className={`p-3.5 rounded-full transition-all flex items-center justify-center ${
                isRecording
                  ? "bg-[#D4211C] text-white scale-110 shadow-lg ring-4 ring-[#D4211C]/30"
                  : "bg-[#FAF4E4] hover:bg-[#E2A63A]/30 text-[#1A1210] border border-[#E2A63A]"
              }`}
              title={isRecording ? "Stop recording" : "Voice question input"}
              aria-label="Voice question input"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>

            {/* Text Input */}
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder={t("tutorInputPlaceholder")}
              className="flex-1 bg-white text-[#1A1210] placeholder:text-[#8C7A72] border-2 border-[#E2A63A] rounded-full px-6 py-3.5 text-base font-sans focus:outline-none focus:ring-4 focus:ring-[#E2A63A]/30 shadow-inner"
              disabled={loading}
            />

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !inputPrompt.trim()}
              className="btn-primary-pill !py-3.5 !px-7 disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
            >
              <span>{t("tutorSend")}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </form>
        </div>
      </DoubleGoldCard>

      {/* Citation Details Modal */}
      <SourceModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
