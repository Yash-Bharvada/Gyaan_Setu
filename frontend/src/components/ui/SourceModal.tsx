"use client";

import React from "react";
import { Citation } from "@/lib/api";
import { GreekKeyDivider } from "./GreekKeyDivider";

interface SourceModalProps {
  citation: Citation | null;
  onClose: () => void;
}

function getYouTubeVideoId(url?: string): string | null {
  if (!url) return null;
  const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
  return match ? match[1] : null;
}

export const SourceModal: React.FC<SourceModalProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  const isVideo =
    citation.type === "timestamp" ||
    citation.ts_start !== undefined ||
    citation.locator.includes("⏱") ||
    citation.locator.includes(":");

  const videoId = getYouTubeVideoId(citation.jump_url || citation.video_url);
  const startSec = Math.floor(citation.ts_start || 0);

  const jumpUrl =
    citation.jump_url ||
    (videoId
      ? `https://www.youtube.com/watch?v=${videoId}&t=${startSec}s`
      : citation.video_url);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl bg-[#F7EDCF] text-[#1A1210] rounded-[24px] p-6 md:p-8 border-[3px] border-[#E2A63A] shadow-[0_20px_50px_rgba(0,0,0,0.6)] max-h-[90vh] overflow-y-auto"
        style={{
          boxShadow:
            "0 0 0 4px #F7EDCF, 0 0 0 7px #E2A63A, 0 25px 50px -12px rgba(0, 0, 0, 0.7)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-[#E2A63A]/40 pb-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className={`px-3 py-0.5 rounded-full text-white text-xs font-bold uppercase tracking-wider ${isVideo ? "bg-[#D4211C]" : "bg-[#D4211C]"}`}>
                {isVideo ? "🎥 Grounded Lecture Video" : "Verified Grounded Source"}
              </span>
              <span className="px-3 py-0.5 rounded-full bg-[#E2A63A]/20 text-[#8C5D0D] border border-[#E2A63A] text-xs font-bold flex items-center gap-1">
                {citation.locator}
              </span>
              {isVideo && citation.ts_start !== undefined && (
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-semibold border border-emerald-300">
                  Exact Audio Sync
                </span>
              )}
            </div>
            <h3 className="font-display text-2xl text-[#1A1210]">
              {citation.source_title}
            </h3>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-[#E2A63A]/20 text-[#1A1210] transition-colors shrink-0"
            aria-label="Close modal"
          >
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Video Player if YouTube */}
        {videoId && (
          <div className="mt-4 rounded-2xl overflow-hidden border-2 border-[#E2A63A] bg-black shadow-md">
            <div className="relative pt-[56.25%]">
              <iframe
                src={`https://www.youtube-nocookie.com/embed/${videoId}?start=${startSec}&autoplay=0`}
                title="Grounded Video Player"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="absolute inset-0 w-full h-full border-0"
              />
            </div>
          </div>
        )}

        {/* Content Body */}
        <div className="py-5 space-y-4">
          <div className="p-4 rounded-xl bg-white/85 border border-[#E2A63A]/40 shadow-inner">
            <div className="flex items-center justify-between gap-2 mb-2">
              <p className="text-xs font-bold text-[#8C5D0D] uppercase tracking-wider">
                {isVideo ? "Transcript at Timestamp" : "Extracted Grounded Excerpt"} ({citation.locator}):
              </p>
              {jumpUrl && (
                <a
                  href={jumpUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-bold text-[#D4211C] hover:underline"
                >
                  <span>Open Video at {citation.locator}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                </a>
              )}
            </div>
            <p className="font-serif text-lg leading-relaxed text-[#1A1210] italic">
              &ldquo;{citation.excerpt}&rdquo;
            </p>
          </div>

          {citation.score && (
            <div className="flex items-center justify-between text-sm text-[#54423C] px-1">
              <span>Embedding Semantic Alignment:</span>
              <span className="font-bold text-[#1A1210]">
                {Math.round(citation.score * 100)}% Confidence Match
              </span>
            </div>
          )}
        </div>

        <GreekKeyDivider className="my-2" />

        {/* Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
          <p className="text-xs text-[#63524C]">
            Gyaan Setu Verifiable Citation Engine • {isVideo ? "faster-whisper STT Timestamps" : "Zero Hallucinations"}
          </p>
          <div className="flex items-center gap-2">
            {jumpUrl && (
              <a
                href={jumpUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded-full bg-[#D4211C] text-white hover:bg-[#B31A16] font-bold text-xs transition-all shadow-md inline-flex items-center gap-1.5"
              >
                <span>Watch on YouTube</span>
                <span>▶️</span>
              </a>
            )}
            <button
              onClick={onClose}
              className="px-6 py-2 rounded-full bg-[#1A1210] text-[#F7EDCF] hover:bg-[#2E201B] font-bold text-sm transition-all"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
