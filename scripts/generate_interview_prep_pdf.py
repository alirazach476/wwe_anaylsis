"""Generate WWE Anaylsis project + interview prep PDF."""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parents[1] / "docs" / "WWE_Anaylsis_Project_Interview_Prep.pdf"

RED = HexColor("#C41E3A")
DARK = HexColor("#111111")
GOLD = HexColor("#C9A227")
GRAY = HexColor("#444444")
LIGHT = HexColor("#F5F5F5")
MUTED = HexColor("#6B6B6B")

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=white,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=34,
    )
)
styles.add(
    ParagraphStyle(
        name="CoverSub",
        fontName="Helvetica",
        fontSize=12,
        textColor=HexColor("#F0D9A8"),
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=16,
    )
)
styles.add(
    ParagraphStyle(
        name="H1Custom",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=DARK,
        spaceBefore=4,
        spaceAfter=10,
        leading=20,
    )
)
styles.add(
    ParagraphStyle(
        name="H2Custom",
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=RED,
        spaceBefore=12,
        spaceAfter=6,
        leading=15,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyCustom",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=GRAY,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=13,
    )
)
styles.add(
    ParagraphStyle(
        name="BulletBody",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=GRAY,
        leading=13,
        leftIndent=0,
    )
)
styles.add(
    ParagraphStyle(
        name="QStyle",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        textColor=DARK,
        spaceBefore=8,
        spaceAfter=3,
        leading=12,
    )
)
styles.add(
    ParagraphStyle(
        name="AStyle",
        fontName="Helvetica",
        fontSize=9.2,
        textColor=GRAY,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
        leading=12.5,
        leftIndent=8,
    )
)
styles.add(
    ParagraphStyle(
        name="FooterStyle",
        fontName="Helvetica",
        fontSize=8,
        textColor=MUTED,
        alignment=TA_CENTER,
    )
)


def bullets(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [
            ListItem(Paragraph(i, styles["BulletBody"]), leftIndent=12, bulletColor=RED)
            for i in items
        ],
        bulletType="bullet",
        start="•",
        leftIndent=15,
        bulletFontSize=9,
    )


def qa(q: str, a: str) -> KeepTogether:
    return KeepTogether(
        [
            Paragraph(f"Q. {q}", styles["QStyle"]),
            Paragraph(a, styles["AStyle"]),
        ]
    )


def section_rule() -> HRFlowable:
    return HRFlowable(width="100%", thickness=1, color=RED, spaceBefore=2, spaceAfter=10)


