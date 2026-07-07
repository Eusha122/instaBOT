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
