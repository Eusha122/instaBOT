import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Server-only Supabase client using the SERVICE ROLE key.
// This bypasses Row Level Security, so it must NEVER be imported into a
// client component. Only use it inside route handlers / server code.
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

const globalForAdmin = globalThis as unknown as { supabaseAdmin?: SupabaseClient };

export const supabaseAdmin =
  globalForAdmin.supabaseAdmin ??
  createClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

globalForAdmin.supabaseAdmin = supabaseAdmin;
