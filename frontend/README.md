# Command Center Frontend - Real-Time Civic Disruption Early-Warning System

This sub-project implements the **Welcome Landing Page** & **Operations Command Center Dashboard** for the Real-Time Civic Disruption Early-Warning System, built with **React (Vite), React Router, Tailwind CSS, Framer Motion, Leaflet.js**, and **WebSockets**.

---

## 🎨 Design System & Palette

> "Designed to mirror mission-critical disaster response and operations command rooms, this UI rejects generic SaaS admin templates in favor of a high-contrast, dark desaturated navy palette (`#080C10` base, `#0D1117` surface) with severe signals that visually pop against a calm baseline. Typography leverages geometric **Space Grotesk** for display headers and crisp **JetBrains Mono** telemetry numerics for coordinates, trust scores, and timestamps."

---

## 🗺 Client-Side Routing & Page Transitions

The frontend includes client-side routing via `react-router-dom` with Framer Motion `AnimatePresence` page transitions:

- **Welcome / Landing Page** ([`/`](http://localhost:5173/)): The first screen a visitor sees upon entering the platform. Features an ambient animated signal grid with blooming radar pings, staggered typography entrance sequence (< 1.2s), and a tactile **"ENTER COMMAND CENTER"** CTA button.
- **Live Command Center Dashboard** ([`/dashboard`](http://localhost:5173/dashboard)): The full-screen operational monitoring view with dark CartoDB Leaflet map, floating real-time alert feed, slide-in signal trace drawer, and live scenario simulation panel.

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Vite Development Server
Launch the server:

```bash
npm run dev
```

Open your browser at `http://localhost:5173` to view the Welcome Landing Page, or navigate directly to `http://localhost:5173/dashboard` to preview the live command center dashboard.

---

## ⚙️ Flipping `USE_MOCK_DATA` (Mock vs. Live Backend Mode)

By default, the application runs with `USE_MOCK_DATA = false` in [`src/config.ts`](file:///d:/edA/frontend/src/config.ts) for production Docker integration. To test standalone in mock mode, set `USE_MOCK_DATA = true`:

```typescript
export const CONFIG = {
  // Set to true for standalone mock mode, or false for live FastAPI/WebSocket connection
  USE_MOCK_DATA: false,

  API_BASE_URL: '/api',
  WS_URL: 'ws://localhost:5173/ws/alerts',
};
```
