import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Reuse one client across pages and across dev hot-reloads to avoid
// "Multiple GoTrueClient instances" warnings and auth-storage races.
const globalForSupabase = globalThis as unknown as { supabase?: SupabaseClient };

export const supabase =
  globalForSupabase.supabase ?? createClient(supabaseUrl, supabaseAnonKey);

globalForSupabase.supabase = supabase;
