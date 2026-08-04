---
name: Industrial Precision
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#44474c'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#74777d'
  outline-variant: '#c4c6cd'
  surface-tint: '#4f6073'
  primary: '#041627'
  on-primary: '#ffffff'
  primary-container: '#1a2b3c'
  on-primary-container: '#8192a7'
  inverse-primary: '#b7c8de'
  secondary: '#006875'
  on-secondary: '#ffffff'
  secondary-container: '#00e3fd'
  on-secondary-container: '#00616d'
  tertiary: '#0e171d'
  on-tertiary: '#ffffff'
  tertiary-container: '#222b32'
  on-tertiary-container: '#89929b'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d2e4fb'
  primary-fixed-dim: '#b7c8de'
  on-primary-fixed: '#0b1d2d'
  on-primary-fixed-variant: '#38485a'
  secondary-fixed: '#9cf0ff'
  secondary-fixed-dim: '#00daf3'
  on-secondary-fixed: '#001f24'
  on-secondary-fixed-variant: '#004f58'
  tertiary-fixed: '#dbe4ed'
  tertiary-fixed-dim: '#bfc8d0'
  on-tertiary-fixed: '#141d23'
  on-tertiary-fixed-variant: '#3f484f'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
  industrial-navy: '#1A2B3C'
  ai-cyan: '#00E5FF'
  tech-gray: '#495057'
  border-subtle: '#DEE2E6'
  success-green: '#28A745'
  danger-red: '#DC3545'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  technical-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.4'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: '1.2'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max-width: 1280px
---

## Brand & Style

The design system is engineered for a technical e-commerce environment where precision, reliability, and innovative support are paramount. It caters to a dual audience: specialized technicians requiring accurate specifications and everyday consumers seeking dependable repairs. 

The visual style is **Corporate / Modern** with a focus on high-utility information density. It prioritizes clarity and speed, reflecting an "Efficiency through Automation" philosophy. The interface uses generous whitespace to prevent cognitive overload during technical searches, while integrating AI-driven elements through a distinct, high-tech visual language.

- **Trust:** Established through a structured grid, sober industrial colors, and clear data hierarchy.
- **Precision:** Conveyed through sharp typography, consistent spacing units, and detailed metadata labels.
- **Innovation:** Represented by the strategic use of vibrant cyan accents and glassmorphic effects within AI interaction zones.

## Colors

The palette is rooted in an **Industrial Navy** primary color, evoking stability and professional authority. **Tech Gray** and its variants are used for secondary information, borders, and backgrounds to maintain a clean, utilitarian aesthetic.

The **AI Cyan** is a high-energy accent reserved exclusively for intelligence-driven features, such as the support chat, compatibility checkers, and automated insights. This color signals a shift from static catalog browsing to interactive, assisted experiences.

- **Primary:** Navigation, headings, and primary buttons.
- **Secondary (AI):** Chat triggers, AI icons, and "verified compatibility" badges.
- **Neutral:** Background surfaces and low-priority containers to allow product photography to stand out.

## Typography

This design system utilizes **Inter** for all primary UI interactions and headings due to its exceptional legibility and neutral, modern character. To emphasize technical precision, **JetBrains Mono** is introduced for specific technical attributes, SKU numbers, and manual references, providing a "blueprint" feel to the data.

- **Headings:** Use tighter letter spacing and heavy weights to anchor the page.
- **Body:** Standardized for readability in long product descriptions and technical manuals.
- **Labels:** Use `label-caps` for table headers and specification categories to create a clear visual distinction from the data itself.

## Layout & Spacing

The layout follows a **Fluid Grid** model built on a 12-column system, ensuring responsiveness for technicians using mobile devices in the field. A 4px base unit governs all spacing, creating a mathematical rhythm that reinforces the brand's focus on precision.

- **Desktop:** 12 columns with 24px gutters. Use fixed-width containers (1280px max) for the storefront to maintain focus, while using full-width fluid layouts for the internal Admin and Insights Dashboards.
- **Tablet:** 8 columns with 16px gutters.
- **Mobile:** 4 columns with 16px gutters and 16px side margins.
- **Vertical Rhythm:** Use larger gaps (48px+) between major sections to emphasize the "clean" aesthetic and prevent visual clutter.

## Elevation & Depth

Hierarchy is established primarily through **Tonal Layers** and **Low-Contrast Outlines** rather than heavy shadows. This maintains a flat, professional, and performance-oriented UI.

- **Surface Levels:** The main background is the lowest level (`neutral`). Product cards and dashboard widgets sit on a white surface with a subtle 1px border (`border-subtle`).
- **AI Focus:** The AI Chat interface uses **Glassmorphism**. A subtle backdrop blur with a very light `ai-cyan` tint distinguishes it as a modern, dynamic layer hovering over the static technical content.
- **Interaction:** On hover, interactive elements (like product cards) should transition to a very soft ambient shadow (0px 4px 12px rgba(0,0,0,0.05)) to indicate clickability without breaking the utilitarian feel.

## Shapes

The shape language is **Soft (Level 1)**. Elements like buttons and input fields use a 0.25rem (4px) radius. This provides a professional appearance that is more approachable than sharp corners but avoids the "playfulness" of highly rounded or pill-shaped designs.

- **Product Cards:** Use `rounded-lg` (8px) to softly frame imagery.
- **Action Buttons:** Use standard 4px rounding for a crisp, technical look.
- **AI Components:** The AI chat bubble or interface may use slightly more rounded corners (`rounded-xl` or 12px) to differentiate the "intelligent" organic software from the "hard" mechanical hardware items in the catalog.

## Components

### Buttons
- **Primary:** Solid `industrial-navy` with white text. High contrast for "Add to Cart."
- **AI Action:** Solid `ai-cyan` with `industrial-navy` text. Used for "Analyze Compatibility" or "Start Diagnostic."
- **Ghost:** `tech-gray` border and text. Used for filters and secondary actions.

### Product Cards
Clean, border-led cards. High-quality product image at the top, followed by the brand name in `label-caps`, then the product title in `headline-sm`. A dedicated "technical row" at the bottom uses `technical-data` (JetBrains Mono) for specs like voltage or dimensions.

### AI Chat Interface
A distinct docked component.
- **Header:** `ai-cyan` background to grab attention.
- **Messages:** User messages are simple gray bubbles; AI responses are white with a subtle `ai-cyan` glow or border.
- **Sources:** Every AI response must include a "Technical Source" tag—a small, monospace label that links directly to the manufacturer's PDF manual.

### Inputs & Tables
- **Inputs:** 1px `border-subtle` with a square-ish feel. Focused state uses an `industrial-navy` 2px border.
- **Data Tables:** High-density, no vertical lines, only horizontal `border-subtle` separators. Use `technical-data` font for all table values.

### Status Badges
- Small, uppercase labels with low-saturation background colors (e.g., light green background with dark green text) for statuses like "In Stock," "Draft," or "SLA Breached."