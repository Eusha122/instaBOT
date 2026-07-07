import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseAdmin';

export async function POST(request: NextRequest) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid request body.' }, { status: 400 });
  }

  const name = typeof body.name === 'string' ? body.name.trim() : '';
  const assistantName =
    typeof body.assistantName === 'string' ? body.assistantName.trim() : '';
  const sessionId = typeof body.sessionId === 'string' ? body.sessionId.trim() : '';
  const bio = typeof body.bio === 'string' ? body.bio.trim() : '';

  if (!name || !assistantName || !sessionId || !bio) {
    return NextResponse.json(
      { error: 'All fields are required.' },
      { status: 400 }
    );
  }

  // Basic sanity limits so a single submission can't dump megabytes into the DB.
  if (name.length > 100 || assistantName.length > 100 || bio.length > 10000) {
    return NextResponse.json({ error: 'One or more fields are too long.' }, { status: 400 });
  }

  const { error } = await supabaseAdmin.from('users').insert([
    {
      name,
      assistant_name: assistantName,
      session_id: sessionId,
      bio,
    },
  ]);

  if (error) {
    console.error('Signup insert error:', error);
    return NextResponse.json({ error: 'Failed to save. Please try again.' }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
