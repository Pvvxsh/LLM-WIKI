---
name: ui-ux-pro-max
displayName: UI/UX Pro Max
description: AI-powered design intelligence with 67 UI styles, 161 color palettes, 57 font pairings, 99 UX guidelines, 25 chart types, and 171 industry-specific reasoning rules across 17 tech stacks.
version: 2.6.2
author: NextLevelBuilder
platforms:
  - claude
  - cursor
  - windsurf
  - copilot
  - kiro
  - roocode
  - kilocode
  - codex
  - qoder
  - gemini
  - trae
  - opencode
  - continue
  - codebuddy
  - droid
  - warp
  - augment
  - antigravity
  - openclaw
tags:
  - ui
  - ux
  - design
  - design-system
  - color-palette
  - typography
  - accessibility
  - frontend
---

# UI/UX Pro Max

AI-powered design intelligence toolkit for building professional UI/UX across multiple platforms and frameworks.

## Trigger

Activate when user requests UI/UX work — build, design, create, implement, review, fix, or improve any user interface.

## Core Capabilities

### 1. Design System Generation (v2.0+)

Analyzes project requirements and generates a complete, tailored design system:

- **Pattern** — Landing page structure (Hero-Centric, Conversion-Optimized, Social Proof, etc.)
- **Style** — Best matching UI style from 67 options
- **Colors** — Industry-appropriate palette from 161 options
- **Typography** — Curated font pairing from 57 combinations
- **Key Effects** — Animations and interactions
- **Anti-patterns** — What NOT to do
- **Pre-delivery Checklist** — Validation checklist

### 2. Searchable Databases

All data stored in CSV files under `src/ui-ux-pro-max/data/`. Search via Python script:

```bash
python src/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain> [-n <max_results>]
```

**Available domains:**

| Domain | Description |
|--------|-------------|
| `product` | Product type recommendations (161 categories) |
| `style` | UI styles (67 styles) + AI prompts and CSS keywords |
| `typography` | Font pairings with Google Fonts imports |
| `color` | Color palettes by product type (161 palettes) |
| `landing` | Page structure and CTA strategies (24 patterns) |
| `chart` | Chart types and library recommendations (25 types) |
| `ux` | Best practices and anti-patterns (99 guidelines) |

**Stack-specific search:**

```bash
python src/ui-ux-pro-max/scripts/search.py "<query>" --stack <stack>
```

Available stacks: `html-tailwind` (default), `react`, `nextjs`, `astro`, `vue`, `nuxtjs`, `nuxt-ui`, `svelte`, `swiftui`, `react-native`, `flutter`, `shadcn`, `jetpack-compose`, `angular`, `laravel`, `javafx`

### 3. Industry-Specific Reasoning Rules (161 rules)

| Category | Examples |
|----------|----------|
| Tech & SaaS | SaaS, Micro SaaS, B2B Service, Developer Tool, AI/Chatbot Platform |
| Finance | Fintech/Crypto, Banking, Insurance, Personal Finance Tracker |
| Healthcare | Medical Clinic, Pharmacy, Dental, Veterinary, Mental Health |
| E-commerce | General, Luxury, Marketplace, Subscription Box, Food Delivery |
| Services | Beauty/Spa, Restaurant, Hotel, Legal, Home Services |
| Creative | Portfolio, Agency, Photography, Gaming, Music Streaming |
| Lifestyle | Habit Tracker, Recipe, Meditation, Weather, Diary |
| Emerging Tech | Web3/NFT, Spatial Computing, Quantum Computing |

## 67 UI Styles

### General Styles (49)

