"use client";

import React from "react";
import { Citation } from "@/lib/api";
import { GreekKeyDivider } from "./GreekKeyDivider";

interface SourceModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const SourceModal: React.FC<SourceModalProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl bg-[#F7EDCF] text-[#1A1210] rounded-[24px] p-6 md:p-8 border-[3px] border-[#E2A63A] shadow-[0_20px_50px_rgba(0,0,0,0.6)]"
        style={{
          boxShadow:
            "0 0 0 4px #F7EDCF, 0 0 0 7px #E2A63A, 0 25px 50px -12px rgba(0, 0, 0, 0.7)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-[#E2A63A]/40 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-3 py-0.5 rounded-full bg-[#D4211C] text-white text-xs font-bold uppercase tracking-wider">
                Verified Grounded Source
              </span>
              <span className="px-3 py-0.5 rounded-full bg-[#E2A63A]/20 text-[#8C5D0D] border border-[#E2A63A] text-xs font-bold">
                {citation.locator}
              </span>
            </div>
            <h3 className="font-display text-2xl text-[#1A1210]">
              {citation.source_title}
            </h3>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-[#E2A63A]/20 text-[#1A1210] transition-colors"
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

        {/* Content Body */}
        <div className="py-6 space-y-4">
          <div className="p-4 rounded-xl bg-white/80 border border-[#E2A63A]/40 shadow-inner">
            <p className="text-xs font-bold text-[#8C5D0D] uppercase tracking-wider mb-2">
              Extracted Grounded Excerpt ({citation.locator}):
            </p>
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
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-[#63524C]">
            Gyaan Setu Verifiable Citation Engine • Zero Hallucinations
          </p>
          <button
            onClick={onClose}
            className="px-6 py-2 rounded-full bg-[#1A1210] text-[#F7EDCF] hover:bg-[#2E201B] font-bold text-sm transition-all"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
};
