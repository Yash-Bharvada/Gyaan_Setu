"use client";

import React from "react";

interface GreekKeyDividerProps {
  className?: string;
  width?: string;
}

export const GreekKeyDivider: React.FC<GreekKeyDividerProps> = ({
  className = "",
}) => {
  return (
    <div
      className={`w-full flex items-center justify-center my-6 md:my-8 opacity-85 select-none ${className}`}
      aria-hidden="true"
    >
      <div className="flex-1 h-[2px] bg-gradient-to-r from-transparent via-[#E2A63A] to-[#E2A63A] opacity-70" />
      <div className="px-3 flex items-center gap-1">
        {/* Greek-Key Meander Motifs */}
        <svg
          width="120"
          height="18"
          viewBox="0 0 120 18"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="text-[#E2A63A]"
        >
          <path
            d="M2 9H16V2H26V16H6V6H12V12H20M30 9H44V2H54V16H34V6H40V12H48M58 9H72V2H82V16H62V6H68V12H76M86 9H100V2H110V16H90V6H96V12H104"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="square"
            strokeLinejoin="miter"
          />
        </svg>
      </div>
      <div className="flex-1 h-[2px] bg-gradient-to-l from-transparent via-[#E2A63A] to-[#E2A63A] opacity-70" />
    </div>
  );
};
