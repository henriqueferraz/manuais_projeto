# Project Brief: TechParts AI - E-commerce de Peças com IA

> **Documento histórico** (brief inicial). Stack LLM e UI vigentes: OpenAI via `*_LLM_MODE`, Django templates — ver [`README.md`](README.md) e [`pages/inventory.md`](pages/inventory.md). Não usar este brief como fonte de implementação.

## 1. Overview
TechParts AI is a specialized e-commerce platform for industrial and domestic spare parts. The core differentiator is the use of Artificial Intelligence to automate catalog management (extracting data from technical manuals) and provide high-fidelity technical support (AI-driven diagnostics and RAG-based chat).

**Brand Concept:** "Efficiency through Automation."
**Visual Identity:** *Industrial Precision* – A clean, technical aesthetic blending industrial reliability with modern AI assistance.

---

## 2. Strategic Objectives
- **Automated Ingestion:** Use AI to extract structured data (SKUs, specs, compatibility) from PDF manuals, reducing manual entry errors and time.
- **Support-to-Sales Conversion:** Implement an AI Diagnostic tool that identifies problems and suggests the correct replacement parts immediately.
- **Technical Accuracy:** Ensure customers buy the right part through a robust "Compatibility Verifier" backed by manufacturer data.
- **Post-Purchase Value:** Provide a Digital Warranty area and technical ticket management to increase customer retention.

---

## 3. Core Features & User Stories

### A. Customer Experience (Storefront)
- **AI-Powered Search:** Intelligent search bar that understands technical terms and model numbers.
- **Diagnostic Chat:** A RAG-based (Retrieval-Augmented Generation) assistant that reads manuals to answer "How-to" and troubleshooting questions.
- **Photo Search (Future):** Visual identification of broken parts via camera.
- **Compatibility Badge:** Visual confirmation on product pages that a part fits the user's specific equipment model.

### B. Administrative Experience (Back-office)
- **Manual Review Dashboard:** Interface for human-in-the-loop validation of AI-extracted data.
- **Inventory Management:** Real-time tracking of stock levels with automated reorder alerts.
- **Support Ticket Portal:** Centralized view of all customer inquiries, with AI-summarized histories.

---

## 4. Design Standards (Industrial Precision)
- **Typography:** Inter (Bold for technical hierarchy, Regular for body).
- **Color Palette:**
    - *Industrial Navy* (`#1a2b3c`): Trust and authority.
    - *AI Cyan* (`#00e5ff`): Innovation and interactive AI elements.
    - *Tech Gray* (`#6c757d`): Metadata and secondary information.
- **Layout:** Responsive (Desktop/Mobile), standard 12-column grid, 4px border radius for a professional "engineered" feel.

---

## 5. Technical Stack (Proposed)
- **Frontend:** Django Templates + htmx + Bootstrap (Server-Side Rendering for SEO).
- **Backend:** Python / Django.
- **AI Engine:** Anthropic Claude (via LangChain/LangGraph) for extraction and diagnostics.
- **Database:** PostgreSQL + pgvector (for semantic search).
- **Infrastructure:** Cloudflare R2 for PDF/Image storage; Celery for background processing.

---

## 6. Roadmap
1.  **Phase 1-3:** Ingestion pipeline and core catalog models (Completed).
2.  **Phase 4:** Core e-commerce (Cart, Checkout, Payment integration).
3.  **Phase 5:** AI Chat & Diagnostic Assistant (Design Phase Completed).
4.  **Phase 6:** Advanced AI features (LangGraph workflows, Photo Search).
5.  **Phase 7-8:** Scale, Multi-language support, and Maintenance Subscriptions.
