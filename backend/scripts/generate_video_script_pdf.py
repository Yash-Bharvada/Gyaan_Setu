"""
Generate a professional, broadcast-ready Video Demo Script PDF for Gyaan Setu.
Outputs: docs/Gyaan_Setu_Video_Demo_Script.pdf
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic page numbers (Page X of Y)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                54,
                letter[1] - 36,
                "GYAAN SETU — Official Product Walkthrough & Video Demo Script",
            )
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 30, footer_text)
        self.drawString(
            54,
            30,
            "Gyaan Setu | Multimodal Grounded AI Tutor & Cognitive Curriculum Engine",
        )
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 42, letter[0] - 54, 42)

        self.restoreState()


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f172a")  # Slate 900
    brand_gold = colors.HexColor("#b45309")     # Amber 700
    accent_blue = colors.HexColor("#0369a1")    # Sky 700
    text_dark = colors.HexColor("#1e293b")      # Slate 800
    text_muted = colors.HexColor("#475569")     # Slate 600

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=0,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=brand_gold,
        alignment=0,
    )

    meta_style = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_muted,
    )

    heading1_style = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
    )

    heading2_style = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=brand_gold,
        spaceBefore=10,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=text_dark,
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white,
    )

    tb_scene = ParagraphStyle(
        "SceneMeta",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=brand_gold,
    )

    tb_action = ParagraphStyle(
        "ActionCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=text_dark,
    )

    tb_narration = ParagraphStyle(
        "NarrationCell",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#0f172a"),
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e3a8a"),
    )

    story = []

    # ── Header Banner ─────────────────────────────────────────────────────────
    story.append(Paragraph("GYAAN SETU &bull; KNOWLEDGE BRIDGE", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Product Video Demo & Walkthrough Script", title_style))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Target Duration:</b> 3 Minutes 30 Seconds &nbsp;|&nbsp; "
            "<b>Format:</b> Screen Recording + Narration Voiceover &nbsp;|&nbsp; "
            "<b>Target Audience:</b> Hackathon Judges (Devpost), Educators, Students",
            meta_style,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=brand_gold,
            spaceBefore=4,
            spaceAfter=12,
        )
    )

    # ── Executive Overview Box ────────────────────────────────────────────────
    overview_text = (
        "<b>Core Narrative:</b> Students face a crisis of fragmented learning—shuffling between dense textbook PDFs and endless YouTube video lectures, while generic AI chats hallucinate formulas without syllabus grounding. "
        "<b>Gyaan Setu</b> solves this by ingesting <b>both documents and YouTube lectures</b> into verifiable, timestamped knowledge units, extracting a curriculum <b>Knowledge DAG</b>, and guiding students through a <b>strictly grounded Socratic Tutor</b>, <b>Bayesian Knowledge Tracing (BKT)</b> adaptive quizzes, and <b>Spaced Repetition (SM-2)</b> audio briefs."
    )
    overview_table = Table(
        [[Paragraph(overview_text, body_style)]],
        colWidths=[letter[0] - 108],
    )
    overview_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(overview_table)
    story.append(Spacer(1, 12))

    # ── Pre-Recording Setup ───────────────────────────────────────────────────
    story.append(Paragraph("🎬 Recommended Demo Preparation Checklist", heading2_style))
    checklist_data = [
        [
            Paragraph("<b>Step</b>", th_style),
            Paragraph("<b>File / Resource to Prepare</b>", th_style),
            Paragraph("<b>Expected Demo Action</b>", th_style),
        ],
        [
            Paragraph("<b>1. Course PDF</b>", tb_action),
            Paragraph("Any syllabus PDF (e.g. <i>Machine Learning Guide.pdf</i>)", tb_action),
            Paragraph("Drag & drop into <b>Library &rarr; Upload Course Files</b>", tb_action),
        ],
        [
            Paragraph("<b>2. YouTube URL</b>", tb_action),
            Paragraph("E.g. <code>https://www.youtube.com/watch?v=aircAruvnKk</code> (Neural Networks by 3Blue1Brown)", tb_action),
            Paragraph("Paste into <b>Library &rarr; Ingest YouTube / Video Lecture</b>", tb_action),
        ],
        [
            Paragraph("<b>3. Clean State</b>", tb_action),
            Paragraph("Database already reset to clean slate (verified 0 rows)", tb_action),
            Paragraph("Ready for live upload during the video demo", tb_action),
        ],
        [
            Paragraph("<b>4. Servers</b>", tb_action),
            Paragraph("Backend on <code>:8000</code>, Frontend on <code>:3000</code>", tb_action),
            Paragraph("Both running and verified healthy", tb_action),
        ],
    ]
    check_table = Table(checklist_data, colWidths=[90, 190, letter[0] - 108 - 280])
    check_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(check_table)
    story.append(Spacer(1, 14))

    # ── SCENE BY SCENE SCRIPT ─────────────────────────────────────────────────
    story.append(Paragraph("📽️ Scene-by-Scene Production Script", heading1_style))
    story.append(
        Paragraph(
            "Follow each scene sequentially. The timing is calibrated for a natural speaking rate of 130-140 words per minute.",
            meta_style,
        )
    )
    story.append(Spacer(1, 6))

    scenes = [
        {
            "num": "SCENE 1",
            "time": "00:00 – 00:22\n(22s)",
            "title": "The Hook & The Crisis in Modern Learning",
            "screen": "Open on Gyaan Setu Landing Page / Dashboard (<code>http://localhost:3000</code>). Show clean Greek-key architectural accents, gold cards, and the 5 navigation tabs: Library, Tutor, Practice, Revise, Progress.",
            "narration": "\"Every student today faces the same struggle: our study materials are completely fragmented. Textbook PDFs, slide decks, and hour-long YouTube lecture videos live in silos. And when we ask generic AI chatbots for help, they hallucinate formulas and ignore our actual syllabus.\n\nMeet Gyaan Setu—the grounded multimodal AI tutor and curriculum engine that unifies your documents and video lectures into one verifiable learning system.\"",
        },
        {
            "num": "SCENE 2",
            "time": "00:22 – 00:45\n(23s)",
            "title": "Dual Ingestion Part 1: Ingesting Course Documents (PDF)",
            "screen": "Click <b>Library</b> tab. In the <b>Upload Course Files</b> section, drag and drop a course PDF (e.g. <i>Machine Learning Guide.pdf</i>). Show the real-time progress bar analyzing layout and indexing units into PyMuPDF chunks. Point out the newly created source card showing Page Count and unit count.",
            "narration": "\"Let's start in the Library. First, we upload our course textbook PDF. Gyaan Setu's multimodal ingestion pipeline extracts every page, table, and formula, indexing them into traceable units with exact page numbers. No lost context, no unverified chunks.\"",
        },
        {
            "num": "SCENE 3",
            "time": "00:45 – 01:10\n(25s)",
            "title": "Dual Ingestion Part 2: Ingesting YouTube Lecture Videos",
            "screen": "Switch to the <b>Ingest YouTube / Video Lecture</b> tab. Paste a YouTube link (e.g. 3Blue1Brown Neural Networks). Enter title 'Neural Networks Foundation'. Click <b>Ingest Video Lecture</b>. Show notification: <i>'Successfully ingested video units'</i>. Notice the exact timestamped units (⏱️ MM:SS–MM:SS) in the source viewer.",
            "narration": "\"Now for the magic: YouTube video lectures. Simply switch to the YouTube tab and paste any lecture URL. Gyaan Setu extracts timestamped transcripts—down to the exact second. Whether a concept was taught on page 4 of the textbook or at minute 3:45 of a video lecture, both are now indexed into our unified semantic vector space.\"",
        },
        {
            "num": "SCENE 4",
            "time": "01:10 – 01:30\n(20s)",
            "title": "Building the Curriculum Knowledge DAG",
            "screen": "Click the gold button: <b>Build Knowledge DAG</b>. Show the toast: <i>'Knowledge DAG built! Topics indexed'</i>. Click <b>Progress</b> tab to show the interactive Directed Acyclic Graph (DAG) with canvas pan/zoom, prerequisite arrows, and topological learning sequence.",
            "narration": "\"Next, with one click, we build the Curriculum Knowledge DAG. Using NetworkX, Gyaan Setu maps prerequisite dependencies between concepts, detecting cycles and organizing a topological learning roadmap. Students never get stuck on an advanced topic without mastering the prerequisite fundamentals.\"",
        },
        {
            "num": "SCENE 5",
            "time": "01:30 – 02:05\n(35s)",
            "title": "Source-Grounded Socratic Tutor & Dual Citations Jump",
            "screen": "Navigate to <b>Tutor</b> tab. Toggle <b>Strict Grounding</b> on. Type a Hinglish/English question: <i>'What is the difference between Gradient Descent and Backpropagation?'</i> Press Send. Show the grounded answer streaming back with citation badges: <code>[Page 4]</code> and <code>[03:45]</code>.\n\n<b>CRITICAL INTERACTIVE ACTION:</b>\n1. Click <code>[Page 4]</code> &rarr; Modal opens showing textbook excerpt!\n2. Click <code>[03:45]</code> &rarr; Modal opens showing embedded YouTube player playing at that exact second!",
            "narration": "\"Now, let's learn with our Socratic AI Tutor. We ask: 'What is the difference between Gradient Descent and Backpropagation?'\n\nNotice how every single claim is strictly verified with clickable citation tags. When I click [Page 4], the source textbook modal opens immediately with the exact excerpt. And when I click [03:45], it embeds the YouTube lecture player and jumps directly to that second! Zero hallucinations. Total academic trust.\"",
        },
        {
            "num": "SCENE 6",
            "time": "02:05 – 02:25\n(20s)",
            "title": "Multilingual Voice & Speech Tutoring",
            "screen": "In Tutor, click the <b>Voice Chat / Microphone</b> button. Speak a question in Hindi or English (e.g. <i>'Mujhe loss function ka intuitive matlab batao'</i>). Show speech transcription via faster-whisper and hear the instant Edge-TTS audio response play with audio waveform indicator.",
            "narration": "\"Gyaan Setu also features real-time voice tutoring. Powered by faster-whisper STT and Edge-TTS synthesis, students can speak naturally in English, Hindi, or Hinglish. Vernacular queries are expanded into academic terminology for seamless cross-lingual retrieval.\"",
        },
        {
            "num": "SCENE 7",
            "time": "02:25 – 02:50\n(25s)",
            "title": "Adaptive Practice Quiz & Bayesian Knowledge Tracing (BKT)",
            "screen": "Click <b>Practice</b> tab. Select topic or click <b>Start Adaptive Quiz</b>. Show an MCQ generated from the ingested PDF and video lecture. Select an option and submit. Show immediate verification feedback, source citations, and the <b>Mastery Probability P(L) update</b> powered by BKT.",
            "narration": "\"How do we test our understanding? The Practice module generates grounded MCQs and short-answer questions verified against our units. When we submit an answer, our cognitive Bayesian Knowledge Tracing engine updates our latent knowledge probability P(L) and memory stability in real time—adapting future quizzes to strengthen our weak spots.\"",
        },
        {
            "num": "SCENE 8",
            "time": "02:50 – 03:15\n(25s)",
            "title": "Spaced Repetition (SM-2) Flashcards & 2-Minute Audio Brief",
            "screen": "Click <b>Revise</b> tab. Show the SuperMemo SM-2 flashcard. Click to flip card and rate memory recall (0 to 5). Then scroll down to the <b>Audio Synthesis Studio</b>, click <b>Play 2-Min Audio Brief</b> or <b>Podcast Mode</b> to hear the generated two-host study podcast.",
            "narration": "\"For retention, the Revise module schedules flashcards using the SuperMemo SM-2 spaced repetition algorithm, calculating optimal review intervals. And when you're on the commute, listen to an automated 2-minute Audio Brief or a two-host dialogue podcast generated directly from your syllabus!\"",
        },
        {
            "num": "SCENE 9",
            "time": "03:15 – 03:35\n(20s)",
            "title": "Architecture, Zero Cost Ledger & Closing",
            "screen": "Return to Dashboard / Progress view. Show the Mastery status and highlight the live backend metrics: 45 API endpoints, local ChromaDB, local sentence-transformers, and zero external API costs incurred in the usage ledger.",
            "narration": "\"Gyaan Setu is built with production-grade engineering: FastAPI, SQLite in WAL mode, local ChromaDB embeddings, and a Next.js 16 frontend. Best of all, it runs with zero external API costs, providing accessible, private, and syllabus-grounded education to every student.\n\nThank you for watching Gyaan Setu—bridging curiosity to true mastery.\"",
        },
    ]

    for sc in scenes:
        table_data = [
            [
                Paragraph(f"<b>{sc['num']}</b><br/>{sc['time']}", tb_scene),
                Paragraph(f"<b>{sc['title']}</b><br/><br/><b>Visual Action:</b><br/>{sc['screen']}", tb_action),
                Paragraph(f"<b>Spoken Narration (Voiceover):</b><br/>{sc['narration'].replace(chr(10), '<br/>')}", tb_narration),
            ]
        ]
        scene_table = Table(table_data, colWidths=[80, 210, letter[0] - 108 - 290])
        scene_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                    ("BACKGROUND", (1, 0), (1, -1), colors.white),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#fefce8")),  # Warm pale gold tint for speech
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(KeepTogether([scene_table, Spacer(1, 8)]))

    # ── Page Break for Production Tips ───────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("🎥 Video Recording & Production Best Practices", heading1_style))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#cbd5e1"),
            spaceBefore=2,
            spaceAfter=10,
        )
    )

    tips = [
        ("Screen Resolution & Aspect Ratio", "Record at standard <b>1080p (1920x1080) at 60 FPS</b>. Set browser zoom to <b>100% or 110%</b> so gold UI cards, buttons, and Greek-key borders are crisp and legible on mobile screens."),
        ("Microphone & Audio Delivery", "Use a USB condenser mic or headset. Speak with an <b>enthusiastic, confident, and articulate pacing (130-140 words per minute)</b>. Leave 1-2 seconds of silence before and after each scene for clean audio splicing."),
        ("Cursor Movement & Highlights", "Move the mouse smoothly with purpose. Avoid rapid circle-spinning. Hover over citations (<code>[Page 4]</code>, <code>[03:45]</code>) for a full second before clicking to draw the viewer's eye."),
        ("Interactive Citation Climax", "In Scene 5, ensure the audience clearly sees the YouTube video modal pop up and start playback at the specified timestamp. This is the <b>'WOW' moment</b> for judges proving true multimodal grounding."),
        ("B-Roll / Title Cards (Optional)", "Add a 2-second intro title card with the Gyaan Setu logo and tagline: <i>'Grounded Multimodal AI Tutor & Cognitive Curriculum Engine'</i>, and a 3-second closing card with your GitHub repository link."),
    ]

    for title, desc in tips:
        t_box = Table(
            [[
                Paragraph(f"<b>&bull; {title}:</b> {desc}", body_style)
            ]],
            colWidths=[letter[0] - 108],
        )
        t_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(t_box)
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(Paragraph("🏆 Key Hackathon Judging Points to Emphasize", heading2_style))

    rubric_points = [
        "<b>Verifiable Grounding vs. Generic RAG:</b> Gyaan Setu doesn't just return chunk snippets; it verifies chunks across PyMuPDF and YouTube transcripts, appending enforceable page and second-level citations.",
        "<b>Cognitive Science Foundation:</b> Features true Bayesian Knowledge Tracing (BKT) updating latent knowledge probability P(L) and SuperMemo SM-2 spaced repetition stability rather than superficial scoring.",
        "<b>Curriculum DAG Reasoning:</b> Uses NetworkX Directed Acyclic Graphs with cycle detection and topological sorting to prevent out-of-order learning.",
        "<b>Zero External API Cost Architecture:</b> Demonstrates that high-end AI education can be delivered affordably using local sentence-transformers, ChromaDB, Edge-TTS, and faster-whisper.",
    ]

    for pt in rubric_points:
        story.append(Paragraph(f"&check; {pt}", body_style))
        story.append(Spacer(1, 4))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] PDF successfully generated at: {output_path}")


if __name__ == "__main__":
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "Gyaan_Setu_Video_Demo_Script.pdf")
    build_pdf(out_file)