| # | Style | Best For |
|---|-------|----------|
| 1 | Minimalism & Swiss Style | Enterprise apps, dashboards |
| 2 | Neumorphism | Health/wellness apps |
| 3 | Glassmorphism | Modern SaaS, financial dashboards |
| 4 | Brutalism | Design portfolios, artistic projects |
| 5 | 3D & Hyperrealism | Gaming, product showcase |
| 6 | Vibrant & Block-based | Startups, creative agencies |
| 7 | Dark Mode (OLED) | Night-mode apps, coding platforms |
| 8 | Accessible & Ethical | Government, healthcare, education |
| 9 | Claymorphism | Educational apps, children's apps |
| 10 | Aurora UI | Modern SaaS, creative agencies |
| 11 | Retro-Futurism | Gaming, entertainment |
| 12 | Flat Design | Web apps, mobile apps |
| 13 | Skeuomorphism | Legacy apps, premium products |
| 14 | Liquid Glass | Premium SaaS, high-end e-commerce |
| 15 | Motion-Driven | Portfolio sites, storytelling |
| 16 | Micro-interactions | Mobile apps, touchscreen UIs |
| 17 | Inclusive Design | Public services, education |
| 18 | Zero Interface | Voice assistants, AI platforms |
| 19 | Soft UI Evolution | Modern enterprise apps |
| 20 | Neubrutalism | Gen Z brands, startups |
| 21 | Bento Box Grid | Dashboards, product pages |
| 22 | Y2K Aesthetic | Fashion brands, music, Gen Z |
| 23 | Cyberpunk UI | Gaming, tech products, crypto |
| 24 | Organic Biophilic | Wellness apps, sustainability |
| 25 | AI-Native UI | AI products, chatbots, copilots |
| 26 | Memphis Design | Creative agencies, youth brands |
| 27 | Vaporwave | Music platforms, gaming |
| 28 | Dimensional Layering | Dashboards, card layouts |
| 29 | Exaggerated Minimalism | Fashion, architecture |
| 30 | Kinetic Typography | Hero sections, marketing |
| 31 | Parallax Storytelling | Brand storytelling |
| 32 | Swiss Modernism 2.0 | Corporate sites, editorial |
| 33 | HUD / Sci-Fi FUI | Sci-fi games, cybersecurity |
| 34 | Pixel Art | Indie games, retro tools |
| 35 | Bento Grids | Product features, dashboards |
| 36 | Spatial UI (VisionOS) | Spatial computing, VR/AR |
| 37 | E-Ink / Paper | Reading apps, digital newspapers |
| 38 | Gen Z Chaos / Maximalism | Gen Z lifestyle, music |
| 39 | Biomimetic / Organic 2.0 | Sustainability tech, biotech |
| 40 | Anti-Polish / Raw Aesthetic | Creative portfolios |
| 41 | Tactile Digital / Deformable UI | Modern mobile apps |
| 42 | Nature Distilled | Wellness brands |
| 43 | Interactive Cursor Design | Creative portfolios |
| 44 | Voice-First Multimodal | Voice assistants, accessibility |
| 45 | 3D Product Preview | E-commerce, furniture |
| 46 | Gradient Mesh / Aurora Evolved | Hero sections, backgrounds |
| 47 | Editorial Grid / Magazine | News sites, blogs |
| 48 | Chromatic Aberration / RGB Split | Music platforms, gaming |
| 49 | Vintage Analog / Retro Film | Photography, vinyl brands |

### Landing Page Styles (8)

| # | Style | Best For |
|---|-------|----------|
| 1 | Hero-Centric Design | Products with strong visual identity |
| 2 | Conversion-Optimized | Lead generation, sales pages |
| 3 | Feature-Rich Showcase | SaaS, complex products |
| 4 | Minimal & Direct | Simple products, apps |
| 5 | Social Proof-Focused | Services, B2C products |
| 6 | Interactive Product Demo | Software, tools |
| 7 | Trust & Authority | B2B, enterprise, consulting |
| 8 | Storytelling-Driven | Brands, agencies, nonprofits |

### BI/Analytics Dashboard Styles (10)

| # | Style | Best For |
|---|-------|----------|
| 1 | Data-Dense Dashboard | Complex data analysis |
| 2 | Heat Map & Heatmap Style | Geographic/behavior data |
| 3 | Executive Dashboard | C-suite summaries |
| 4 | Real-Time Monitoring | Operations, DevOps |
| 5 | Drill-Down Analytics | Detailed exploration |
| 6 | Comparative Analysis Dashboard | Side-by-side comparisons |
| 7 | Predictive Analytics | Forecasting, ML insights |
| 8 | User Behavior Analytics | UX research, product analytics |
| 9 | Financial Dashboard | Finance, accounting |
| 10 | Sales Intelligence Dashboard | Sales teams, CRM |

## 17 Supported Tech Stacks

| Category | Stacks |
|----------|--------|
| Web (HTML) | HTML + Tailwind (default) |
| React Ecosystem | React, Next.js, shadcn/ui |
| Vue Ecosystem | Vue, Nuxt.js, Nuxt UI |
| Angular | Angular |
| PHP | Laravel (Blade, Livewire, Inertia.js) |
| Other Web | Svelte, Astro, Three.js |
| Desktop | JavaFX |
| iOS | SwiftUI |
| Android | Jetpack Compose |
| Cross-Platform | React Native, Flutter |

## 99 UX Guidelines

Covers best practices, anti-patterns, and accessibility rules including:

- No emojis as icons (use SVG: Heroicons/Lucide)
- cursor-pointer on all clickable elements
- Hover states with smooth transitions (150-300ms)
- Light mode: text contrast 4.5:1 minimum
- Focus states visible for keyboard nav
- prefers-reduced-motion respected
- Responsive breakpoints: 375px, 768px, 1024px, 1440px

## Architecture

```
src/ui-ux-pro-max/                # Source of Truth
├── data/                         # Canonical CSV databases
│   ├── products.csv, styles.csv, colors.csv, typography.csv, ...
│   └── stacks/                   # Stack-specific guidelines
├── scripts/
│   ├── search.py                 # CLI entry point
│   ├── core.py                   # BM25 + regex hybrid search engine
│   └── design_system.py          # Design system generation
└── templates/
    ├── base/                     # Base templates
    └── platforms/                # Platform configs
```

## Prerequisites

Python 3.x (no external dependencies required).

## Example Prompts

```
Build a landing page for my SaaS product
Create a dashboard for healthcare analytics
Design a portfolio website with dark mode
Make a mobile app UI for e-commerce
Build a fintech banking app with dark theme
```
