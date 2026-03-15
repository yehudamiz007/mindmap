# Google OAuth Setup Guide

## Step 1 - Google Cloud Console

1. Go to https://console.cloud.google.com
2. Create new project (or select existing)
3. APIs & Services → OAuth consent screen
   - User type: External
   - Fill app name, support email
   - Add scope: `email`, `profile`
4. APIs & Services → Credentials → Create Credentials → OAuth Client ID
   - Application type: **Web application**
   - Authorized redirect URIs:
     - `http://localhost:3000/api/auth/callback/google` (dev)
     - `https://your-app.vercel.app/api/auth/callback/google` (prod)
5. Copy **Client ID** and **Client Secret**

## Step 2 - Environment Variables

```env
AUTH_GOOGLE_ID=123456789-abc.apps.googleusercontent.com
AUTH_GOOGLE_SECRET=GOCSPX-xxxxx
AUTH_SECRET=run-openssl-rand-base64-32-to-generate
```

## Step 3 - Generate AUTH_SECRET

```bash
openssl rand -base64 32
```

## Step 4 - Vercel Production

In Vercel dashboard → Project → Settings → Environment Variables:
- Add all 5 env vars (SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, AUTH_SECRET, AUTH_GOOGLE_ID, AUTH_GOOGLE_SECRET)
- Redeploy after adding vars

## Troubleshooting

- **redirect_uri_mismatch**: Make sure the exact URL is in Google Console authorized redirects
- **Session undefined**: Wrap app in `<SessionProvider>` from `next-auth/react`
- **AUTH_SECRET missing**: Generate and add to both `.env.local` and Vercel
