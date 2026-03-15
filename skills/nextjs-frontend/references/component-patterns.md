# Component Patterns

## Navigation (RTL)
```tsx
<nav className="flex items-center justify-between px-6 py-4 bg-gray-900 border-b border-gray-800">
  <div className="flex gap-6">
    <a href="/" className="text-violet-400 font-semibold">ראשי</a>
    <a href="/history" className="text-gray-400 hover:text-white">היסטוריה</a>
  </div>
  <span className="text-xl font-bold">🥗 האפליקציה שלי</span>
</nav>
```

## Stats Grid
```tsx
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  {stats.map(s => (
    <div key={s.label} className="bg-gray-900 rounded-2xl p-4 border border-gray-800">
      <div className="text-gray-400 text-sm mb-1">{s.label}</div>
      <div className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</div>
    </div>
  ))}
</div>
```

## Form with Validation
```tsx
'use client'
import { useState } from 'react'

export default function MealForm({ onSubmit }: { onSubmit: (data: any) => void }) {
  const [form, setForm] = useState({ name: '', calories: '' })
  const [error, setError] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name) { setError('נא למלא שם'); return }
    onSubmit(form)
    setForm({ name: '', calories: '' })
    setError('')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-red-400 text-sm">{error}</p>}
      <input
        value={form.name}
        onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
        placeholder="שם הארוחה"
        className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-right"
      />
      <button type="submit" className="w-full bg-violet-600 hover:bg-violet-500 text-white py-2.5 rounded-xl font-semibold">
        ✅ הוסף
      </button>
    </form>
  )
}
```

## Toast Notification
```tsx
'use client'
import { useState } from 'react'

export function useToast() {
  const [msg, setMsg] = useState('')
  function toast(text: string) {
    setMsg(text)
    setTimeout(() => setMsg(''), 2500)
  }
  const Toast = () => msg ? (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-violet-600 text-white px-6 py-2.5 rounded-full text-sm font-semibold shadow-lg z-50 animate-bounce">
      {msg}
    </div>
  ) : null
  return { toast, Toast }
}
```

## Empty State
```tsx
<div className="text-center py-16 text-gray-500">
  <div className="text-5xl mb-4">🍽️</div>
  <p className="text-lg">אין נתונים עדיין</p>
  <p className="text-sm mt-1">הוסף את הפריט הראשון שלך</p>
</div>
```
