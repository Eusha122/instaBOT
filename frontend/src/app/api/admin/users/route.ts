import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseAdmin';
import { isAdminRequest } from '@/lib/adminAuth';

export async function GET() {
  if (!(await isAdminRequest())) {
    return NextResponse.json({ error: 'Unauthorized.' }, { status: 401 });
  }

  const { data, error } = await supabaseAdmin.from('users').select('*');

  if (error) {
    console.error('Admin users fetch error:', error);
    return NextResponse.json({ error: 'Failed to load users.' }, { status: 500 });
  }

  return NextResponse.json({ users: data ?? [] });
}

export async function PATCH(request: NextRequest) {
  if (!(await isAdminRequest())) {
    return NextResponse.json({ error: 'Unauthorized.' }, { status: 401 });
  }

  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid request body.' }, { status: 400 });
  }

  const id = typeof body.id === 'string' ? body.id : '';
  if (!id) {
    return NextResponse.json({ error: 'Missing user id.' }, { status: 400 });
  }

  const updates: Record<string, string> = {};
  if (typeof body.proxy === 'string') updates.proxy = body.proxy.trim();
  if (typeof body.bio === 'string') updates.bio = body.bio;
  if (typeof body.assistant_name === 'string') updates.assistant_name = body.assistant_name.trim();

  if (Object.keys(updates).length === 0) {
    return NextResponse.json({ error: 'Nothing to update.' }, { status: 400 });
  }

  const { error } = await supabaseAdmin.from('users').update(updates).eq('id', id);
  if (error) {
    console.error('Admin user update error:', error);
    return NextResponse.json({ error: 'Failed to update user.' }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}

export async function DELETE(request: NextRequest) {
  if (!(await isAdminRequest())) {
    return NextResponse.json({ error: 'Unauthorized.' }, { status: 401 });
  }

  const id = request.nextUrl.searchParams.get('id');
  if (!id) {
    return NextResponse.json({ error: 'Missing user id.' }, { status: 400 });
  }

  const { error } = await supabaseAdmin.from('users').delete().eq('id', id);
  if (error) {
    console.error('Admin user delete error:', error);
    return NextResponse.json({ error: 'Failed to delete user.' }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
