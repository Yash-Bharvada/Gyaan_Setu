"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { GreekKeyDivider } from "@/components/ui/GreekKeyDivider";
import { useI18n } from "@/lib/i18n";
import { apiClient, HealthStatus } from "@/lib/api";

export const Footer: React.FC = () => {
  const { t } = useI18n();
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    apiClient.getHealth().then(setHealth).catch(() => {});
  }, []);

  return (
    <footer className="w-full mt-24 pb-14 px-6 md:px-12 text-[#F7EDCF] relative z-20">
      <div className="max-w-6xl mx-auto">
        <GreekKeyDivider />

        <div className="flex flex-col md:flex-row items-center justify-between gap-6 py-6 text-center md:text-left">
          {/* Brand Info */}
          <div>
            <h2 className="font-display text-3xl md:text-4xl text-[#F7EDCF] tracking-wide mb-1">
              {t("brandName")}
            </h2>
            <p className="text-sm text-[#F7EDCF]/80 max-w-md">
              {t("heroHeadline")}
            </p>
          </div>

          {/* Quick Links */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm font-bold">
            <Link href="/library" className="hover:text-[#E2A63A] transition-colors">
              {t("navLibrary")}
            </Link>
            <Link href="/tutor" className="hover:text-[#E2A63A] transition-colors">
              {t("navTutor")}
            </Link>
            <Link href="/practice" className="hover:text-[#E2A63A] transition-colors">
              {t("navPractice")}
            </Link>
            <Link href="/revise" className="hover:text-[#E2A63A] transition-colors">
              {t("navRevise")}
            </Link>
            <Link href="/progress" className="hover:text-[#E2A63A] transition-colors">
              {t("navProgress")}
            </Link>
          </div>

          {/* Backend Status Indicator */}
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1A1210]/60 border border-[#E2A63A]/40 text-xs">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                health?.status === "ok" ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            <span className="text-[#F7EDCF]/90 font-medium">
              {health?.status === "ok" ? t("backendConnected") : t("backendOfflineMock")}
            </span>
          </div>
        </div>

        <div className="border-t border-[#E2A63A]/20 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#F7EDCF]/60">
          <p>{t("footerCopyright")}</p>
          <p className="text-right">
            FastAPI Backend • Vector RAG • Bayesian Knowledge Tracing • Offline Fallback
          </p>
        </div>
      </div>
    </footer>
  );
};
