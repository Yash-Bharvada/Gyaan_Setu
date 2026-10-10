"use client";

import React from "react";

interface DoubleGoldCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export const DoubleGoldCard: React.FC<DoubleGoldCardProps> = ({
  children,
  className = "",
  size = "md",
  ...props
}) => {
  const radiusClass =
    size === "sm"
      ? "rounded-[20px]"
      : size === "lg"
      ? "rounded-[32px]"
      : "rounded-[24px]";

  const shadowStyle =
    size === "sm"
      ? {
          boxShadow:
            "0 0 0 2px #E2A63A, 0 0 0 6px #F7EDCF, 0 0 0 8px #E2A63A, 0 10px 24px rgba(26, 18, 16, 0.3)",
        }
      : {
          boxShadow:
            "0 0 0 3px #E2A63A, 0 0 0 9px #F7EDCF, 0 0 0 12px #E2A63A, 0 18px 40px rgba(26, 18, 16, 0.35)",
        };

  return (
    <div
      className={`relative bg-[#F7EDCF] text-[#1A1210] p-6 md:p-8 transition-all ${radiusClass} ${className}`}
      style={shadowStyle}
      {...props}
    >
      {children}
    </div>
  );
};
