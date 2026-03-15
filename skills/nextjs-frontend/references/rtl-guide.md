# Hebrew RTL Guide

## Basics
- Always set `dir="rtl"` on `<html>` and `lang="he"`
- Tailwind: use `space-x-reverse` for horizontal spacing in RTL
- Text inputs: add `className="text-right"` or `dir="rtl"`
- Flexbox: items flow right-to-left naturally with `dir="rtl"`

## RTL-Aware Tailwind Classes
```
ml-* → מרווח שמאל (בעברית: ימין הגיוני)
mr-* → מרווח ימין (בעברית: שמאל הגיוני)
ps-* / pe-* → padding-inline-start / end (RTL-aware ✅)
ms-* / me-* → margin-inline-start / end (RTL-aware ✅)
```

Prefer `ps-`, `pe-`, `ms-`, `me-` over `pl-`, `pr-`, `ml-`, `mr-` for RTL-safe layouts.

## Common RTL Issues & Fixes

### Flex row reverses direction
```tsx
// Problem: icons appear on wrong side
<div className="flex items-center gap-2">
  <Icon /> <span>טקסט</span>  // icon will be on RIGHT in RTL
</div>

// Solution: use flex-row-reverse if needed, or just let RTL handle it
```

### Number inputs
```tsx
// Numbers should still be LTR
<input dir="ltr" className="text-left" type="number" />
```

### Charts (Chart.js)
```tsx
// Chart.js is LTR by default - axis labels fine, text labels need care
options: {
  plugins: {
    legend: { rtl: true, textDirection: 'rtl' }
  }
}
```

### Date display
```tsx
// Hebrew locale formatting
new Date().toLocaleDateString('he-IL', { weekday: 'long', day: 'numeric', month: 'long' })
// → "יום ראשון, 15 במרץ"
```
