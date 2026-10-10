"use client";

import React from "react";
import Image from "next/image";
import { useHeroPast } from "@/lib/useHeroPast";

export const OrnateFrame: React.FC = () => {
  const heroPast = useHeroPast();

  return (
    <div
      className={`fixed inset-0 pointer-events-none z-40 select-none overflow-hidden transition-all duration-700 ease-out ${
        heroPast ? "opacity-100 visible" : "opacity-0 invisible"
      }`}
      aria-hidden="true"
    >
      {/* 3px Inner Gold Frame Inset 18px */}
      <div
        className="absolute inset-[10px] md:inset-[18px] border-[2px] md:border-[3px] border-[#E2A63A] rounded-[8px] pointer-events-none"
        style={{
          boxShadow: "inset 0 0 12px rgba(226, 166, 58, 0.25), 0 0 16px rgba(0, 0, 0, 0.4)",
        }}
      />

      {/* Top-Left Corner Gold Ornament */}
      <div className="absolute top-[6px] left-[6px] md:top-[12px] md:left-[12px] w-[110px] h-[110px] md:w-[210px] md:h-[210px] lg:w-[230px] lg:h-[230px] pointer-events-none opacity-90 transition-opacity">
        <Image
          src="/corner_gold.png"
          alt=""
          width={230}
          height={230}
          className="w-full h-full object-contain filter drop-shadow-[0_4px_8px_rgba(0,0,0,0.4)]"
          priority
        />
      </div>

      {/* Top-Right Corner Gold Ornament (Mirrored Horizontally) */}
      <div className="absolute top-[6px] right-[6px] md:top-[12px] md:right-[12px] w-[110px] h-[110px] md:w-[210px] md:h-[210px] lg:w-[230px] lg:h-[230px] pointer-events-none opacity-90 transition-opacity">
        <Image
          src="/corner_gold.png"
          alt=""
          width={230}
          height={230}
          className="w-full h-full object-contain filter drop-shadow-[0_4px_8px_rgba(0,0,0,0.4)]"
          style={{ transform: "scaleX(-1)" }}
          priority
        />
      </div>

      {/* Bottom-Left Corner Gold Ornament (Mirrored Vertically) */}
      <div className="absolute bottom-[6px] left-[6px] md:bottom-[12px] md:left-[12px] w-[110px] h-[110px] md:w-[210px] md:h-[210px] lg:w-[230px] lg:h-[230px] pointer-events-none opacity-90 transition-opacity">
        <Image
          src="/corner_gold.png"
          alt=""
          width={230}
          height={230}
          className="w-full h-full object-contain filter drop-shadow-[0_4px_8px_rgba(0,0,0,0.4)]"
          style={{ transform: "scaleY(-1)" }}
          priority
        />
      </div>

      {/* Bottom-Right Corner Gold Ornament (Mirrored Both Axes) */}
      <div className="absolute bottom-[6px] right-[6px] md:bottom-[12px] md:right-[12px] w-[110px] h-[110px] md:w-[210px] md:h-[210px] lg:w-[230px] lg:h-[230px] pointer-events-none opacity-90 transition-opacity">
        <Image
          src="/corner_gold.png"
          alt=""
          width={230}
          height={230}
          className="w-full h-full object-contain filter drop-shadow-[0_4px_8px_rgba(0,0,0,0.4)]"
          style={{ transform: "scale(-1, -1)" }}
          priority
        />
      </div>
    </div>
  );
};
