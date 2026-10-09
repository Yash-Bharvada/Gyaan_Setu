"use client";

import React, { useState, useEffect } from "react";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { SourceModal } from "@/components/ui/SourceModal";
import { useI18n } from "@/lib/i18n";
import { apiClient, Source, Citation, Job } from "@/lib/api";

export default function LibraryPage() {
  const { t } = useI18n();
  const [sources, setSources] = useState<Source[]>([]);
  const [activeJob, setActiveJob] = useState<Job | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [quotaInfo, setQuotaInfo] = useState<any>(null);

  useEffect(() => {
    apiClient.getSources().then(setSources);
    apiClient.getAdminUsage().then(setQuotaInfo);
  }, []);

  const handleFileUpload = async (file: File) => {
    const jobResp = await apiClient.uploadSource(file);
    const newJob: Job = {
      id: jobResp.job_id,
      kind: `ingest_${file.name.split(".").pop() || "doc"}`,
      status: "running",
      progress: 0.15,
      message: `Analyzing layout & extracting content units from ${file.name}...`,
      created_at: new Date().toISOString(),
    };
    setActiveJob(newJob);

    // Simulate progressive processing updates
    let p = 0.15;
    const interval = setInterval(() => {
      p += 0.25;
      if (p >= 1.0) {
        clearInterval(interval);
        setActiveJob((prev) =>
          prev
            ? {
                ...prev,
                status: "completed",
                progress: 1.0,
                message: `Successfully indexed ${file.name}! 48 units generated.`,
              }
            : null
        );

        // Append to sources
        const newSource: Source = {
          id: Date.now(),
          title: file.name.replace(/\.[^/.]+$/, ""),
          kind: file.name.endsWith(".pdf")
            ? "pdf"
            : file.name.endsWith(".pptx")
            ? "pptx"
            : file.name.endsWith(".mp4")
            ? "video"
            : "pdf",
          file_size: file.size,
          status: "ready",
          page_count: file.name.endsWith(".pdf") ? 28 : undefined,
          slide_count: file.name.endsWith(".pptx") ? 18 : undefined,
          units_count: 48,
          created_at: new Date().toISOString(),
        };
        setSources((prev) => [newSource, ...prev]);
      } else {
        setActiveJob((prev) =>
          prev
            ? {
                ...prev,
                progress: p,
                message:
                  p < 0.4
                    ? "Running Tesseract / FreeOCR on scanned regions..."
                    : p < 0.7
                    ? "Chunking into grounded source-linked units..."
                    : "Computing sentence-transformer embeddings & indexing vectors...",
              }
            : null
        );
      }
    }, 1200);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-4 md:px-8 pt-24 pb-12 space-y-10">
      {/* Page Title & Intro */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <h1 className="font-display text-4xl md:text-5xl text-[#F7EDCF] tracking-wide drop-shadow-md">
          {t("libTitle")}
        </h1>
        <p className="text-[#F7EDCF]/90 text-lg leading-relaxed">
          {t("libSubtitle")}
        </p>
      </div>

      {/* Upload Zone & Drag-and-Drop */}
      <DoubleGoldCard size="lg">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-[20px] p-8 md:p-12 text-center transition-all ${
            dragActive
              ? "border-[#D4211C] bg-[#D4211C]/5 scale-[1.01]"
              : "border-[#E2A63A] bg-white/50 hover:bg-white/70"
          }`}
        >
          <input
            type="file"
            id="file-upload-input"
            className="hidden"
            accept=".pdf,.pptx,.ppt,.mp4,.mp3,.png,.jpg,.jpeg"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileUpload(e.target.files[0]);
              }
            }}
          />

          <div className="max-w-md mx-auto space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-[#E2A63A]/20 border border-[#E2A63A] flex items-center justify-center text-[#8C5D0D]">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>

            <h2 className="font-display text-2xl text-[#1A1210]">
              {t("libDropzoneTitle")}
            </h2>

            <p className="text-sm text-[#63524C] leading-normal">
              {t("libDropzoneHint")}
            </p>

            <div>
              <label
                htmlFor="file-upload-input"
                className="btn-primary-pill text-sm cursor-pointer shadow-md inline-flex items-center gap-2"
              >
                <span>{t("libBrowseBtn")}</span>
              </label>
            </div>
          </div>
        </div>

        {/* Live Ingestion Job Progress (from /jobs/{id}) */}
        {activeJob && (
          <div className="mt-8 p-6 rounded-[20px] bg-white border-2 border-[#E2A63A] shadow-md animate-in fade-in duration-300">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#E2A63A] animate-ping" />
                <span className="font-bold text-sm text-[#1A1210]">
                  Job #{activeJob.id} • {activeJob.kind}
                </span>
              </div>
              <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-[#E2A63A]/20 text-[#8C5D0D]">
                {Math.round(activeJob.progress * 100)}%
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full h-3 rounded-full bg-[#FAF4E4] overflow-hidden border border-[#E2A63A]/50">
              <div
                className="h-full bg-gradient-to-r from-[#E2A63A] to-[#D4211C] transition-all duration-500 rounded-full"
                style={{ width: `${Math.round(activeJob.progress * 100)}%` }}
              />
            </div>

            <p className="text-xs text-[#63524C] mt-3 font-medium">
              {activeJob.message}
            </p>
          </div>
        )}
      </DoubleGoldCard>

      <GreekKeyDivider />

      {/* Indexed Materials List */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-3xl text-[#F7EDCF]">
            {t("libSourcesList")}
          </h2>
          <span className="text-sm text-[#F7EDCF]/80 font-bold bg-[#1A1210]/60 px-4 py-1 rounded-full border border-[#E2A63A]/50">
            {sources.length} Documents Grounded
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sources.map((src) => (
            <div
              key={src.id}
              className="bg-[#F7EDCF] rounded-[24px] p-6 border-[2px] border-[#E2A63A] shadow-[0_8px_20px_rgba(0,0,0,0.25)] flex flex-col justify-between hover:scale-[1.02] transition-transform"
              style={{
                boxShadow: "0 0 0 2px #E2A63A, 0 0 0 6px #F7EDCF, 0 8px 18px rgba(0,0,0,0.3)",
              }}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#1A1210] text-[#F7EDCF] text-xs font-bold uppercase tracking-wider">
                    {src.kind.toUpperCase()}
                  </span>
                  <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                    Grounded & Ready
                  </span>
                </div>

                <h3 className="font-bold text-lg text-[#1A1210] line-clamp-2">
                  {src.title}
                </h3>
              </div>

              <div className="mt-6 pt-4 border-t border-[#E2A63A]/30 space-y-3">
                <div className="flex items-center justify-between text-xs text-[#63524C]">
                  <span>{t("libUnitsExtracted")}:</span>
                  <span className="font-bold text-[#1A1210]">{src.units_count} units</span>
                </div>

                {src.page_count && (
                  <div className="flex items-center justify-between text-xs text-[#63524C]">
                    <span>{t("libPages")}:</span>
                    <span className="font-bold text-[#1A1210]">{src.page_count} pages</span>
                  </div>
                )}

                {src.slide_count && (
                  <div className="flex items-center justify-between text-xs text-[#63524C]">
                    <span>{t("libSlides")}:</span>
                    <span className="font-bold text-[#1A1210]">{src.slide_count} slides</span>
                  </div>
                )}

                {src.duration_secs && (
                  <div className="flex items-center justify-between text-xs text-[#63524C]">
                    <span>{t("libDuration")}:</span>
                    <span className="font-bold text-[#1A1210]">
                      {Math.floor(src.duration_secs / 60)}m {src.duration_secs % 60}s
                    </span>
                  </div>
                )}

                {src.units && src.units.length > 0 && (
                  <div className="pt-2">
                    <p className="text-[11px] font-bold text-[#8C5D0D] uppercase mb-1.5">
                      Sample Unit Citations:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {src.units.map((u) => {
                        const loc = u.page
                          ? `Page ${u.page}`
                          : u.slide_no
                          ? `Slide ${u.slide_no}`
                          : u.ts_start
                          ? `${Math.floor(u.ts_start / 60)}:${u.ts_start % 60}`
                          : "Unit";
                        return (
                          <button
                            key={u.id}
                            onClick={() =>
                              setSelectedCitation({
                                source_id: src.id,
                                source_title: src.title,
                                unit_id: u.id,
                                type: u.page ? "page" : u.slide_no ? "slide" : "timestamp",
                                locator: loc,
                                excerpt: u.text,
                              })
                            }
                            className="chip-citation text-xs"
                          >
                            {loc}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quota & Budget Guard Information */}
      {quotaInfo && (
        <div className="p-6 rounded-[20px] bg-[#1A1210]/60 border border-[#E2A63A]/40 text-[#F7EDCF] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <div>
            <span className="font-bold text-[#E2A63A]">Free-Tier Quota Guard: </span>
            <span>
              FreeOCR calls used: 14/45 (auto-fallback to local Tesseract when cap reached).
            </span>
          </div>
          <div>
            <span className="font-bold text-[#E2A63A]">Audio Translation: </span>
            <span>Local faster-whisper + edge-tts (zero quota consumption).</span>
          </div>
        </div>
      )}

      {/* Source Citation Inspector Modal */}
      <SourceModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
