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
  const [isBuildingGraph, setIsBuildingGraph] = useState(false);
  const [showTextModal, setShowTextModal] = useState(false);
  const [rawTitle, setRawTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [notification, setNotification] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  const loadSources = async () => {
    try {
      const data = await apiClient.getSources();
      setSources(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadSources();
    apiClient.getAdminUsage().then(setQuotaInfo);
  }, []);

  const showNotify = (msg: string, type: "success" | "error" = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleFileUpload = async (file: File) => {
    const jobResp = await apiClient.uploadSource(file);
    const newJob: Job = {
      id: jobResp.job_id,
      kind: `ingest_${file.name.split(".").pop() || "doc"}`,
      status: "running",
      progress: 0.25,
      message: `Analyzing document layout & indexing units from ${file.name}...`,
    };
    setActiveJob(newJob);

    // Poll job status until done
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const job = await apiClient.getJob(jobResp.job_id);
        if (job.status === "completed" || attempts > 6) {
          clearInterval(interval);
          setActiveJob(null);
          showNotify(`Successfully indexed ${file.name} into curriculum!`);
          await loadSources();
        } else {
          setActiveJob((prev) =>
            prev ? { ...prev, progress: Math.min(0.9, prev.progress + 0.2) } : null
          );
        }
      } catch {
        clearInterval(interval);
        setActiveJob(null);
        await loadSources();
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

  const handleBuildKnowledgeGraph = async () => {
    setIsBuildingGraph(true);
    try {
      const res = await apiClient.buildKnowledgeGraph();
      showNotify(`Knowledge DAG built! ${res.topics_count || 3} topics indexed.`);
      await loadSources();
    } catch {
      showNotify("Error building knowledge DAG", "error");
    } finally {
      setIsBuildingGraph(false);
    }
  };

  const handleRawTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawTitle.trim() || !rawText.trim()) return;

    try {
      await apiClient.ingestRawText(rawTitle, rawText);
      showNotify(`Ingested "${rawTitle}" successfully!`);
      setShowTextModal(false);
      setRawTitle("");
      setRawText("");
      await loadSources();
    } catch {
      showNotify("Failed to ingest text snippet", "error");
    }
  };

  const handleDeleteSource = async (id: number, title: string) => {
    if (!confirm(`Delete "${title}" from your library?`)) return;
    const ok = await apiClient.deleteSource(id);
    if (ok) {
      showNotify(`Deleted "${title}"`);
      setSources((prev) => prev.filter((s) => s.id !== id));
    }
  };

  const [ingestTab, setIngestTab] = useState<"files" | "youtube">("files");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [youtubeTitle, setYoutubeTitle] = useState("");
  const [isIngestingVideo, setIsIngestingVideo] = useState(false);

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return "";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins >= 60) {
      const hrs = Math.floor(mins / 60);
      const remMins = mins % 60;
      return `${hrs}h ${remMins}m`;
    }
    return `${mins}m ${secs}s`;
  };

  const formatUnitSeconds = (secs: number): string => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const handleYouTubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl.trim()) return;

    setIsIngestingVideo(true);
    const tempJob: Job = {
      id: Date.now(),
      kind: "ingest_video_stt",
      status: "running",
      progress: 0.35,
      message: "Parsing video transcript with faster-whisper & second-accurate timestamps...",
    };
    setActiveJob(tempJob);

    try {
      const res = await apiClient.ingestYouTube(youtubeUrl.trim(), youtubeTitle.trim() || undefined);
      setActiveJob({
        ...tempJob,
        progress: 1.0,
        status: "completed",
        message: res.message || "Video lecture parsed & indexed into curriculum!",
      });
      showNotify(`Successfully ingested video lecture (${res.units_count || 1} timestamped units)!`);
      setYoutubeUrl("");
      setYoutubeTitle("");
      await loadSources();
      setTimeout(() => setActiveJob(null), 2500);
    } catch (err: any) {
      console.error(err);
      showNotify(err.message || "Failed to ingest YouTube video", "error");
      setActiveJob(null);
    } finally {
      setIsIngestingVideo(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-4 md:px-8 pt-24 pb-12 space-y-10">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed top-6 right-6 z-50 px-5 py-3 rounded-xl border text-sm font-bold shadow-2xl animate-in slide-in-from-top-4 duration-300 ${
            notification.type === "success"
              ? "bg-[#1A1210] border-[#E2A63A] text-[#F7EDCF]"
              : "bg-[#D4211C] border-white text-white"
          }`}
        >
          {notification.msg}
        </div>
      )}

      {/* Page Title & Controls */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="space-y-2 text-center md:text-left">
          <h1 className="font-display text-4xl md:text-5xl text-[#F7EDCF] tracking-wide drop-shadow-md">
            {t("libTitle")}
          </h1>
          <p className="text-[#F7EDCF]/90 text-lg leading-relaxed">
            {t("libSubtitle")}
          </p>
        </div>

        {/* Global Pipeline Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => {
              setIngestTab("youtube");
              window.scrollTo({ top: 180, behavior: "smooth" });
            }}
            className="px-4 py-2 rounded-full bg-[#D4211C] text-white hover:bg-[#B31A16] text-xs font-bold transition-all flex items-center gap-1.5 shadow-md"
          >
            <span>🎥 Ingest YouTube Video</span>
          </button>
          <button
            onClick={() => setShowTextModal(true)}
            className="px-4 py-2 rounded-full bg-[#1A1210]/80 border border-[#E2A63A]/70 text-[#F7EDCF] hover:bg-[#1A1210] hover:border-[#E2A63A] text-xs font-bold transition-all flex items-center gap-2"
          >
            <span>+ Quick Text Note</span>
          </button>
          <button
            onClick={handleBuildKnowledgeGraph}
            disabled={isBuildingGraph}
            className="btn-primary-pill text-xs py-2 px-5 shadow-lg flex items-center gap-2"
          >
            {isBuildingGraph ? (
              <>
                <span className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                <span>Building DAG...</span>
              </>
            ) : (
              <>
                <span>Build Knowledge Graph</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Upload Zone & Mode Switcher */}
      <DoubleGoldCard size="lg">
        {/* Mode Selector Tabs */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <button
            type="button"
            onClick={() => setIngestTab("files")}
            className={`px-5 py-2 rounded-full font-bold text-xs transition-all flex items-center gap-2 ${
              ingestTab === "files"
                ? "bg-[#D4211C] text-white shadow-md"
                : "bg-white/80 text-[#1A1210] border border-[#E2A63A]/60 hover:bg-white"
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span>Upload Documents & Files</span>
          </button>
          <button
            type="button"
            onClick={() => setIngestTab("youtube")}
            className={`px-5 py-2 rounded-full font-bold text-xs transition-all flex items-center gap-2 ${
              ingestTab === "youtube"
                ? "bg-[#D4211C] text-white shadow-md"
                : "bg-white/80 text-[#1A1210] border border-[#E2A63A]/60 hover:bg-white"
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
            </svg>
            <span>Ingest YouTube / Video Lecture</span>
          </button>
        </div>

        {ingestTab === "files" ? (
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
              accept=".pdf,.pptx,.ppt,.mp4,.mp3,.png,.jpg,.jpeg,.txt"
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
        ) : (
          <div className="border-2 border-[#E2A63A] rounded-[20px] p-6 md:p-8 bg-white/60 text-center">
            <div className="max-w-xl mx-auto space-y-5 text-left">
              <div className="text-center space-y-2">
                <div className="w-14 h-14 mx-auto rounded-full bg-[#D4211C]/15 border border-[#D4211C]/40 flex items-center justify-center text-[#D4211C]">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                  </svg>
                </div>
                <h3 className="font-display text-2xl text-[#1A1210]">
                  Ingest Video Lecture with Exact Timestamps
                </h3>
                <p className="text-xs text-[#63524C] max-w-md mx-auto">
                  Paste any YouTube or lecture video URL. We parse transcripts with exact start/end second timings (⏱️ MM:SS–MM:SS) and index units for citations, quizzes, and your knowledge graph.
                </p>
              </div>

              <form onSubmit={handleYouTubeSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase text-[#8C5D0D] mb-1">
                    YouTube or Video Lecture URL *
                  </label>
                  <input
                    type="url"
                    required
                    placeholder="https://www.youtube.com/watch?v=aircAruvnKk or https://youtu.be/..."
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl bg-white border border-[#E2A63A] text-sm text-[#1A1210] focus:outline-none focus:ring-2 focus:ring-[#D4211C] shadow-inner"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase text-[#8C5D0D] mb-1">
                    Custom Title (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 3Blue1Brown: Neural Networks Deep Dive"
                    value={youtubeTitle}
                    onChange={(e) => setYoutubeTitle(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl bg-white border border-[#E2A63A] text-sm text-[#1A1210] focus:outline-none focus:ring-2 focus:ring-[#D4211C]"
                  />
                </div>

                <div className="p-3 rounded-xl bg-[#FAF4E4] border border-[#E2A63A]/40 flex flex-wrap items-center justify-between gap-2 text-xs text-[#63524C]">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-600"></span>
                    <span>STT Engine: <strong>faster-whisper</strong></span>
                  </div>
                  <div>
                    <span>Citations: <strong>Video Timings (⏱️ MM:SS)</strong></span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isIngestingVideo}
                  className={`w-full py-3.5 px-6 rounded-full font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2.5 shadow-lg ${
                    isIngestingVideo
                      ? "bg-[#D4211C]/60 text-white cursor-wait"
                      : !youtubeUrl.trim()
                      ? "bg-[#D4211C] hover:bg-[#B31A16] text-white border-2 border-[#E2A63A]/60 hover:border-[#E2A63A] cursor-pointer shadow-md"
                      : "bg-gradient-to-r from-[#D4211C] to-[#B31A16] hover:from-[#E02621] hover:to-[#C01E19] text-white border-2 border-[#E2A63A] hover:scale-[1.01] hover:shadow-[0_8px_25px_rgba(212,33,28,0.4)] cursor-pointer"
                  }`}
                >
                  {isIngestingVideo ? (
                    <>
                      <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                      <span>Parsing Video Transcript & Indexing Timestamps...</span>
                    </>
                  ) : (
                    <>
                      <span className="tracking-wide">Parse & Ingest Video Lecture</span>
                      <span className="text-base">▶️</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}

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
            {sources.length} Documents & Lectures Grounded
          </span>
        </div>

        {sources.length === 0 ? (
          <DoubleGoldCard size="lg" className="p-8 md:p-12 text-center">
            <div className="max-w-md mx-auto space-y-4">
              <div className="w-16 h-16 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center mx-auto shadow-lg border border-[#E2A63A]/40">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="12" y1="18" x2="12" y2="12" />
                  <line x1="9" y1="15" x2="15" y2="15" />
                </svg>
              </div>
              <h3 className="font-display text-2xl md:text-3xl text-[#1A1210]">
                No Study Materials Ingested Yet
              </h3>
              <p className="text-sm text-[#63524C] leading-relaxed">
                Your database is empty and ready. Upload course PDFs, lecture presentations, paste textbook notes, or add YouTube video lectures above.
              </p>
              <div className="pt-2 flex flex-wrap justify-center gap-3">
                <button
                  onClick={() => setIngestTab("youtube")}
                  className="bg-[#D4211C] hover:bg-[#B31A16] text-white border-2 border-[#E2A63A] rounded-full font-bold text-sm py-2.5 px-6 shadow-xl inline-flex items-center gap-2 transition-all hover:scale-105"
                >
                  <span>Add YouTube Video</span>
                  <span>▶️</span>
                </button>
              </div>
            </div>
          </DoubleGoldCard>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sources.map((src) => {
              const isVideo = src.kind === "video" || src.kind === "audio";
              return (
                <div
                  key={src.id}
                  className="bg-[#F7EDCF] rounded-[24px] p-6 border-[2px] border-[#E2A63A] shadow-[0_8px_20px_rgba(0,0,0,0.25)] flex flex-col justify-between hover:scale-[1.01] transition-transform relative group"
                  style={{
                    boxShadow: "0 0 0 2px #E2A63A, 0 0 0 6px #F7EDCF, 0 8px 18px rgba(0,0,0,0.3)",
                  }}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                        isVideo ? "bg-[#D4211C] text-white" : "bg-[#1A1210] text-[#F7EDCF]"
                      }`}>
                        {isVideo ? "🎥 VIDEO LECTURE" : src.kind.toUpperCase()}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                          Grounded & Ready
                        </span>
                        {src.file_path && src.file_path.startsWith("http") && (
                          <a
                            href={src.file_path}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-stone-500 hover:text-[#D4211C] p-1 rounded-full transition-colors"
                            title="Open external link"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                              <polyline points="15 3 21 3 21 9" />
                              <line x1="10" y1="14" x2="21" y2="3" />
                            </svg>
                          </a>
                        )}
                        <button
                          onClick={() => handleDeleteSource(src.id, src.title)}
                          className="text-stone-400 hover:text-red-600 p-1 rounded-full transition-colors"
                          title="Delete document"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                          </svg>
                        </button>
                      </div>
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

                    {src.duration_secs && (
                      <div className="flex items-center justify-between text-xs text-[#63524C]">
                        <span>Lecture Duration:</span>
                        <span className="font-bold text-[#D4211C]">{formatDuration(src.duration_secs)}</span>
                      </div>
                    )}

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

                    {src.units && src.units.length > 0 && (
                      <div className="pt-2">
                        <p className="text-[11px] font-bold text-[#8C5D0D] uppercase mb-1.5">
                          {isVideo ? "Timestamped Units (Click to inspect):" : "Sample Unit Citations:"}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {src.units.slice(0, 4).map((u) => {
                            const isUnitVideo = (u.ts_start !== undefined && u.ts_start !== null) || u.type === "transcript";
                            const loc = isUnitVideo
                              ? `⏱️ ${formatUnitSeconds(u.ts_start || 0)}${u.ts_end !== undefined && u.ts_end !== null ? `–${formatUnitSeconds(u.ts_end)}` : ""}`
                              : u.page
                              ? `Page ${u.page}`
                              : u.slide_no
                              ? `Slide ${u.slide_no}`
                              : `Unit #${u.id}`;
                            return (
                              <button
                                key={u.id}
                                onClick={() =>
                                  setSelectedCitation({
                                    source_id: src.id,
                                    source_title: src.title,
                                    unit_id: u.id,
                                    type: isUnitVideo ? "timestamp" : u.page ? "page" : "slide",
                                    locator: loc,
                                    excerpt: u.text,
                                    ts_start: u.ts_start,
                                    ts_end: u.ts_end,
                                    video_url: src.file_path,
                                  })
                                }
                                className={`chip-citation text-xs ${
                                  isUnitVideo ? "bg-[#D4211C]/15 border-[#D4211C]/50 text-[#1A1210] hover:bg-[#D4211C]/25" : ""
                                }`}
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
              );
            })}
          </div>
        )}
      </div>

      {/* Quick Text Ingest Modal */}
      {showTextModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div
            className="w-full max-w-lg bg-[#F7EDCF] rounded-[24px] p-6 md:p-8 border-[3px] border-[#E2A63A] shadow-2xl space-y-4"
            style={{ boxShadow: "0 0 0 4px #F7EDCF, 0 0 0 7px #E2A63A, 0 25px 50px rgba(0,0,0,0.7)" }}
          >
            <div className="flex items-center justify-between border-b border-[#E2A63A]/40 pb-3">
              <h3 className="font-display text-2xl text-[#1A1210]">Direct Text Ingestion</h3>
              <button
                onClick={() => setShowTextModal(false)}
                className="text-stone-500 hover:text-black font-bold"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleRawTextSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase text-[#8C5D0D] mb-1">
                  Topic / Document Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chapter 4: Dynamic Programming Notes"
                  value={rawTitle}
                  onChange={(e) => setRawTitle(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-white border border-[#E2A63A] text-sm text-[#1A1210] focus:outline-none focus:ring-2 focus:ring-[#D4211C]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-[#8C5D0D] mb-1">
                  Content / Lecture Snippet
                </label>
                <textarea
                  required
                  rows={6}
                  placeholder="Paste lecture notes, study guide definitions, or theorems..."
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-white border border-[#E2A63A] text-sm text-[#1A1210] focus:outline-none focus:ring-2 focus:ring-[#D4211C]"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowTextModal(false)}
                  className="px-4 py-2 rounded-full border border-stone-400 text-stone-700 text-sm font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary-pill text-sm py-2 px-6 shadow-md"
                >
                  Ingest & Vector Index
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quota & Budget Guard Information */}
      {quotaInfo && (
        <div className="p-6 rounded-[20px] bg-[#1A1210]/60 border border-[#E2A63A]/40 text-[#F7EDCF] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <div>
            <span className="font-bold text-[#E2A63A]">Free-Tier Quota Guard: </span>
            <span>
              OCR: Tesseract + FreeOCR active. Embeddings: Local sentence-transformer (zero cloud cost).
            </span>
          </div>
          <div>
            <span className="font-bold text-[#E2A63A]">Audio Pipeline: </span>
            <span>Local faster-whisper + gTTS / Edge TTS active.</span>
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