def build() -> None:
    story: list = []

    cover_data = [
        [Paragraph("WWE ANAYLSIS", styles["CoverTitle"])],
        [Paragraph("Project Working Guide · Tech Stack · Interview Prep", styles["CoverSub"])],
        [Paragraph("Premium Live Event Analytics Platform (2000–2027)", styles["CoverSub"])],
        [
            Paragraph(
                "Live: https://wwe-anaylsis.vercel.app<br/>"
                "Repo: https://github.com/alirazach476/wwe_anaylsis",
                styles["CoverSub"],
            )
        ],
    ]
    cover = Table(cover_data, colWidths=[6.5 * inch])
    cover.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DARK),
                ("TOPPADDING", (0, 0), (-1, 0), 90),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 80),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 3, GOLD),
            ]
        )
    )
    story.append(cover)
    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            "Use this pack to walk interviewers through <b>what you built</b>, "
            "<b>how data flows</b>, <b>why each technology was chosen</b>, and "
            "<b>crisp answers</b> for system-design and data-engineering questions.",
            styles["BodyCustom"],
        )
    )
    story.append(PageBreak())

    # 1. Overview
    story.append(Paragraph("1. Project Overview — How It Works", styles["H1Custom"]))
    story.append(section_rule())
    story.append(
        Paragraph(
            "<b>WWE Anaylsis</b> is an end-to-end analytics product for WWE Premium Live Events (PLEs). "
            "It collects and validates historical event/match data, loads a dimensional warehouse, "
            "materializes analytics marts, serves them through a FastAPI layer, and renders a "
            "broadcast-style React dashboard with event-logo theming, wrestler/event deep dives, "
            "championship analytics, and curated historical landmarks.",
            styles["BodyCustom"],
        )
    )

    story.append(Paragraph("Product surfaces", styles["H2Custom"]))
    prod = [
        ["Page", "What it shows"],
        ["Home / Overview", "Catalog KPIs, attendance trends, chart gallery moved from Events"],
        ["Events + Detail", "Poster cards, filters, match card, duration charts, logo theme"],
        ["Matches", "Duration / finish-method analytics with sticky custom filters"],
        ["Wrestlers + Detail", "Full deduped roster, Man/Woman avatars, career stats"],
        ["Championships", "PLE title landscape including Crown Jewel featured belts"],
        ["Timeline", "Curated landmark records (e.g. Cena 17 world titles, Reigns 1,316 days)"],
    ]
    t = Table(prod, colWidths=[1.7 * inch, 4.8 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, white]),
                ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#DDDDDD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)

    story.append(Paragraph("End-to-end data flow", styles["H2Custom"]))
    story.append(
        Paragraph(
            "<font face='Courier' size='8'>Registry / MediaWiki API → Clean / Validate → "
            "Dimensional Warehouse → Marts CSV → FastAPI → React (Vite) → Vercel</font>",
            styles["BodyCustom"],
        )
    )
    story.append(
        bullets(
            [
                "<b>Raw / inventory:</b> event series registry + collectors (Wikipedia / MediaWiki), "
                "eligibility rules excluding weekly TV &amp; house shows.",
                "<b>Cleaning:</b> normalize names, dedupe wrestlers, flag conflicts; "
                "null attendance is never coerced to 0.",
                "<b>Warehouse:</b> dimensional model (events, matches, participants, championships) "
                "in SQLite/Postgres.",
                "<b>Marts:</b> pre-aggregated CSVs for overview, attendance, wrestlers, matches, "
                "Rumble/MITB, championships.",
                "<b>API:</b> FastAPI reads marts (+ runtime export fallbacks) — dashboard never invents "
                "metrics client-side.",
                "<b>UI:</b> React pages consume <font face='Courier'>/api/*</font>; Plotly charts; "
                "themes sampled from event logo palettes.",
                "<b>Deploy:</b> Vercel static frontend + Python serverless ASGI "
                "(<font face='Courier'>api/index.py</font>) with marts/exports bundled via "
                "<font face='Courier'>includeFiles</font>.",
            ]
        )
    )

    story.append(Paragraph("Design constraints (say these in interviews)", styles["H2Custom"]))
    story.append(
        bullets(
            [
                "No fabricated historical rows — curated Timeline records are labeled as landmarks "
                "when marts diverge from official marks.",
                "Championship analytics = PLE title changes only (not weekly TV defenses).",
                "Dashboard metrics come from API/marts only.",
                "Serverless FS is read-only — settings mkdir is guarded; exports resolve to "
                "<font face='Courier'>runtime_exports</font> on Vercel.",
            ]
        )
    )
    story.append(PageBreak())

    # 2. Tech stack
    story.append(Paragraph("2. Tech Stack", styles["H1Custom"]))
    story.append(section_rule())
    stack = [
        ["Layer", "Technology", "Why it fits"],
        ["Language (BE)", "Python 3.11+", "Pandas + FastAPI ecosystem; strong for ETL"],
        ["API", "FastAPI + Uvicorn / ASGI", "Typed routes, fast cold starts, Vercel ASGI"],
        ["Validation", "Pydantic / pydantic-settings", "Config + schema contracts for inventory"],
        ["Dataframes", "Pandas (+ NumPy)", "Mart materialization & analytics transforms"],
        ["ORM / DB", "SQLAlchemy, SQLite / Postgres", "Local SQLite; Compose Postgres optional"],
        ["Transform SQL", "dbt (optional path)", "Documented SQL marts alongside Python"],
        ["Collection", "requests / httpx, BS4, lxml", "MediaWiki + HTML parsing, retries (tenacity)"],
        ["Frontend", "React 18 + TypeScript + Vite", "SPA speed, typed UI, modern DX"],
        ["Charts", "Plotly (react-plotly.js)", "Interactive analytics visuals"],
        ["Routing", "React Router 6", "Event/wrestler deep links"],
        ["Theming", "Logo-derived CSS variables", "Event-specific broadcast look"],
        ["Deploy", "Vercel (static + Python fn)", "One project for UI + API"],
        ["Containers", "Docker Compose", "Postgres + API + frontend local parity"],
        ["Orchestration", "Airflow DAG (optional)", "Warehouse refresh scheduling"],
        ["Tests", "Pytest", "Registry, eligibility, dedupe, warehouse"],
    ]
    st = Table(stack, colWidths=[1.2 * inch, 1.9 * inch, 3.4 * inch])
    st.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), RED),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, white]),
                ("GRID", (0, 0), (-1, -1), 0.35, HexColor("#DDDDDD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(st)

    story.append(Paragraph("Key API endpoints (talking points)", styles["H2Custom"]))
    story.append(
        bullets(
            [
                "<font face='Courier'>/health</font> — marts present? warehouse sqlite?",
                "<font face='Courier'>/api/analytics/overview</font>, "
                "<font face='Courier'>/attendance</font>, "
                "<font face='Courier'>/matches</font>, "
                "<font face='Courier'>/championships</font>",
                "<font face='Courier'>/api/events</font>, "
                "<font face='Courier'>/api/wrestlers</font> (full roster + dedupe), "
                "<font face='Courier'>/api/matches</font>",
                "<font face='Courier'>/api/analytics/historical-records</font> — curated Timeline landmarks",
                "<font face='Courier'>/api/filters/meta</font> — drives sticky FilterSelect portals",
            ]
        )
    )

    story.append(Paragraph("Repo map (30-second tour)", styles["H2Custom"]))
    story.append(
        Paragraph(
            "<font face='Courier' size='8'>"
            "api/ → Vercel entry &nbsp;|&nbsp; frontend/ → React app &nbsp;|&nbsp; "
            "src/wwe_data/ → collectors, warehouse, API<br/>"
            "data/warehouse/marts + runtime_exports → production data &nbsp;|&nbsp; "
            "config/ → series registry &amp; eligibility<br/>"
            "docs/ → architecture &amp; dictionary &nbsp;|&nbsp; "
            "scripts/ → one-offs (e.g. Crown Jewel)"
            "</font>",
            styles["BodyCustom"],
        )
    )
    story.append(PageBreak())

    # 3. Architecture
    story.append(Paragraph("3. Architecture Deep Dive", styles["H1Custom"]))
    story.append(section_rule())
    story.append(Paragraph("Dimensional thinking", styles["H2Custom"]))
    story.append(
        Paragraph(
            "Facts (matches, title changes) are separated from dimensions "
            "(events, wrestlers, venues, brands, dates). Marts are <b>denormalized read models</b> "
            "optimized for dashboard queries so the API stays simple and cheap on serverless.",
            styles["BodyCustom"],
        )
    )
    story.append(Paragraph("Vercel production shape", styles["H2Custom"]))
    story.append(
        bullets(
            [
                "Build: <font face='Courier'>cd frontend &amp;&amp; npm run build</font> → "
                "<font face='Courier'>frontend/dist</font>",
                "Rewrites: <font face='Courier'>/api/*</font> and <font face='Courier'>/health</font> → "
                "Python ASGI; SPA fallback to <font face='Courier'>index.html</font>",
                "Bundle: <font face='Courier'>includeFiles</font> packs <font face='Courier'>src/**</font>, "
                "marts, and <font face='Courier'>runtime_exports</font> (because "
                "<font face='Courier'>data/exports</font> is gitignored)",
                "Assets: event logos live under <font face='Courier'>frontend/public/logos/files</font> "
                "(must not be ignored by <font face='Courier'>.vercelignore</font>)",
            ]
        )
    )
    story.append(Paragraph("Hard problems you solved (story bank)", styles["H2Custom"]))
    story.append(
        bullets(
            [
                "<b>Wrestler identity:</b> same performer under aliases → dedupe + full roster listing "
                "(not capped samples).",
                "<b>Attendance honesty:</b> exclude zeros / missing from averages; yearly avg chart "
                "instead of sum-as-avg mistakes.",
                "<b>Official vs warehouse records:</b> Timeline uses curated landmarks where PLE-scoped "
                "marts undercount all-time marks.",
                "<b>UX:</b> sticky filter strip + portal-based FilterSelect to avoid overflow clipping "
                "in scroll containers.",
                "<b>Theming:</b> sample palette from event logos so each PLE feels branded, not a "
                "generic dark dashboard.",
                "<b>Deploy packaging:</b> junction logos failed on Linux builders; real files + correct "
                "ignore patterns required.",
            ]
        )
    )
    story.append(PageBreak())

    # 4. Interview behavioral
    story.append(Paragraph("4. Interview Prep — Elevator &amp; Behavioral", styles["H1Custom"]))
    story.append(section_rule())
    story.append(Paragraph("60-second elevator pitch", styles["H2Custom"]))
    story.append(
        Paragraph(
            "“I built a full-stack analytics platform for WWE Premium Live Events from 2000–2027. "
            "It starts with a documented collection pipeline into a dimensional warehouse and analytics "
            "marts, exposes them through FastAPI, and ships a React + Plotly dashboard with event-logo "
            "theming. It’s deployed on Vercel with the UI and Python API in one project. The focus was "
            "trustworthy metrics, clear product UX, and production packaging — not just charts on a CSV.”",
            styles["BodyCustom"],
        )
    )
    story.append(Paragraph("STAR stories to prepare", styles["H2Custom"]))
    story.append(
        qa(
            "Tell me about a data-quality decision you made.",
            "Attendance nulls were being treated like zero and inflated or collapsed averages. I excluded "
            "non-positive attendance from average calculations and added a yearly average view so the "
            "metric matched user intent. Constraint: never invent attendance.",
        )
    )
    story.append(
        qa(
            "Describe a production deploy issue.",
            "Event logos were a Windows junction and later excluded by a broad "
            "<font face='Courier'>logos</font> vercelignore rule. Linux build couldn’t see them "
            "(404s in prod). Fixed by shipping real files under "
            "<font face='Courier'>frontend/public/logos</font> and scoping ignore to root-only "
            "<font face='Courier'>/logos</font>, then redeploying.",
        )
    )
    story.append(
        qa(
            "How did you handle conflicting ‘truth’ between dataset and public records?",
            "PLE-scoped marts can’t always reproduce all-time records (e.g. Cena’s 17). Timeline exposes "
            "curated landmark records with clear framing, while warehouse charts remain honest to PLE "
            "data — transparency over fake equality.",
        )
    )
    story.append(Paragraph("Behavioral one-liners", styles["H2Custom"]))
    story.append(
        bullets(
            [
                "Owned product + engineering: filters, themes, API contracts, deploy.",
                "Prefer constraints over cleverness: eligibility registry, no fabricated rows.",
                "Iterate with user-visible bugs (avatar gender labels, filter portal scroll, "
                "Crown Jewel titles).",
            ]
        )
    )
    story.append(PageBreak())

    # 5. Technical Q&A
    story.append(Paragraph("5. Technical Q&amp;A (Practice Answers)", styles["H1Custom"]))
    story.append(section_rule())
    story.append(Paragraph("System design &amp; data", styles["H2Custom"]))
    story.append(
        qa(
            "Why marts instead of querying the warehouse from the UI?",
            "Dashboards need stable, fast, denormalized slices. Marts keep the serverless API simple "
            "(read CSV/pandas), reduce join cost, and freeze metric definitions so the React app doesn’t "
            "reimplement business logic.",
        )
    )
    story.append(
        qa(
            "Why FastAPI?",
            "Native async ASGI (Vercel-friendly), automatic OpenAPI, Pydantic validation, and low "
            "boilerplate for read-heavy analytics endpoints.",
        )
    )
    story.append(
        qa(
            "How do you prevent weekly Raw results from polluting PLE analytics?",
            "Eligibility config + series registry. Collectors and warehouse loads only include Premium "
            "Live Events and allowlisted specials — Raw/SmackDown/NXT TakeOver/house shows are excluded "
            "by rule.",
        )
    )
    story.append(
        qa(
            "How does wrestler deduplication work at a high level?",
            "Normalize display names, map aliases, and collapse duplicate identities when serving roster "
            "endpoints so the UI shows one career card instead of fragmented rows.",
        )
    )
    story.append(
        qa(
            "What would you change at larger scale?",
            "Move marts to a columnar store or Postgres, add caching (CDN/ETag) on API GETs, paginate "
            "heavy endpoints, split logo assets to object storage/CDN, and CI-build marts on a schedule "
            "instead of shipping CSVs in the function bundle.",
        )
    )
    story.append(Paragraph("Frontend &amp; product", styles["H2Custom"]))
    story.append(
        qa(
            "Why Plotly over Chart.js / Recharts?",
            "Rich statistical chart types, hover templates, and fast iteration for analytics-heavy pages "
            "without building a custom viz layer.",
        )
    )
    story.append(
        qa(
            "Explain the event theme system.",
            "Each event logo contributes a palette; CSS variables drive accents so WrestleMania vs "
            "Summerslam feel distinct while sharing one design system (broadcast cards, KPI strips, "
            "tables).",
        )
    )
    story.append(Paragraph("DevOps / Vercel", styles["H2Custom"]))
    story.append(
        qa(
            "How is the API packaged for Vercel?",
            "<font face='Courier'>api/index.py</font> adds <font face='Courier'>src</font> to "
            "<font face='Courier'>sys.path</font> and exports the FastAPI "
            "<font face='Courier'>app</font>. Requirements stay lean in "
            "<font face='Courier'>api/requirements.txt</font>. Marts and runtime export CSVs are "
            "included via <font face='Courier'>includeFiles</font> because primary exports are gitignored.",
        )
    )
    story.append(
        qa(
            "SPA + API on one domain — how?",
            "Rewrites send <font face='Courier'>/api/*</font> to the Python function; other non-file "
            "routes fall through to <font face='Courier'>index.html</font> for client routing.",
        )
    )
    story.append(PageBreak())

    # 6. Cheat sheet
    story.append(Paragraph("6. Interview Cheat Sheet", styles["H1Custom"]))
    story.append(section_rule())
    cheat = [
        ["Topic", "Soundbite"],
        ["Problem", "Trusted PLE analytics UI over messy multi-source wrestling history"],
        ["Approach", "Registry → clean → dimensional WH → marts → API → React"],
        ["Stack", "Python/FastAPI/Pandas + React/TS/Vite/Plotly + Vercel"],
        ["Quality", "No fabricated rows; null ≠ 0; PLE-scoped titles"],
        ["UX wins", "Logo themes, sticky filters, full deduped roster, Timeline landmarks"],
        ["Prod", "https://wwe-anaylsis.vercel.app"],
        ["Code", "https://github.com/alirazach476/wwe_anaylsis"],
        ["Scale next", "DB-backed marts, CDN assets, cache, CI refresh"],
    ]
    ct = Table(cheat, colWidths=[1.3 * inch, 5.2 * inch])
    ct.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFF5F5"), white]),
                ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#E0E0E0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 1), (0, -1), RED),
            ]
        )
    )
    story.append(ct)
    story.append(Spacer(1, 16))
    story.append(Paragraph("Questions to ask the interviewer", styles["H2Custom"]))
    story.append(
        bullets(
            [
                "How does your team separate metric definitions from UI code "
                "(semantic layer / marts / metrics store)?",
                "What’s your approach to historical data corrections without silent rewrites?",
                "For read-heavy dashboards, do you prefer BFF APIs, edge caches, or "
                "warehouse-direct tools?",
            ]
        )
    )
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceBefore=4, spaceAfter=10))
    story.append(
        Paragraph(
            "WWE Anaylsis — Project Working · Tech Stack · Interview Prep<br/>"
            "Generated for interview readiness · Live demo on Vercel",
            styles["FooterStyle"],
        )
    )

    def add_page_number(canvas, doc) -> None:
        canvas.saveState()
        if doc.page > 1:
            canvas.setFillColor(MUTED)
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(letter[0] / 2, 0.45 * inch, f"WWE Anaylsis  ·  Page {doc.page - 1}")
            canvas.setStrokeColor(RED)
            canvas.setLineWidth(1)
            canvas.line(0.75 * inch, letter[1] - 0.5 * inch, letter[0] - 0.75 * inch, letter[1] - 0.5 * inch)
        canvas.restoreState()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="WWE Anaylsis — Project Working, Tech Stack & Interview Prep",
        author="Ali Raza Chaudhry",
        subject="Interview preparation pack for the WWE Anaylsis analytics platform",
    )
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
