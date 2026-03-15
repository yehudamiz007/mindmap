# Supabase Patterns

## Aggregations & Stats
```ts
// Sum calories for a day
const { data } = await supabaseAdmin
  .from('meals')
  .select('calories.sum(), protein.sum(), carbs.sum(), fat.sum()')
  .eq('user_id', userId)
  .eq('date', '2026-03-15')
  .single()
```

## Date Range Query
```ts
const { data } = await supabaseAdmin
  .from('meals')
  .select('*')
  .eq('user_id', userId)
  .gte('date', '2026-03-01')
  .lte('date', '2026-03-31')
  .order('date', { ascending: false })
```

## Upsert (Insert or Update)
```ts
const { data } = await supabaseAdmin
  .from('daily_goals')
  .upsert({ user_id: userId, calories: 2000, protein: 150 }, { onConflict: 'user_id' })
  .select()
  .single()
```

## Real-time Subscription (Client)
```ts
import { supabase } from '@/lib/supabase'

useEffect(() => {
  const channel = supabase
    .channel('meals-changes')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'meals' }, payload => {
      console.log('Change:', payload)
      refetch()
    })
    .subscribe()
  return () => { supabase.removeChannel(channel) }
}, [])
```

## Common Tables Schema

```sql
-- Users goals
CREATE TABLE user_goals (
  user_id TEXT PRIMARY KEY,
  calories INTEGER DEFAULT 2000,
  protein FLOAT DEFAULT 150,
  carbs FLOAT DEFAULT 200,
  fat FLOAT DEFAULT 65,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quick meals presets
CREATE TABLE quick_meals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  calories INTEGER DEFAULT 0,
  protein FLOAT DEFAULT 0,
  carbs FLOAT DEFAULT 0,
  fat FLOAT DEFAULT 0
);
```

## Error Handling Pattern
```ts
const { data, error } = await supabaseAdmin.from('meals').select('*')
if (error) {
  console.error('Supabase error:', error.message)
  return NextResponse.json({ error: 'שגיאת מסד נתונים' }, { status: 500 })
}
```
