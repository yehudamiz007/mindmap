---
name: nextjs-frontend
description: Build and develop Next.js 14 frontend applications with React, Tailwind CSS, Chart.js, and Hebrew RTL support. Use when building UI components, pages, dashboards, forms, data visualizations, or full frontend apps with Next.js. Covers App Router, server/client components, Tailwind styling, Chart.js charts, RTL Hebrew layout, responsive design, and Vercel deployment. Triggers on phrases like "build a UI", "create a page", "Next.js component", "dashboard", "Hebrew app", "frontend app", "Tailwind", "React component".
---

# Next.js Frontend Skill

## Stack

- **Next.js 14** - App Router, Server/Client Components
- **Tailwind CSS** - Utility-first styling
- **Chart.js + react-chartjs-2** - Data visualizations
- **Hebrew RTL** - Full RTL support via `dir="rtl"` + Tailwind RTL
- **TypeScript** (preferred) or JavaScript

## Project Bootstrap

```bash
npx create-next-app@latest my-app --typescript --tailwind --app --src-dir
cd my-app
npm install chart.js react-chartjs-2
```

### tailwind.config.ts - RTL support
```ts
import type { Config } from 'tailwindcss'
export default {
  content: ['./src/**/*.{ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
} satisfies Config
```

### layout.tsx - Hebrew RTL root
```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <body className="bg-gray-950 text-gray-100 font-sans">{children}</body>
    </html>
  )
}
```

## Key Patterns

### Server Component (default)
```tsx
// app/page.tsx - runs on server, no 'use client'
export default async function Page() {
  const data = await fetch('/api/data').then(r => r.json())
  return <main>{/* render data */}</main>
}
```

### Client Component
```tsx
'use client'
import { useState } from 'react'
export default function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>
}
```

### Chart.js (Client Component required)
```tsx
'use client'
import { Bar } from 'react-chartjs-2'
import { Chart, CategoryScale, LinearScale, BarElement } from 'chart.js'
Chart.register(CategoryScale, LinearScale, BarElement)

export default function MyChart({ data }: { data: number[] }) {
  return (
    <Bar
      data={{ labels: ['ינואר','פברואר','מרץ'], datasets: [{ data, backgroundColor: '#7c6af7' }] }}
      options={{ responsive: true, plugins: { legend: { display: false } } }}
    />
  )
}
```

## Tailwind Dark Mode UI Patterns

```tsx
// Card
<div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 shadow-lg">

// Input (RTL)
<input className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-right focus:outline-none focus:border-violet-500" />

// Button Primary
<button className="bg-violet-600 hover:bg-violet-500 text-white px-6 py-2.5 rounded-xl font-semibold transition-colors">

// Progress Bar
<div className="h-2 bg-gray-800 rounded-full">
  <div className="h-full bg-violet-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
</div>
```

## Vercel Deployment

```bash
npm i -g vercel
vercel        # first deploy (follow prompts)
vercel --prod # production deploy
```

Or connect GitHub repo to Vercel dashboard for auto-deploy on push.

## References

- See `references/component-patterns.md` for reusable component examples
- See `references/rtl-guide.md` for Hebrew RTL layout tips
