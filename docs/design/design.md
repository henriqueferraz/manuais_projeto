# Design System: Industrial Precision

**Brand:** TechParts AI  
**Core Concept:** Efficiency through Automation. A high-fidelity industrial aesthetic that blends technical precision with modern AI assistance.

---

## 1. Visual Identity & Theme

- **Color Mode:** Light
- **Primary Font:** Inter (Sans-serif)
- **Roundness:** `ROUND_FOUR` (4px / 0.25rem) - Subtle, professional radius.
- **Brand Personality:** Trustworthy, efficient, precise, and innovative.

---

## 2. Color Palette

The palette uses a technical navy base with high-contrast AI-focused accents.

### Surface Colors
- **Surface:** `#f8f9fa`
- **Surface Dim:** `#d9dadb`
- **Surface Bright:** `#f8f9fa`
- **Surface Container Lowest:** `#ffffff`
- **Surface Container Low:** `#f3f4f5`
- **Surface Container:** `#ededee`
- **Surface Container High:** `#e2e3e4`
- **Surface Container Highest:** `#d9dadb`

### Brand & Accents
- **Industrial Navy (Primary):** `#1a2b3c` (Main brand color, headings, navigation)
- **AI Cyan (Secondary/Action):** `#00e5ff` (AI features, primary buttons, call-to-actions)
- **Tech Gray:** `#6c757d` (Secondary text, inactive states, icons)
- **Status Success:** `#28a745` (Availability, resolved tickets)
- **Status Alert/Danger:** `#dc3545` (Critical failures, complex diagnostics)

---

## 3. Typography Scale

- **Headline Large:** 32px / 2rem, Inter, Bold, Navy
- **Headline Medium:** 24px / 1.5rem, Inter, Bold, Navy
- **Headline Small:** 20px / 1.25rem, Inter, Semi-Bold, Navy
- **Body Large:** 18px / 1.125rem, Inter, Regular
- **Body Medium:** 16px / 1rem, Inter, Regular (Default text)
- **Body Small:** 14px / 0.875rem, Inter, Regular (Technical specs)
- **Label/Caps:** 12px / 0.75rem, Inter, Bold, Uppercase (Overlines, categories)

---

## 4. Spacing & Layout

- **Margin (Desktop):** 48px / 3rem
- **Gutter:** 24px / 1.5rem
- **Container Max Width:** 1280px
- **Grid:** Standard 12-column responsive grid.

---

## 5. Component Patterns

### Navigation (Top Bar)
- **Background:** White (`#ffffff`) with a subtle bottom border.
- **Logo:** TechParts AI (Navy + Cyan AI icon).
- **Links:** Inter Body Medium, Tech Gray, active state in Navy with a bottom border indicator.

### Product Cards
- **Style:** Flat with thin border (`#d9dadb`).
- **Content:** Large clear photo, SKU badge, compatibility tag (Cyan), and price in Bold Navy.
- **Action:** Square-ish buttons with minimal radius.

### Buttons
- **Primary:** Background AI Cyan (`#00e5ff`), Text Navy (`#1a2b3c`), Bold.
- **Secondary:** Background Navy (`#1a2b3c`), Text White, Bold.
- **Outline:** Transparent background, Navy border, Navy text.

### Feedback Mechanism
- **Style:** Small, non-intrusive 👍/👎 icons next to AI responses to train the RAG model.

---

## 6. Implementation Notes

- **Framework:** Django Templates + htmx + Bootstrap.
- **Icons:** Material Symbols (Outlined style).
- **Animations:** Subtle transitions (200ms) for hover states. No heavy parallax or distractions.
