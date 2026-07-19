import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  // Fail loudly but don't crash the module graph — easier to debug a blank
  // screen with this in the console than a bundler-time error.
  // (createClient throws synchronously on an empty string, so we still need
  // to hand it harmless placeholders below to keep this promise.)
  console.error(
    "[{{PRODUCT_SLUG}}/pwa] Missing VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY. Copy .env.example to .env.local.",
  );
}

export const supabase = createClient(
  supabaseUrl || "http://localhost:54321",
  supabaseAnonKey || "public-anon-key-placeholder",
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      // Mobile PWA: no OAuth redirect URL to parse on boot by default. Flip
      // this on if/when a social-login redirect flow is added.
      detectSessionInUrl: false,
    },
  },
);
