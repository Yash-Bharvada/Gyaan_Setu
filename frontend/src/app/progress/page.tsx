"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import Link from "next/link";
import { DoubleGoldCard } from "@/components/ui/DoubleGoldCard";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { useI18n } from "@/lib/i18n";
import { apiClient, KnowledgeGraphData, TopicNode, PrerequisiteEdge } from "@/lib/api";

interface LayoutNode extends TopicNode {
  rank: number;
  x: number;
  y: number;
}

export default function ProgressPage() {
  const { t, lang } = useI18n();
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<number | null>(null);
  const [filterChapterId, setFilterChapterId] = useState<number | "all">("all");
  const [viewTab, setViewTab] = useState<"dag" | "roadmap" | "chapters">("dag");
  const [loading, setLoading] = useState(true);

  // Pan and Zoom Canvas State
  const [zoom, setZoom] = useState(0.85);
  const [pan, setPan] = useState({ x: 40, y: 30 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isExpanded, setIsExpanded] = useState(false);
  const canvasContainerRef = useRef<HTMLDivElement>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getKnowledgeGraph(1);
      setGraphData(data);
      if (data.nodes.length > 0) {
        setSelectedNodeId(data.nodes[0].id);
      }
    } catch (e) {
      console.warn("Failed to load knowledge graph:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const hasNodes = Boolean(graphData && graphData.nodes.length > 0);

  // Chapters list (Level 0 nodes)
  const chapters = useMemo(() => {
    if (!graphData?.nodes) return [];
    return graphData.nodes.filter(
      (n) => n.level === 0 || n.parent_id === null || n.name.toLowerCase().startsWith("chapter")
    );
  }, [graphData]);

  // Overall Mastery calculation across all curriculum nodes
  const overallMastery = useMemo(() => {
    if (!hasNodes || !graphData?.nodes.length) return 0;
    const sum = graphData.nodes.reduce((acc, n) => acc + (n.mastery_p ?? 0.3), 0);
    return Math.round((sum / graphData.nodes.length) * 100);
  }, [hasNodes, graphData]);

  // Mastery categories count
  const masteryStats = useMemo(() => {
    if (!graphData?.nodes) return { mastered: 0, inProgress: 0, needsReview: 0 };
    let mastered = 0;
    let inProgress = 0;
    let needsReview = 0;
    graphData.nodes.forEach((n) => {
      const p = n.mastery_p ?? 0.3;
      if (p >= 0.85) mastered++;
      else if (p >= 0.5) inProgress++;
      else needsReview++;
    });
    return { mastered, inProgress, needsReview };
  }, [graphData]);

  // Filter nodes based on selected chapter scope
  const filteredNodes = useMemo(() => {
    if (!graphData?.nodes) return [];
    if (filterChapterId === "all") return graphData.nodes;

    // Filter to chapter itself, child concepts, and direct connections
    const targetChapter = graphData.nodes.find((n) => n.id === filterChapterId);
    const directChildIds = new Set(
      graphData.nodes.filter((n) => n.parent_id === filterChapterId).map((n) => n.id)
    );
    if (targetChapter) directChildIds.add(targetChapter.id);

    // Also include immediate prerequisite or dependent edges for context
    const relatedEdgeIds = new Set<number>();
    graphData.edges.forEach((e) => {
      if (directChildIds.has(e.from) || directChildIds.has(e.to)) {
        relatedEdgeIds.add(e.from);
        relatedEdgeIds.add(e.to);
      }
    });

    return graphData.nodes.filter((n) => directChildIds.has(n.id) || relatedEdgeIds.has(n.id));
  }, [graphData, filterChapterId]);

  const activeNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  // Filter edges active between visible nodes
  const activeEdges = useMemo(() => {
    if (!graphData?.edges) return [];
    return graphData.edges.filter((e) => activeNodeIds.has(e.from) && activeNodeIds.has(e.to));
  }, [graphData, activeNodeIds]);

  // TOPOLOGICAL RANKING & NON-OVERLAPPING COORDINATES CALCULATION
  const { layoutNodes, layoutEdges, canvasWidth, canvasHeight, sortedRanks } = useMemo(() => {
    if (filteredNodes.length === 0) {
      return { layoutNodes: [], layoutEdges: [], canvasWidth: 900, canvasHeight: 500, sortedRanks: [] };
    }

    const inDegree = new Map<number, number>();
    const adj = new Map<number, number[]>();
    const ranks = new Map<number, number>();

    filteredNodes.forEach((n) => {
      inDegree.set(n.id, 0);
      adj.set(n.id, []);
      ranks.set(n.id, 0);
    });

    activeEdges.forEach((e) => {
      if (adj.has(e.from) && inDegree.has(e.to)) {
        adj.get(e.from)!.push(e.to);
        inDegree.set(e.to, (inDegree.get(e.to) || 0) + 1);
      }
    });

    // Kahn's longest-path DAG topological rank assignment
    const queue: number[] = [];
    filteredNodes.forEach((n) => {
      if ((inDegree.get(n.id) || 0) === 0) {
        queue.push(n.id);
        ranks.set(n.id, 0);
      }
    });

    const degCopy = new Map(inDegree);
    while (queue.length > 0) {
      const u = queue.shift()!;
      const uRank = ranks.get(u) || 0;
      for (const v of adj.get(u) || []) {
        const curVRank = ranks.get(v) || 0;
        if (uRank + 1 > curVRank) {
          ranks.set(v, uRank + 1);
        }
        degCopy.set(v, (degCopy.get(v) || 1) - 1);
        if (degCopy.get(v) === 0) {
          queue.push(v);
        }
      }
    }

    // Default any remaining unranked node
    filteredNodes.forEach((n) => {
      if (!ranks.has(n.id)) ranks.set(n.id, 0);
    });

    // Group nodes by calculated rank
    const nodesByRank = new Map<number, TopicNode[]>();
    filteredNodes.forEach((n) => {
      const r = ranks.get(n.id) || 0;
      if (!nodesByRank.has(r)) nodesByRank.set(r, []);
      nodesByRank.get(r)!.push(n);
    });

    const rankList = Array.from(nodesByRank.keys()).sort((a, b) => a - b);
    const CARD_WIDTH = 240;
    const CARD_HEIGHT = 84;
    const COL_SPACING = 340;
    const ROW_SPACING = 114;

    let maxNodesInAnyCol = 1;
    rankList.forEach((r) => {
      const count = nodesByRank.get(r)?.length || 0;
      if (count > maxNodesInAnyCol) maxNodesInAnyCol = count;
    });

    const computedWidth = Math.max(1000, rankList.length * COL_SPACING + 140);
    const computedHeight = Math.max(540, maxNodesInAnyCol * ROW_SPACING + 80);

    const positions: LayoutNode[] = [];
    rankList.forEach((r, colIdx) => {
      const colNodes = nodesByRank.get(r) || [];
      const colHeight = colNodes.length * ROW_SPACING;
      // Vertically center nodes in this rank column
      const yStart = Math.max(30, (computedHeight - colHeight) / 2);

      colNodes.forEach((node, rowIdx) => {
        positions.push({
          ...node,
          rank: r,
          x: 50 + colIdx * COL_SPACING,
          y: yStart + rowIdx * ROW_SPACING,
        });
      });
    });

    return {
      layoutNodes: positions,
      layoutEdges: activeEdges,
      canvasWidth: computedWidth,
      canvasHeight: computedHeight,
      sortedRanks: rankList,
    };
  }, [filteredNodes, activeEdges]);

  // Selected node object
  const selectedNode = useMemo(() => {
    if (!graphData?.nodes) return null;
    return graphData.nodes.find((n) => n.id === selectedNodeId) || graphData.nodes[0] || null;
  }, [graphData, selectedNodeId]);

  // Connected incoming & outgoing edge IDs for selected or hovered node
  const activeFocusNodeId = hoveredNodeId ?? selectedNodeId;
  const connectedEdgeDetails = useMemo(() => {
    if (!activeFocusNodeId || !graphData?.edges) {
      return { incomingIds: new Set<string>(), outgoingIds: new Set<string>() };
    }
    const inSet = new Set<string>();
    const outSet = new Set<string>();
    graphData.edges.forEach((e) => {
      const key = `${e.from}-${e.to}`;
      if (e.to === activeFocusNodeId) inSet.add(key);
      if (e.from === activeFocusNodeId) outSet.add(key);
    });
    return { incomingIds: inSet, outgoingIds: outSet };
  }, [activeFocusNodeId, graphData]);

  // Auto-fit graph view to container on initial load or layout change
  const handleFitView = () => {
    if (!canvasContainerRef.current) return;
    const rect = canvasContainerRef.current.getBoundingClientRect();
    const scaleX = (rect.width - 60) / canvasWidth;
    const scaleY = (rect.height - 60) / canvasHeight;
    const fitScale = Math.min(1.2, Math.max(0.4, Math.min(scaleX, scaleY)));
    setZoom(fitScale);
    const offsetX = Math.max(20, (rect.width - canvasWidth * fitScale) / 2);
    const offsetY = Math.max(20, (rect.height - canvasHeight * fitScale) / 2);
    setPan({ x: offsetX, y: offsetY });
  };

  useEffect(() => {
    if (layoutNodes.length > 0) {
      // Small timeout to allow container render
      const timer = setTimeout(handleFitView, 100);
      return () => clearTimeout(timer);
    }
  }, [layoutNodes.length, filterChapterId, isExpanded]);

  // Mouse pan event handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left click
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom((prev) => Math.min(1.8, Math.max(0.35, prev * zoomFactor)));
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-4 md:px-8 pt-24 pb-16 space-y-10">
      {/* Page Title */}
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
        <div className="space-y-1.5 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#D4211C] bg-red-100/80 px-2.5 py-0.5 rounded-full border border-red-200">
              Bayesian Knowledge Tracing (BKT) Engine
            </span>
            <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-300">
              Verified DAG
            </span>
          </div>

          <h2 className="font-display text-3xl text-[#1A1210]">
            {t("progressMasteryLevel")}: {overallMastery}%
          </h2>

          <p className="text-sm text-[#63524C]">
            {hasNodes
              ? `Live cognitive estimate calculated across ${graphData?.nodes.length} curriculum concepts & ${graphData?.edges.length} prerequisite dependency edges.`
              : "No course concepts ingested yet. Upload materials in your Library to begin tracking cognitive mastery."}
          </p>

          {/* Quick Stats Pill Row */}
          {hasNodes && (
            <div className="pt-2 flex flex-wrap items-center justify-center md:justify-start gap-2 text-xs font-bold">
              <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-900 border border-emerald-300">
                {masteryStats.mastered} Mastered (&ge;85%)
              </span>
              <span className="px-3 py-1 rounded-full bg-amber-50 text-amber-900 border border-amber-300">
                {masteryStats.inProgress} In Progress (50&ndash;84%)
              </span>
              <span className="px-3 py-1 rounded-full bg-red-50 text-red-900 border border-red-300">
                {masteryStats.needsReview} Unexplored / Needs Review (&lt;50%)
              </span>
            </div>
          )}
        </div>

        {/* Big Circular Metric */}
        <div className="relative w-28 h-28 flex items-center justify-center shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" stroke="#FAF4E4" strokeWidth="10" fill="none" />
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

      {/* MAIN CURRICULUM SECTION */}
      <div className="space-y-4">
        {/* View Switcher & Chapter Controls Bar */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 px-2">
          {/* View Mode Tabs */}
          <div className="inline-flex rounded-2xl bg-[#1A1210]/80 p-1.5 border border-[#E2A63A]/50 shadow-md">
            <button
              onClick={() => setViewTab("dag")}
              className={`px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition-all flex items-center gap-2 ${
                viewTab === "dag"
                  ? "bg-[#FAF4E4] text-[#1A1210] shadow-sm"
                  : "text-[#F7EDCF] hover:text-white"
              }`}
            >
              <span>☍</span>
              <span>Interactive DAG Graph</span>
            </button>
            <button
              onClick={() => setViewTab("roadmap")}
              className={`px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition-all flex items-center gap-2 ${
                viewTab === "roadmap"
                  ? "bg-[#FAF4E4] text-[#1A1210] shadow-sm"
                  : "text-[#F7EDCF] hover:text-white"
              }`}
            >
              <span>🗺️</span>
              <span>Topological Roadmap</span>
            </button>
            <button
              onClick={() => setViewTab("chapters")}
              className={`px-4 py-2 rounded-xl text-xs md:text-sm font-bold transition-all flex items-center gap-2 ${
                viewTab === "chapters"
                  ? "bg-[#FAF4E4] text-[#1A1210] shadow-sm"
                  : "text-[#F7EDCF] hover:text-white"
              }`}
            >
              <span>📚</span>
              <span>Chapter Hierarchy</span>
            </button>
          </div>

          {/* Legend */}
          {hasNodes && (
            <div className="flex flex-wrap items-center gap-3 text-xs text-[#F7EDCF] bg-[#1A1210]/60 px-4 py-2 rounded-full border border-[#E2A63A]/40 self-start lg:self-center">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                {t("progressLegendMastered")} (&ge;85%)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#E2A63A]" />
                {t("progressLegendLearning")} (50&ndash;84%)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#D4211C]" />
                {t("progressLegendUnexplored")} (&lt;50%)
              </span>
            </div>
          )}
        </div>

        {/* Chapter Filter Scope Pills (Available when in DAG or Roadmap view) */}
        {hasNodes && chapters.length > 1 && viewTab !== "chapters" && (
          <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 px-2 no-scrollbar">
            <span className="text-xs font-bold text-[#F7EDCF] uppercase tracking-wider shrink-0 mr-1">
              Chapter Filter:
            </span>
            <button
              onClick={() => setFilterChapterId("all")}
              className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all border ${
                filterChapterId === "all"
                  ? "bg-[#E2A63A] text-[#1A1210] border-[#FAF4E4] shadow-md"
                  : "bg-[#1A1210]/60 text-[#F7EDCF] border-[#E2A63A]/30 hover:bg-[#1A1210]"
              }`}
            >
              All Concepts ({graphData?.nodes.length})
            </button>
            {chapters.map((ch) => {
              const isSelected = filterChapterId === ch.id;
              // Shorten chapter title for pill
              const shortTitle = ch.name.length > 28 ? ch.name.slice(0, 26) + "..." : ch.name;
              return (
                <button
                  key={ch.id}
                  onClick={() => setFilterChapterId(ch.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all border ${
                    isSelected
                      ? "bg-[#E2A63A] text-[#1A1210] border-[#FAF4E4] shadow-md"
                      : "bg-[#1A1210]/60 text-[#F7EDCF] border-[#E2A63A]/30 hover:bg-[#1A1210]"
                  }`}
                >
                  {shortTitle}
                </button>
              );
            })}
          </div>
        )}

        {/* VIEW TAB 1: INTERACTIVE PREREQUISITE DAG GRAPH */}
        {viewTab === "dag" && (
          <>
            {hasNodes ? (
              <DoubleGoldCard size="lg" className="overflow-hidden p-3 md:p-5 relative">
                {/* Canvas Toolbar Controls */}
                <div className="absolute top-6 right-6 z-30 flex items-center gap-1.5 bg-[#1A1210]/85 backdrop-blur-md p-1.5 rounded-2xl border border-[#E2A63A]/50 shadow-xl">
                  <button
                    onClick={() => setZoom((z) => Math.min(1.8, z + 0.15))}
                    title="Zoom In"
                    className="w-8 h-8 rounded-xl bg-white/10 hover:bg-white/20 text-[#F7EDCF] flex items-center justify-center font-bold text-base transition-colors"
                  >
                    +
                  </button>
                  <button
                    onClick={() => setZoom((z) => Math.max(0.35, z - 0.15))}
                    title="Zoom Out"
                    className="w-8 h-8 rounded-xl bg-white/10 hover:bg-white/20 text-[#F7EDCF] flex items-center justify-center font-bold text-base transition-colors"
                  >
                    &minus;
                  </button>
                  <button
                    onClick={handleFitView}
                    title="Fit to Screen"
                    className="px-2.5 h-8 rounded-xl bg-white/10 hover:bg-white/20 text-[#F7EDCF] text-xs font-bold flex items-center gap-1 transition-colors"
                  >
                    <span>⛶</span>
                    <span className="hidden sm:inline">Fit</span>
                  </button>
                  <button
                    onClick={() => {
                      setZoom(1.0);
                      setPan({ x: 40, y: 30 });
                    }}
                    title="Reset Zoom to 100%"
                    className="px-2 h-8 rounded-xl bg-white/10 hover:bg-white/20 text-[#F7EDCF] text-xs font-bold transition-colors"
                  >
                    {Math.round(zoom * 100)}%
                  </button>
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    title={isExpanded ? "Collapse View" : "Expand Height"}
                    className="w-8 h-8 rounded-xl bg-[#E2A63A] hover:bg-[#FAF4E4] text-[#1A1210] flex items-center justify-center font-bold text-xs transition-colors"
                  >
                    {isExpanded ? "▲" : "▼"}
                  </button>
                </div>

                {/* Quick Hint */}
                <div className="absolute bottom-6 left-6 z-20 hidden md:flex items-center gap-2 text-[11px] font-bold text-[#63524C] bg-[#FAF4E4]/90 backdrop-blur-sm px-3 py-1.5 rounded-full border border-[#E2A63A]/40 shadow-sm pointer-events-none select-none">
                  <span>🖱️ Drag canvas to pan</span>
                  <span>•</span>
                  <span>Scroll to zoom</span>
                  <span>•</span>
                  <span>Click node for deep dive</span>
                </div>

                {/* Interactive Canvas Container */}
                <div
                  ref={canvasContainerRef}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                  onWheel={handleWheel}
                  className={`w-full rounded-2xl bg-[#FAF4E4] border border-[#E2A63A]/50 relative overflow-hidden select-none shadow-inner transition-all duration-300 ${
                    isExpanded ? "h-[720px]" : "h-[500px]"
                  } ${isDragging ? "cursor-grabbing" : "cursor-grab"}`}
                >
                  {/* Subtle Grid Background Pattern */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
                    <defs>
                      <pattern id="dag-grid" width="40" height="40" patternUnits="userSpaceOnUse">
                        <circle cx="20" cy="20" r="1.5" fill="#8C5D0D" />
                      </pattern>
                    </defs>
                    <rect width="100%" height="100%" fill="url(#dag-grid)" />
                  </svg>

                  {/* Transformed Canvas Layer */}
                  <div
                    style={{
                      transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                      transformOrigin: "0 0",
                      width: `${canvasWidth}px`,
                      height: `${canvasHeight}px`,
                      position: "relative",
                    }}
                  >
                    {/* SVG Connector Arrows Layer */}
                    <svg
                      className="absolute inset-0 pointer-events-none overflow-visible"
                      width={canvasWidth}
                      height={canvasHeight}
                    >
                      <defs>
                        {/* Standard Antique Gold Arrow */}
                        <marker
                          id="dag-arrow-default"
                          viewBox="0 0 10 10"
                          refX="14"
                          refY="5"
                          markerWidth="7"
                          markerHeight="7"
                          orient="auto-start-reverse"
                        >
                          <path d="M 0 1 L 9 5 L 0 9 z" fill="#8C5D0D" />
                        </marker>

                        {/* Incoming Prerequisite Arrow (Crimson) */}
                        <marker
                          id="dag-arrow-prereq"
                          viewBox="0 0 10 10"
                          refX="14"
                          refY="5"
                          markerWidth="8"
                          markerHeight="8"
                          orient="auto-start-reverse"
                        >
                          <path d="M 0 1 L 9 5 L 0 9 z" fill="#D4211C" />
                        </marker>

                        {/* Outgoing Dependent Arrow (Emerald) */}
                        <marker
                          id="dag-arrow-unlock"
                          viewBox="0 0 10 10"
                          refX="14"
                          refY="5"
                          markerWidth="8"
                          markerHeight="8"
                          orient="auto-start-reverse"
                        >
                          <path d="M 0 1 L 9 5 L 0 9 z" fill="#10B981" />
                        </marker>
                      </defs>

                      {/* Render Dynamic Cubic Bezier Curved Edges */}
                      {layoutEdges.map((e, idx) => {
                        const fromNode = layoutNodes.find((n) => n.id === e.from);
                        const toNode = layoutNodes.find((n) => n.id === e.to);
                        if (!fromNode || !toNode) return null;

                        const edgeKey = `${e.from}-${e.to}`;
                        const isIncomingToFocus = connectedEdgeDetails.incomingIds.has(edgeKey);
                        const isOutgoingFromFocus = connectedEdgeDetails.outgoingIds.has(edgeKey);
                        const isFocusedEdge = isIncomingToFocus || isOutgoingFromFocus;
                        const hasActiveFocus = activeFocusNodeId !== null;

                        // Start from right center of source card, connect to left center of target card
                        const CARD_WIDTH = 240;
                        const CARD_HEIGHT = 84;
                        const pFrom = { x: fromNode.x + CARD_WIDTH, y: fromNode.y + CARD_HEIGHT / 2 };
                        const pTo = { x: toNode.x, y: toNode.y + CARD_HEIGHT / 2 };

                        const dx = Math.max(50, (pTo.x - pFrom.x) * 0.45);
                        const pathD = `M ${pFrom.x} ${pFrom.y} C ${pFrom.x + dx} ${pFrom.y}, ${pTo.x - dx} ${pTo.y}, ${pTo.x} ${pTo.y}`;

                        let strokeColor = "#8C5D0D";
                        let strokeWidth = 2.0;
                        let markerUrl = "url(#dag-arrow-default)";
                        let strokeOpacity = 0.75;

                        if (isIncomingToFocus) {
                          strokeColor = "#D4211C";
                          strokeWidth = 3.5;
                          markerUrl = "url(#dag-arrow-prereq)";
                          strokeOpacity = 1.0;
                        } else if (isOutgoingFromFocus) {
                          strokeColor = "#10B981";
                          strokeWidth = 3.5;
                          markerUrl = "url(#dag-arrow-unlock)";
                          strokeOpacity = 1.0;
                        } else if (hasActiveFocus) {
                          strokeOpacity = 0.15;
                        }

                        return (
                          <g key={idx}>
                            <path
                              d={pathD}
                              stroke={strokeColor}
                              strokeWidth={strokeWidth}
                              strokeOpacity={strokeOpacity}
                              fill="none"
                              markerEnd={markerUrl}
                              className={isFocusedEdge ? "transition-all duration-300" : ""}
                            />
                          </g>
                        );
                      })}
                    </svg>

                    {/* HTML Node Cards Layered with Exact Calculated Non-Overlapping Coordinates */}
                    {layoutNodes.map((node) => {
                      const isSelected = selectedNodeId === node.id;
                      const isHovered = hoveredNodeId === node.id;
                      const isChapter = node.level === 0 || node.name.toLowerCase().startsWith("chapter");

                      const mastery = node.mastery_p ?? 0.3;
                      const statusColor =
                        mastery >= 0.85
                          ? "border-emerald-600 bg-emerald-50 text-emerald-950"
                          : mastery >= 0.5
                          ? "border-[#E2A63A] bg-amber-50 text-amber-950"
                          : "border-[#D4211C] bg-red-50 text-red-950";

                      const isPrereqParent = selectedNode?.prerequisites.includes(node.id);

                      return (
                        <div
                          key={node.id}
                          onClick={() => setSelectedNodeId(node.id)}
                          onMouseEnter={() => setHoveredNodeId(node.id)}
                          onMouseLeave={() => setHoveredNodeId(null)}
                          className={`absolute p-3 rounded-2xl border-2 transition-all flex flex-col justify-between shadow-md hover:scale-[1.03] hover:z-30 cursor-pointer ${statusColor} ${
                            isSelected
                              ? "ring-4 ring-[#1A1210] scale-[1.03] z-20 shadow-xl"
                              : isPrereqParent
                              ? "ring-2 ring-[#D4211C] ring-dashed"
                              : ""
                          }`}
                          style={{
                            left: `${node.x}px`,
                            top: `${node.y}px`,
                            width: "240px",
                            height: "84px",
                          }}
                        >
                          {/* Top Row: Level & Mastery */}
                          <div className="flex items-center justify-between w-full">
                            <span
                              className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                                isChapter
                                  ? "bg-[#1A1210] text-[#E2A63A]"
                                  : "bg-[#1A1210]/15 text-[#1A1210]"
                              }`}
                            >
                              {isChapter ? "Domain / Chapter" : `Concept (L${node.level})`}
                            </span>
                            <span
                              className={`text-[11px] font-extrabold px-1.5 py-0.5 rounded ${
                                mastery >= 0.85
                                  ? "text-emerald-800 bg-emerald-100"
                                  : mastery >= 0.5
                                  ? "text-amber-800 bg-amber-100"
                                  : "text-red-800 bg-red-100"
                              }`}
                            >
                              {Math.round(mastery * 100)}%
                            </span>
                          </div>

                          {/* Middle: Title */}
                          <div className="my-auto">
                            <span
                              className="text-xs font-bold leading-snug line-clamp-2 block text-left"
                              title={node.name}
                            >
                              {lang === "hi" && node.name_hi ? node.name_hi : node.name}
                            </span>
                          </div>

                          {/* Bottom Row: Prereq Count */}
                          <div className="flex items-center justify-between text-[10px] text-[#63524C] font-semibold border-t border-black/10 pt-1">
                            <span>
                              {node.prerequisites.length === 0
                                ? "Foundational Root"
                                : `${node.prerequisites.length} Prerequisite${
                                    node.prerequisites.length > 1 ? "s" : ""
                                  }`}
                            </span>
                            <span className="opacity-70">Rank {node.rank}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Selected Concept Deep Dive Drawer */}
                {selectedNode && (
                  <div className="mt-4 p-5 rounded-2xl bg-white border border-[#E2A63A]/50 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-5 animate-in fade-in duration-200">
                    <div className="space-y-2 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2.5 py-0.5 rounded-full bg-[#1A1210] text-[#F7EDCF] text-xs font-bold">
                          {selectedNode.level === 0 ? "Chapter / Domain" : `Level ${selectedNode.level} Concept`}
                        </span>

                        <span className="text-xs font-bold text-[#8C5D0D] bg-[#FAF4E4] px-2.5 py-0.5 rounded-full border border-[#E2A63A]/40">
                          Prerequisites (Required Before):{" "}
                          {selectedNode.prerequisites && selectedNode.prerequisites.length > 0 ? (
                            selectedNode.prerequisites
                              .map((pid) => graphData?.nodes.find((n) => n.id === pid)?.name || `Concept #${pid}`)
                              .join(", ")
                          ) : (
                            <span className="text-emerald-700">None (Foundational Entrypoint)</span>
                          )}
                        </span>
                      </div>

                      <h3 className="font-bold text-xl text-[#1A1210]">
                        {selectedNode.name}
                      </h3>

                      <p className="text-sm text-[#63524C] leading-relaxed">
                        {selectedNode.summary}
                      </p>
                    </div>

                    <div className="flex items-center gap-4 shrink-0 self-stretch md:self-center justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-stone-200">
                      <div className="text-right">
                        <span className="block text-2xl font-bold text-[#D4211C]">
                          {Math.round((selectedNode.mastery_p ?? 0.3) * 100)}%
                        </span>
                        <span className="text-[11px] text-[#63524C] font-semibold">
                          Stability: {selectedNode.stability_days ?? 7}d
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <Link
                          href="/practice"
                          className="btn-primary-pill text-xs py-2 px-4 shadow-md flex items-center gap-1.5"
                        >
                          <span>Practice Concept</span>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <line x1="5" y1="12" x2="19" y2="12" />
                            <polyline points="12 5 19 12 12 19" />
                          </svg>
                        </Link>
                      </div>
                    </div>
                  </div>
                )}
              </DoubleGoldCard>
            ) : (
              /* EMPTY STATE CARD WHEN DATABASE HAS ZERO CONCEPTS */
              <DoubleGoldCard size="lg" className="p-8 md:p-12 text-center">
                <div className="max-w-md mx-auto space-y-4">
                  <div className="w-16 h-16 rounded-full bg-[#1A1210] text-[#E2A63A] flex items-center justify-center mx-auto shadow-lg border border-[#E2A63A]/40">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                    </svg>
                  </div>

                  <h3 className="font-display text-2xl md:text-3xl text-[#1A1210]">
                    No Curriculum Concepts Mapped Yet
                  </h3>

                  <p className="text-sm text-[#63524C] leading-relaxed">
                    Your database is fresh. Upload your course textbook (PDF), lecture slides (PPTX), or notes in the <strong>Library</strong>, then click <strong>Build Knowledge Graph</strong> to automatically extract concept nodes and prerequisite dependency arrows!
                  </p>

                  <div className="pt-2">
                    <Link
                      href="/library"
                      className="btn-primary-pill text-sm py-2.5 px-6 shadow-xl inline-flex items-center gap-2"
                    >
                      <span>Go to Library & Upload Materials</span>
                      <span>→</span>
                    </Link>
                  </div>
                </div>
              </DoubleGoldCard>
            )}
          </>
        )}

        {/* VIEW TAB 2: TOPOLOGICAL LEARNING ROADMAP (STEP-BY-STEP ORDER) */}
        {viewTab === "roadmap" && (
          <DoubleGoldCard size="lg" className="p-6 md:p-8 space-y-8">
            <div className="space-y-1">
              <h3 className="font-display text-2xl text-[#1A1210]">
                Curriculum Progression Roadmap (Topological Order)
              </h3>
              <p className="text-sm text-[#63524C]">
                Concepts sequenced according to prerequisite dependency constraints. Master earlier foundational stages to unlock advanced topics!
              </p>
            </div>

            <div className="space-y-6">
              {sortedRanks.map((rank) => {
                const rankNodes = layoutNodes.filter((n) => n.rank === rank);
                if (rankNodes.length === 0) return null;

                const stageTitle =
                  rank === 0
                    ? "Stage 1: Foundational Roots & Core Introductions"
                    : rank === 1
                    ? "Stage 2: Mathematical Tools & Initial Principles"
                    : rank === 2
                    ? "Stage 3: Data Architecture, Probability & Calculus"
                    : rank === 3
                    ? "Stage 4: Core Optimization, Features & Baseline Models"
                    : rank === 4
                    ? "Stage 5: Algorithmic Training, Descent & Preprocessing"
                    : `Stage ${rank + 1}: Model Evaluation, Solutions & Mastery`;

                return (
                  <div key={rank} className="p-5 rounded-2xl bg-white border border-[#E2A63A]/40 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-stone-200 pb-3">
                      <div className="flex items-center gap-2">
                        <span className="w-7 h-7 rounded-full bg-[#1A1210] text-[#E2A63A] text-xs font-bold flex items-center justify-center">
                          {rank + 1}
                        </span>
                        <h4 className="font-bold text-base text-[#1A1210]">{stageTitle}</h4>
                      </div>
                      <span className="text-xs font-bold text-[#8C5D0D] bg-[#FAF4E4] px-3 py-1 rounded-full border border-[#E2A63A]/30">
                        {rankNodes.length} Concepts in Stage
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {rankNodes.map((n) => {
                        const m = n.mastery_p ?? 0.3;
                        return (
                          <div
                            key={n.id}
                            className="p-4 rounded-xl bg-[#FAF4E4]/50 border border-[#E2A63A]/30 flex flex-col justify-between gap-3 hover:border-[#E2A63A] transition-all"
                          >
                            <div className="space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-[#8C5D0D]">
                                  {n.level === 0 ? "Chapter" : `Level ${n.level}`}
                                </span>
                                <span
                                  className={`text-xs font-bold ${
                                    m >= 0.85
                                      ? "text-emerald-700"
                                      : m >= 0.5
                                      ? "text-amber-700"
                                      : "text-red-700"
                                  }`}
                                >
                                  {Math.round(m * 100)}% Mastery
                                </span>
                              </div>
                              <h5 className="font-bold text-sm text-[#1A1210]">{n.name}</h5>
                              <p className="text-xs text-[#63524C] line-clamp-2">{n.summary}</p>
                            </div>

                            <div className="pt-2 border-t border-stone-200/60 flex items-center justify-between">
                              <span className="text-[11px] text-[#63524C]">
                                {n.prerequisites.length === 0
                                  ? "No prereqs required"
                                  : `${n.prerequisites.length} prereqs`}
                              </span>
                              <Link
                                href="/practice"
                                className="text-xs font-bold text-[#D4211C] hover:underline flex items-center gap-1"
                              >
                                <span>Practice</span>
                                <span>→</span>
                              </Link>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </DoubleGoldCard>
        )}

        {/* VIEW TAB 3: CHAPTER HIERARCHY ACCORDION */}
        {viewTab === "chapters" && (
          <DoubleGoldCard size="lg" className="p-6 md:p-8 space-y-6">
            <div className="space-y-1">
              <h3 className="font-display text-2xl text-[#1A1210]">
                Curriculum Chapter Breakdown
              </h3>
              <p className="text-sm text-[#63524C]">
                Explore concepts organized hierarchically under each domain chapter.
              </p>
            </div>

            <div className="space-y-4">
              {chapters.map((ch, idx) => {
                const children = graphData?.nodes.filter((n) => n.parent_id === ch.id) || [];
                const avgMastery =
                  children.length > 0
                    ? Math.round(
                        (children.reduce((acc, c) => acc + (c.mastery_p ?? 0.3), 0) / children.length) * 100
                      )
                    : Math.round((ch.mastery_p ?? 0.3) * 100);

                return (
                  <div key={ch.id} className="p-5 rounded-2xl bg-white border border-[#E2A63A]/40 shadow-sm space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-stone-200 pb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded-full bg-[#1A1210] text-[#E2A63A] text-xs font-bold uppercase tracking-wider">
                            Chapter {idx + 1}
                          </span>
                          <span className="text-xs font-bold text-[#63524C]">
                            {children.length} Concepts
                          </span>
                        </div>
                        <h4 className="font-bold text-lg text-[#1A1210] mt-1">{ch.name}</h4>
                        <p className="text-xs text-[#63524C] mt-0.5">{ch.summary}</p>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        <div className="text-right">
                          <span className="block text-xl font-bold text-[#D4211C]">{avgMastery}%</span>
                          <span className="text-[10px] text-[#63524C] font-semibold">Avg Mastery</span>
                        </div>
                        <button
                          onClick={() => {
                            setFilterChapterId(ch.id);
                            setViewTab("dag");
                          }}
                          className="btn-primary-pill text-xs py-1.5 px-3.5 shadow-sm"
                        >
                          View DAG Subgraph
                        </button>
                      </div>
                    </div>

                    {/* Children Concepts Grid */}
                    {children.length > 0 && (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
                        {children.map((child) => {
                          const cm = child.mastery_p ?? 0.3;
                          return (
                            <div
                              key={child.id}
                              onClick={() => {
                                setSelectedNodeId(child.id);
                                setViewTab("dag");
                              }}
                              className="p-3 rounded-xl bg-[#FAF4E4]/60 border border-[#E2A63A]/30 hover:border-[#E2A63A] hover:bg-[#FAF4E4] transition-all cursor-pointer flex flex-col justify-between"
                            >
                              <div className="space-y-1">
                                <div className="flex items-center justify-between">
                                  <span className="text-[10px] font-bold text-[#8C5D0D]">Level {child.level}</span>
                                  <span className="text-[11px] font-bold text-emerald-800">
                                    {Math.round(cm * 100)}%
                                  </span>
                                </div>
                                <h6 className="font-bold text-xs text-[#1A1210]">{child.name}</h6>
                                <p className="text-[11px] text-[#63524C] line-clamp-2">{child.summary}</p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </DoubleGoldCard>
        )}
      </div>

      <GreekKeyDivider />
    </div>
  );
}
