import type { Metadata } from "next";
import { Kaushan_Script, Mukta } from "next/font/google";
import "./globals.css";
import "@/tokens.css";
import { I18nProvider } from "@/lib/i18n";
import { OrnateFrame } from "@/components/layout/OrnateFrame";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

const kaushanScript = Kaushan_Script({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-kaushan",
  display: "swap",
});

const mukta = Mukta({
  weight: ["400", "600", "700"],
  subsets: ["latin", "devanagari"],
  variable: "--font-mukta",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Gyaan Setu — Personalized Tutoring & Adaptive Learning",
  description:
    "Learn from your own books, slides and lectures. Source-grounded AI companion with verifiable citations, prerequisite knowledge graphs, and adaptive mastery.",
  keywords: [
    "Gyaan Setu",
    "AI Tutor",
    "Adaptive Learning",
    "Bayesian Knowledge Tracing",
    "Spaced Repetition",
    "Grounded RAG",
    "Hindi EdTech",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${kaushanScript.variable} ${mukta.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#D4211C] text-[#F7EDCF] selection:bg-[#F7EDCF] selection:text-[#1A1210] overflow-x-hidden relative">
        <I18nProvider>
          {/* Outer Gold Frame & 4 Corner Ornaments */}
          <OrnateFrame />

          {/* Sticky Header Nav */}
          <Navbar />

          {/* Main Route Content */}
          <main className="flex-1 w-full relative z-10">
            {children}
          </main>

          {/* Global Thematic Footer */}
          <Footer />
        </I18nProvider>
      </body>
    </html>
  );
}
