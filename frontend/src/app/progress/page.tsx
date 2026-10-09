"use client";

import React, { useState, useEffect } from "react";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { useI18n } from "@/lib/i18n";
import { apiClient, KnowledgeGraphData, TopicNode } from "@/lib/api";

export default function ProgressPage() {
  const { t, lang } = useI18n();
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<TopicNode | null>(null);

  useEffect(() => {
    apiClient.getKnowledgeGraph().then((data) => {
      setGraphData(data);
      if (data.nodes.length > 0) setSelectedNode(data.nodes[0]);
    });
  }, []);

  const overallMastery = graphData
    ? Math.round(
        (graphData.nodes.reduce((acc, n) => acc + n.mastery_p, 0) /
          graphData.nodes.length) *
          100
      )
    : 0;

  return (
    <div className="w-full max-w-6xl mx-auto px-4 md:px-8 pt-24 pb-12 space-y-10">
      {/* Title */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <h1 className="font-display text-4xl md:text-5xl text-[#F7EDCF] tracking-wide drop-shadow-md">
          {t("progressTitle")}
        </h1>
        <p className="text-[#F7EDCF]/90 text-lg">
          {t("progressSubtitle")}
        </p>
      </div>

      {/* OVERALL MASTERY SUMMARY CARD */}
      <DoubleGoldCard size="md" className="flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-1 text-center md:text-left">
          <span className="text-xs font-bold uppercase tracking-wider text-[#D4211C]">
            Bayesian Knowledge Tracing (BKT) Engine
          </span>
          <h2 className="font-display text-3xl text-[#1A1210]">
            {t("progressMasteryLevel")}: {overallMastery}%
          </h2>
          <p className="text-sm text-[#63524C]">
            Calculated across {graphData?.nodes.length || 0} prerequisite curriculum concepts
          </p>
        </div>

        {/* Big Circular Metric */}
        <div className="relative w-28 h-28 flex items-center justify-center shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="40"
              stroke="#FAF4E4"
              strokeWidth="10"
              fill="none"
            />
            <circle
              cx="50"
              cy="50"
              r="40"
              stroke="#E2A63A"
              strokeWidth="10"
              fill="none"
              strokeDasharray="251.2"
              strokeDashoffset={251.2 * (1 - overallMastery / 100)}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <span className="absolute font-display text-2xl text-[#1A1210]">
            {overallMastery}%
          </span>
        </div>
      </DoubleGoldCard>

      {/* INTERACTIVE PREREQUISITE DAG GRAPH */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-2">
          <h2 className="font-display text-3xl text-[#F7EDCF]">
            {t("progressPrereqGraph")}
          </h2>
          {/* Legend */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-[#F7EDCF] bg-[#1A1210]/60 px-4 py-1.5 rounded-full border border-[#E2A63A]/40">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              {t("progressLegendMastered")}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#E2A63A]" />
              {t("progressLegendLearning")}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#D4211C]" />
              {t("progressLegendUnexplored")}
            </span>
          </div>
        </div>

        <DoubleGoldCard size="lg" className="overflow-hidden p-4 md:p-6">
          <div className="w-full h-[380px] md:h-[440px] bg-[#FAF4E4] rounded-2xl border border-[#E2A63A]/50 relative overflow-hidden select-none shadow-inner">
            {/* SVG Canvas for Edges and Nodes */}
            <svg className="w-full h-full" viewBox="0 0 900 420">
              <defs>
                <marker
                  id="dag-arrow"
                  viewBox="0 0 10 10"
                  refX="18"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#8C5D0D" />
                </marker>
              </defs>

              {/* Layout Coordinates */}
              {/* Level 0: x = 120 */}
              {/* Level 1: x = 380 */}
              {/* Level 2: x = 680 */}

              {/* Directed Edges */}
              {/* Node 1 (Asymptotics: 120, 210) -> Node 2 (Recursion: 380, 120) */}
              <path d="M 120 210 C 250 210, 250 120, 380 120" stroke="#8C5D0D" strokeWidth="2.5" fill="none" markerEnd="url(#dag-arrow)" strokeDasharray="4 2" />
              {/* Node 1 -> Node 4 (Graph Repr: 380, 300) */}
              <path d="M 120 210 C 250 210, 250 300, 380 300" stroke="#8C5D0D" strokeWidth="2.5" fill="none" markerEnd="url(#dag-arrow)" strokeDasharray="4 2" />
              {/* Node 2 -> Node 3 (Binary Search: 680, 70) */}
              <path d="M 380 120 C 530 120, 530 70, 680 70" stroke="#8C5D0D" strokeWidth="2.5" fill="none" markerEnd="url(#dag-arrow)" />
              {/* Node 2 -> Node 7 (DP: 680, 170) */}
              <path d="M 380 120 C 530 120, 530 170, 680 170" stroke="#8C5D0D" strokeWidth="2.5" fill="none" markerEnd="url(#dag-arrow)" />
              {/* Node 4 -> Node 5 (BFS: 680, 270) */}
              <path d="M 380 300 C 530 300, 530 270, 680 270" stroke="#8C5D0D" strokeWidth="2.5" fill="none" markerEnd="url(#dag-arrow)" />
              {/* Node 4 -> Node 6 (DFS: 680, 370) */}
              <path d="M 380 300 C 530 300, 530 370, 680 370" stroke="#8C5D0D" strokeWidth="2.5" fill="none" markerEnd="url(#dag-arrow)" />
            </svg>

            {/* Interactive HTML Nodes Layered on Coordinates */}
            {graphData?.nodes.map((node) => {
              const coords: { [id: number]: { x: number; y: number } } = {
                1: { x: 50, y: 175 },
                2: { x: 290, y: 85 },
                4: { x: 290, y: 265 },
                3: { x: 590, y: 35 },
                7: { x: 590, y: 135 },
                5: { x: 590, y: 235 },
                6: { x: 590, y: 335 },
              };
              const c = coords[node.id] || { x: 50, y: 50 };
              const isSelected = selectedNode?.id === node.id;

              const statusColor =
                node.mastery_p >= 0.85
                  ? "border-emerald-600 bg-emerald-50 text-emerald-950"
                  : node.mastery_p >= 0.4
                  ? "border-[#E2A63A] bg-amber-50 text-amber-950"
                  : "border-[#D4211C] bg-red-50 text-red-950";

              return (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`absolute p-3 rounded-2xl border-2 transition-all flex flex-col items-start gap-1 shadow-md hover:scale-105 ${statusColor} ${
                    isSelected ? "ring-4 ring-[#1A1210] scale-105 z-10" : ""
                  }`}
                  style={{
                    left: `${(c.x / 900) * 100}%`,
                    top: `${(c.y / 420) * 100}%`,
                    width: "160px",
                  }}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-[10px] font-bold uppercase tracking-wider opacity-70">
                      Level {node.level}
                    </span>
                    <span className="text-[11px] font-bold">
                      {Math.round(node.mastery_p * 100)}%
                    </span>
                  </div>
                  <span className="text-xs font-bold line-clamp-1 text-left">
                    {lang === "hi" && node.name_hi ? node.name_hi : node.name}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Selected Concept Deep Dive Drawer */}
          {selectedNode && (
            <div className="mt-4 p-5 rounded-2xl bg-white border border-[#E2A63A]/50 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#1A1210] text-[#F7EDCF] text-xs font-bold">
                    Concept #{selectedNode.id}
                  </span>
                  <h3 className="font-bold text-lg text-[#1A1210]">
                    {lang === "hi" && selectedNode.name_hi ? selectedNode.name_hi : selectedNode.name}
                  </h3>
                </div>
                <p className="text-xs text-[#54423C]">
                  {selectedNode.summary}
                </p>
              </div>

              <div className="flex items-center gap-4 text-xs font-medium text-[#1A1210] shrink-0">
                <div className="text-center px-3 py-1.5 rounded-xl bg-[#FAF4E4] border border-[#E2A63A]/40">
                  <span className="block text-[10px] text-[#63524C]">Stability</span>
                  <span className="font-bold">{selectedNode.stability_days} days</span>
                </div>
                <div className="text-center px-3 py-1.5 rounded-xl bg-[#FAF4E4] border border-[#E2A63A]/40">
                  <span className="block text-[10px] text-[#63524C]">Attempts</span>
                  <span className="font-bold">{selectedNode.attempts} questions</span>
                </div>
              </div>
            </div>
          )}
        </DoubleGoldCard>
      </div>

      <GreekKeyDivider />

      {/* EBBINGHAUS FORGETTING CURVE VISUALIZATION */}
      <DoubleGoldCard size="md" className="space-y-6">
        <div className="border-b border-[#E2A63A]/30 pb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-[#D4211C]">
            Cognitive Decay Modeling
          </span>
          <h2 className="font-display text-2xl md:text-3xl text-[#1A1210]">
            {t("progressForgettingCurve")}
          </h2>
          <p className="text-xs text-[#63524C] mt-1">
            Simulated memory retention probability R(t) = e^(-t/S) with optimal spaced review interventions
          </p>
        </div>

        {/* Decay Curve SVG */}
        <div className="w-full h-48 bg-white rounded-xl p-4 border border-[#E2A63A]/40 shadow-inner relative">
          <svg className="w-full h-full" viewBox="0 0 600 160">
            {/* Grid Lines */}
            <line x1="50" y1="20" x2="580" y2="20" stroke="#EAE0C8" strokeWidth="1" strokeDasharray="4 2" />
            <line x1="50" y1="70" x2="580" y2="70" stroke="#EAE0C8" strokeWidth="1" strokeDasharray="4 2" />
            <line x1="50" y1="120" x2="580" y2="120" stroke="#EAE0C8" strokeWidth="1" strokeDasharray="4 2" />

            {/* Y Axis Labels */}
            <text x="15" y="24" fontSize="10" fill="#8C5D0D" fontWeight="bold">100%</text>
            <text x="20" y="74" fontSize="10" fill="#8C5D0D">60%</text>
            <text x="20" y="124" fontSize="10" fill="#8C5D0D">20%</text>

            {/* Unreinforced Decay Curve (Red Faint) */}
            <path
              d="M 50 20 Q 150 110, 580 135"
              stroke="#D4211C"
              strokeWidth="2"
              strokeDasharray="4 4"
              fill="none"
              opacity="0.6"
            />

            {/* Spaced Repetition Boost Curve (Gold Solid with Spikes) */}
            <path
              d="M 50 20 Q 100 65, 150 75 L 150 20 Q 220 50, 300 55 L 300 20 Q 420 35, 580 40"
              stroke="#E2A63A"
              strokeWidth="3"
              fill="none"
            />

            {/* Intervention Dots */}
            <circle cx="150" cy="20" r="4" fill="#1A1210" />
            <circle cx="300" cy="20" r="4" fill="#1A1210" />
          </svg>

          <div className="flex items-center justify-between text-[11px] font-bold text-[#63524C] px-8 pt-1">
            <span>Initial Learning</span>
            <span>Day 1 Review (Spike 1)</span>
            <span>Day 4 Review (Spike 2)</span>
            <span>Stable Long-Term Memory</span>
          </div>
        </div>
      </DoubleGoldCard>
    </div>
  );
}
