import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  // Fails loudly at startup rather than surfacing as a confusing runtime
  // error the first time an admin action hits Supabase.
  throw new Error(
    "Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY — copy .env.example to .env.local and fill in the local Supabase project's values.",
  );
}

// Single Supabase client for mission-control. RLS policies (keyed off
// tenant status flags) are the real access-control boundary — this client
// carries the signed-in admin's session, nothing more.
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
