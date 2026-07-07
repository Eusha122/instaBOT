import { cookies } from 'next/headers';

export const ADMIN_COOKIE = 'admin_auth';

// The cookie stores the admin password itself. It's httpOnly, so client-side
// JavaScript can never read it, and we compare it back to the server-only
// ADMIN_PASSWORD on every protected request. Not a full session system, but it
// keeps the secret out of the JS bundle and out of the database.
export async function isAdminRequest(): Promise<boolean> {
  const expected = process.env.ADMIN_PASSWORD;
  if (!expected) return false;
  const store = await cookies();
  return store.get(ADMIN_COOKIE)?.value === expected;
}
