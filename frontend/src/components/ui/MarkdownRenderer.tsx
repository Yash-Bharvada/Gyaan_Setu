"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  onCitationClick?: (citationText: string) => void;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = "",
  onCitationClick,
}) => {
  return (
    <div className={`markdown-body space-y-3 leading-relaxed text-[#1A1210] ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="font-display text-2xl md:text-3xl text-[#1A1210] mt-4 mb-2 pb-1 border-b border-[#E2A63A]/40">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="font-display text-xl md:text-2xl text-[#1A1210] mt-3 mb-2">
              {children}
            </h2>
          ),
          h3: ({ children }) => {
            const text = String(children);
            const isQuickCheck =
              text.toLowerCase().includes("quick check") ||
              text.toLowerCase().includes("reflection") ||
              text.includes("💡");

            if (isQuickCheck) {
              return (
                <div className="mt-4 mb-2 flex items-center gap-2 p-2.5 rounded-xl bg-gradient-to-r from-[#FAF4E4] to-[#F7EDCF] border border-[#E2A63A] shadow-sm">
                  <span className="text-xl">💡</span>
                  <span className="font-display text-lg font-bold text-[#8C5D0D]">
                    {children}
                  </span>
                </div>
              );
            }
            return (
              <h3 className="font-bold text-lg text-[#1A1210] mt-3 mb-1">
                {children}
              </h3>
            );
          },
          h4: ({ children }) => (
            <h4 className="font-bold text-base text-[#8C5D0D] mt-2 mb-1">
              {children}
            </h4>
          ),
          p: ({ children }) => (
            <p className="text-[15px] md:text-base leading-relaxed text-[#2D211D]">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-[#1A1210]">
              {children}
            </strong>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-5 space-y-1.5 my-2 marker:text-[#8C5D0D]">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 space-y-1.5 my-2 marker:font-bold marker:text-[#8C5D0D]">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-[15px] leading-relaxed text-[#2D211D]">
              {children}
            </li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="my-3 pl-4 py-2 border-l-4 border-[#E2A63A] bg-[#FAF4E4]/90 rounded-r-xl italic text-[#4A3B32]">
              {children}
            </blockquote>
          ),
          hr: () => (
            <hr className="my-4 border-t-2 border-[#E2A63A]/30" />
          ),
          code: ({ children, className }) => {
            const isBlock = className && className.includes("language-");
            if (isBlock) {
              return (
                <pre className="my-3 p-3 rounded-xl bg-[#1A1210] text-[#F7EDCF] font-mono text-xs overflow-x-auto border border-[#E2A63A]/40">
                  <code>{children}</code>
                </pre>
              );
            }
            return (
              <code className="px-1.5 py-0.5 rounded bg-[#FAF4E4] border border-[#E2A63A]/40 text-[#8C5D0D] font-mono text-xs font-semibold">
                {children}
              </code>
            );
          },
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#D4211C] hover:underline font-semibold"
            >
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
