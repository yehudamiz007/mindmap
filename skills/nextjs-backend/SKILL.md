---
name: nextjs-backend
description: Build Next.js 14 backend with API Routes, Supabase (Postgres), and NextAuth.js Google authentication. Use when building API endpoints, database queries, user authentication, protected routes, or full-stack Next.js apps with a real database. Covers Next.js App Router API routes, Supabase client setup, SQL queries, NextAuth Google OAuth, session handling, middleware, and environment variables. Triggers on phrases like "API route", "Supabase", "database", "authentication", "Google login", "backend", "NextAuth", "protected route", "full-stack".
---

# Next.js Backend Skill

## Stack

- **Next.js 14 API Routes** - `app/api/*/route.ts`
- **Supabase** - Postgres DB + Auth helpers (free tier)
- **NextAuth.js v5** - Google OAuth + session management
- **TypeScript** (preferred)

## Setup

### 1. Install dependencies
```bash
npm install @supabase/supabase-js next-auth@beta @auth/supabase-adapter
```

### 2. Environment variables (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
AUTH_SECRET=your-random-secret-here  # openssl rand -base64 32
AUTH_GOOGLE_ID=your-google-client-id
AUTH_GOOGLE_SECRET=your-google-client-secret
```

### 3. Supabase client
```ts
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Server-side only (full access)
export const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)
```

### 4. NextAuth config
```ts
// auth.ts (root level)
import NextAuth from 'next-auth'
import Google from 'next-auth/providers/google'

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  callbacks: {
    session({ session, token }) {
      if (session.user) session.user.id = token.sub!
      return session
    }
  }
})
```

```ts
// app/api/auth/[...nextauth]/route.ts
export { handlers as GET, handlers as POST } from '@/auth'
```

## API Route Patterns

### Basic GET/POST
```ts
// app/api/meals/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/auth'
import { supabaseAdmin } from '@/lib/supabase'

export async function GET(req: NextRequest) {
  const session = await auth()
  if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data, error } = await supabaseAdmin
    .from('meals')
    .select('*')
    .eq('user_id', session.user.id)
    .order('created_at', { ascending: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const body = await req.json()
  const { data, error } = await supabaseAdmin
    .from('meals')
    .insert({ ...body, user_id: session.user.id })
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data, { status: 201 })
}
```

### Dynamic route (by ID)
```ts
// app/api/meals/[id]/route.ts
export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  const session = await auth()
  if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { error } = await supabaseAdmin
    .from('meals')
    .delete()
    .eq('id', params.id)
    .eq('user_id', session.user.id)  // security: only own records

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return new NextResponse(null, { status: 204 })
}
```

## Middleware - Protect Routes

```ts
// middleware.ts (root level)
import { auth } from '@/auth'

export default auth((req) => {
  if (!req.auth && req.nextUrl.pathname.startsWith('/dashboard')) {
    return Response.redirect(new URL('/login', req.url))
  }
})

export const config = { matcher: ['/dashboard/:path*', '/api/meals/:path*'] }
```

## Supabase SQL - Common Patterns

```sql
-- Create meals table
CREATE TABLE meals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  calories INTEGER DEFAULT 0,
  protein FLOAT DEFAULT 0,
  carbs FLOAT DEFAULT 0,
  fat FLOAT DEFAULT 0,
  date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own meals" ON meals FOR ALL USING (user_id = auth.uid()::text);
```

## Client-side Auth (UI)

```tsx
'use client'
import { signIn, signOut, useSession } from 'next-auth/react'

export default function AuthButton() {
  const { data: session } = useSession()
  if (session) return (
    <div className="flex items-center gap-3">
      <span>{session.user?.name}</span>
      <button onClick={() => signOut()} className="text-red-400">יציאה</button>
    </div>
  )
  return <button onClick={() => signIn('google')} className="bg-violet-600 text-white px-4 py-2 rounded-xl">כניסה עם Google</button>
}
```

## Vercel Deployment

1. Push to GitHub
2. Import repo at https://vercel.com/new
3. Add all env vars in Vercel dashboard → Settings → Environment Variables
4. Add `https://your-app.vercel.app/api/auth/callback/google` to Google OAuth allowed redirects

## References

- See `references/supabase-patterns.md` for advanced DB queries and RLS patterns
- See `references/nextauth-setup.md` for Google OAuth console setup guide
