"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type Language = "en" | "hi";

interface TranslationDictionary {
  [key: string]: {
    en: string;
    hi: string;
  };
}

export const translations: TranslationDictionary = {
  // Brand
  brandName: { en: "Gyaan Setu", hi: "ज्ञान सेतु" },
  brandTagline: {
    en: "Personalized Tutoring & Adaptive Learning",
    hi: "व्यक्तिगत शिक्षण एवं अनुकूलित ज्ञान सेतु",
  },

  // Navigation
  navHome: { en: "Home", hi: "होम" },
  navLibrary: { en: "Library", hi: "पुस्तकालय" },
  navTutor: { en: "Tutor", hi: "गुरुजी" },
  navPractice: { en: "Practice", hi: "अभ्यास" },
  navRevise: { en: "Revise", hi: "पुनरावृत्ति" },
  navProgress: { en: "Progress", hi: "प्रगति" },

  // CTAs
  btnStartLearning: { en: "Start learning", hi: "सीखना शुरू करें" },
  btnUploadMaterial: { en: "Upload study material", hi: "अध्ययन सामग्री अपलोड करें" },
  btnAskTutor: { en: "Ask the tutor", hi: "गुरुजी से पूछें" },
  btnGenerateQuiz: { en: "Generate Adaptive Quiz", hi: "अनुकूली प्रश्नोत्तरी बनाएं" },
  btnStartRevision: { en: "Start Flashcards", hi: "फ्लैशकार्ड शुरू करें" },
  btnViewProgress: { en: "View Knowledge Map", hi: "ज्ञान मानचित्र देखें" },

  // Home Hero
  heroHeadline: {
    en: "Learn from your own books, slides and lectures.",
    hi: "अपनी पुस्तकों, स्लाइड्स और व्याख्यानों से सीखें।",
  },
  heroSubtitle: {
    en: "An AI companion that organizes your course materials into prerequisite knowledge graphs, answers queries with verifiable source citations, tracks mastery via Bayesian Knowledge Tracing, and builds personal revision schedules.",
    hi: "एक बौद्धिक साथी जो आपकी पाठ्यपुस्तकों को ज्ञान आरेख में व्यवस्थित करता है, पृष्ठ-दर-पृष्ठ सटीक संदर्भों के साथ उत्तर देता है, और वैज्ञानिक पुनरावृत्ति योजनाएं बनाता है।",
  },
  heroBadge: {
    en: "100% Free-Tier & Local-Stack Architecture",
    hi: "100% निःशुल्क एवं सुरक्षित स्थानीय तकनीक",
  },

  // Features Overview
  featLibraryTitle: { en: "Multimodal Library", hi: "मल्टीमॉडल पुस्तकालय" },
  featLibraryDesc: {
    en: "Ingest textbooks (PDF), lecture slides (PPTX), and video recordings down to precise page, slide, and timestamp units.",
    hi: "PDF पुस्तकें, PPTX स्लाइड्स और वीडियो व्याख्यानों को पृष्ठों, स्लाइडों और समय-चिह्नों के साथ संगृहीत करें।",
  },
  featTutorTitle: { en: "Grounded AI Tutor", hi: "संदर्भित एआई गुरुजी" },
  featTutorDesc: {
    en: "Every explanation cites exact page numbers and timestamps. Strict relevance gating prevents hallucinations and refuses out-of-scope questions.",
    hi: "प्रत्येक उत्तर आपकी ही पुस्तक के सटीक पृष्ठ का संदर्भ देता है। पाठ्यक्रम से बाहर के प्रश्नों पर स्पष्ट अस्वीकृति।",
  },
  featPracticeTitle: { en: "Adaptive Practice", hi: "अनुकूली अभ्यास" },
  featPracticeDesc: {
    en: "Target your learning frontier with Bloom's taxonomy assessments, cross-model verification, and rubric-based automatic grading.",
    hi: "ब्लूम्स वर्गीकरण आधारित प्रश्न, क्रॉस-मॉडल सत्यापन और रूब्रिक-आधारित स्वचालित मूल्यांकन।",
  },
  featReviseTitle: { en: "Spaced Revision", hi: "स्मरण पुनरावृत्ति" },
  featReviseDesc: {
    en: "Active-recall flashcards powered by SM-2 and FSRS algorithms, cheat-sheet slide summaries, and 5-minute audio briefs.",
    hi: "SM-2 एवं FSRS एल्गोरिद्म आधारित फ्लैशकार्ड्स, सार संक्षेप स्लाइड्स, और 5-मिनट ऑडियो सारांश।",
  },
  featProgressTitle: { en: "Knowledge Map", hi: "ज्ञान आरेख व प्रगति" },
  featProgressDesc: {
    en: "Explore your course as an interactive prerequisite DAG with Bayesian Knowledge Tracing (BKT) and forgetting curve predictions.",
    hi: "बायेशियन नॉलेज ट्रेसिंग (BKT) और विस्मरण वक्र (Forgetting Curve) के साथ पाठ्यक्रम का संवादात्मक ज्ञान मानचित्र।",
  },

  // Library Screen
  libTitle: { en: "Study Material Library", hi: "अध्ययन सामग्री पुस्तकालय" },
  libSubtitle: {
    en: "Upload PDFs, slide presentations, lecture videos, or handwritten notes. All content is indexed into verifiable units.",
    hi: "PDF, प्रेजेंटेशन स्लाइड्स, वीडियो व्याख्यान अथवा हस्तलिखित नोट्स अपलोड करें।",
  },
  libDropzoneTitle: { en: "Drag & drop study files here", hi: "अध्ययन सामग्री यहाँ खींचें और छोड़ें" },
  libDropzoneHint: {
    en: "Supports PDF (Textbooks/Papers), PPTX (Slide Decks), MP4 (Lecture Videos), PNG/JPG (Diagrams)",
    hi: "समर्थित: PDF (पुस्तकें), PPTX (स्लाइड्स), MP4 (वीडियो), PNG/JPG (चित्र)",
  },
  libBrowseBtn: { en: "Or browse files on your computer", hi: "अथवा अपने कंप्यूटर से फ़ाइल चुनें" },
  libActiveJobs: { en: "Active Ingestion Jobs", hi: "सक्रिय प्रसंस्करण कार्य" },
  libSourcesList: { en: "Indexed Course Materials", hi: "अनुक्रमित पाठ्यक्रम सामग्री" },
  libUnitsExtracted: { en: "Units Extracted", hi: "निकाले गए संदर्भ खंड" },
  libPages: { en: "Pages", hi: "पृष्ठ" },
  libSlides: { en: "Slides", hi: "स्लाइड्स" },
  libDuration: { en: "Duration", hi: "अवधि" },

  // Tutor Screen
  tutorTitle: { en: "Grounded AI Tutor", hi: "संदर्भित एआई गुरुजी" },
  tutorSubtitle: {
    en: "Direct answers verified against your course materials. Click citation chips to inspect the original source excerpt.",
    hi: "आपकी सामग्री से सत्यापित प्रत्यक्ष उत्तर। मूल पुस्तक पृष्ठ देखने के लिए संदर्भ चिप पर क्लिक करें।",
  },
  tutorInputPlaceholder: {
    en: "Ask a question about your uploaded materials...",
    hi: "अपनी अपलोड की गई सामग्री के बारे में कोई प्रश्न पूछें...",
  },
  tutorSend: { en: "Ask", hi: "पूछें" },
  tutorVoiceHold: { en: "Hold for voice", hi: "ध्वनि के लिए दबाएं" },
  tutorScopeLabel: { en: "Curriculum Scope:", hi: "अध्ययन दायरा:" },
  tutorScopeAll: { en: "All Uploaded Materials", hi: "सभी अपलोड की गई सामग्री" },
  tutorGroundedBadge: { en: "Source Grounded", hi: "प्रामाणिक स्रोत" },
  tutorInspectSource: { en: "Inspect Source Unit", hi: "मूल संदर्भ देखें" },
  tutorRefusalTitle: { en: "Out-of-Scope Query", hi: "पाठ्यक्रम से बाहर का प्रश्न" },
  tutorRefusalMsg: {
    en: "This question cannot be answered from your uploaded materials. Gyaan Setu strictly refuses ungrounded answers to prevent hallucinations.",
    hi: "यह प्रश्न आपकी अपलोड की गई सामग्री में उपलब्ध नहीं है। गलत जानकारी रोकने के लिए ज्ञान सेतु केवल प्रामाणिक सामग्री से उत्तर देता है।",
  },

  // Practice Screen
  practiceTitle: { en: "Adaptive Practice Engine", hi: "अनुकूली अभ्यास प्रणाली" },
  practiceSubtitle: {
    en: "Auto-generated questions targeted at your mastery frontier. Verified by cross-model checks.",
    hi: "आपकी प्रवीणता स्तर के अनुसार स्वतः निर्मित प्रश्न। क्रॉस-मॉडल सत्यापन द्वारा परीक्षित।",
  },
  practiceBloomLevel: { en: "Bloom's Taxonomy Level", hi: "ब्लूम्स स्तर" },
  practiceSubmit: { en: "Submit Response", hi: "उत्तर सबमिट करें" },
  practiceFeedback: { en: "Instructor Feedback & Citations", hi: "मूल्यांकन एवं संदर्भ" },
  practiceRubricTitle: { en: "Rubric Grading Criteria", hi: "रूब्रिक मूल्यांकन मानदंड" },
  practiceScore: { en: "Score", hi: "अंक" },

  // Revise Screen
  reviseTitle: { en: "Active Recall & Spaced Repetition", hi: "सक्रिय स्मरण एवं पुनरावृत्ति" },
  reviseSubtitle: {
    en: "Review high-yield flashcards (SM-2 / FSRS), inspect summary slides, and listen to 5-minute pre-exam audio briefs.",
    hi: "SM-2/FSRS आधारित फ्लैशकार्ड्स, मुख्य सार संक्षेप, एवं 5-मिनट ऑडियो ब्रीफ से तीव्र पुनरावृत्ति।",
  },
  reviseFlipPrompt: { en: "Click or press Space to reveal answer", hi: "उत्तर देखने के लिए क्लिक करें या स्पेस दबाएं" },
  reviseRatingAgain: { en: "Again (< 1d)", hi: "पुनः (< 1 दिन)" },
  reviseRatingHard: { en: "Hard (2d)", hi: "कठिन (2 दिन)" },
  reviseRatingGood: { en: "Good (4d)", hi: "उत्तम (4 दिन)" },
  reviseRatingEasy: { en: "Easy (7d)", hi: "सरल (7 दिन)" },
  reviseAudioBrief: { en: "5-Minute Pre-Exam Audio Brief", hi: "5-मिनट परीक्षा पूर्व ऑडियो सारांश" },
  reviseSummaryDeck: { en: "High-Yield Summary Deck", hi: "उच्च प्रासंगिक सार संक्षेप" },

  // Progress Screen
  progressTitle: { en: "Knowledge Map & Learner State", hi: "ज्ञान मानचित्र एवं विद्यार्थी प्रगति" },
  progressSubtitle: {
    en: "Interactive Prerequisite Directed Acyclic Graph (DAG) with Bayesian Knowledge Tracing (BKT) and memory decay modeling.",
    hi: "बायेशियन ज्ञान ट्रेसिंग (BKT) एवं विस्मरण वक्र के साथ संवादात्मक पूर्वापेक्षा आरेख।",
  },
  progressMasteryLevel: { en: "Overall Curriculum Mastery", hi: "समग्र पाठ्यक्रम प्रवीणता" },
  progressForgettingCurve: { en: "Ebbinghaus Memory Retention Decay", hi: "एबिंगहॉस स्मृति अवधारण वक्र" },
  progressPrereqGraph: { en: "Prerequisite Concept Graph (DAG)", hi: "पूर्वापेक्षा ज्ञान आरेख (DAG)" },
  progressLegendMastered: { en: "Mastered (p > 0.85)", hi: "प्रवीण (p > 0.85)" },
  progressLegendLearning: { en: "In Progress (0.4 - 0.85)", hi: "अध्ययनरत (0.4 - 0.85)" },
  progressLegendUnexplored: { en: "Needs Attention (p < 0.4)", hi: "ध्यान देने योग्य (p < 0.4)" },

  // Footer & Status
  footerCopyright: {
    en: "© 2026 Gyaan Setu. Where Knowledge Bridges Minds.",
    hi: "© 2026 ज्ञान सेतु। जहाँ ज्ञान मस्तिष्क को जोड़ता है।",
  },
  backendConnected: { en: "Backend: Live & Operational", hi: "बैकएंड: सक्रिय एवं संचालित" },
  backendOfflineMock: { en: "Backend: Standalone Mode (Typed Mock Engine)", hi: "बैकएंड: स्टैंडअलोन मोड (सुरक्षित मॉक इंजन)" },
};

interface I18nContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: keyof typeof translations) => string;
}

const I18nContext = createContext<I18nContextType>({
  lang: "en",
  setLang: () => {},
  t: (key) => translations[key]?.en || String(key),
});

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Language>("en");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("gyaan_setu_lang") as Language;
      if (saved === "en" || saved === "hi") {
        setLangState(saved);
      }
    } catch {
      // Ignore in SSR
    }
  }, []);

  const setLang = (newLang: Language) => {
    setLangState(newLang);
    try {
      localStorage.setItem("gyaan_setu_lang", newLang);
    } catch {
      // Ignore
    }
  };

  const t = (key: keyof typeof translations): string => {
    const entry = translations[key];
    if (!entry) return String(key);
    return entry[lang] || entry.en || String(key);
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => useContext(I18nContext);
