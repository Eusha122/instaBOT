'use client';
import { useState } from 'react';

export default function AdminDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visibleSessions, setVisibleSessions] = useState<{[key: string]: boolean}>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [viewingKb, setViewingKb] = useState<any | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoggingIn(true);
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(data.error || 'Incorrect Password');
        return;
      }
      setPassword('');
      setIsAuthenticated(true);
      fetchUsers();
    } catch {
      alert('Network error. Please try again.');
    } finally {
      setLoggingIn(false);
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/admin/users');
      if (!res.ok) {
        if (res.status === 401) setIsAuthenticated(false);
        console.error('Error fetching users:', await res.text());
        setUsers([]);
      } else {
        const data = await res.json();
        setUsers(data.users || []);
      }
    } catch (err) {
      console.error('Error fetching users:', err);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (userId: string, userName: string) => {
    if (window.confirm(`Are you sure you want to delete ${userName}? This will permanently stop their bot.`)) {
      try {
        const res = await fetch(`/api/admin/users?id=${encodeURIComponent(userId)}`, {
          method: 'DELETE',
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          alert(data.error || 'Failed to delete user.');
          return;
        }
        setUsers(users.filter(u => u.id !== userId));
      } catch {
        alert('Network error. Please try again.');
      }
    }
  };

  const handleCopySession = async (userId: string, sessionId: string) => {
    try {
      await navigator.clipboard.writeText(sessionId);
    } catch {
      // Clipboard API can be unavailable on non-HTTPS origins; fall back to a hidden textarea
      const textarea = document.createElement('textarea');
      textarea.value = sessionId;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
    setCopiedId(userId);
    setTimeout(() => setCopiedId(prev => (prev === userId ? null : prev)), 1500);
  };

  const toggleSessionVisibility = (userId: string) => {
    setVisibleSessions(prev => ({
      ...prev,
      [userId]: !prev[userId]
    }));
  };

  if (!isAuthenticated) {
    return (
      <div className="layout-wrapper flex items-center justify-center" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <div className="form-card" style={{ maxWidth: '400px', width: '100%' }}>
          <h2 style={{ textAlign: 'center', marginBottom: '20px', color: '#fff' }}>Admin Access</h2>
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label>Password</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter admin password"
                required
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #333', background: 'rgba(255,255,255,0.05)', color: '#fff' }}
              />
            </div>
            <button type="submit" disabled={loggingIn} className="btn-submit" style={{ width: '100%', padding: '12px', marginTop: '10px', borderRadius: '8px', background: '#3b82f6', color: '#fff', border: 'none', cursor: loggingIn ? 'not-allowed' : 'pointer', fontWeight: 'bold', opacity: loggingIn ? 0.7 : 1 }}>
              {loggingIn ? 'Logging in...' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', color: '#fff', padding: '40px 20px', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
          <div>
            <h1 style={{ fontSize: '2.5rem', fontWeight: '800', background: 'linear-gradient(to right, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', color: 'transparent', margin: 0 }}>
              Bot Manager
            </h1>
            <p style={{ color: '#888', marginTop: '8px' }}>Manage all active Instagram AI Clones running on the VPS.</p>
          </div>
          <button 
            onClick={fetchUsers}
            style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '10px 20px', borderRadius: '8px', color: '#fff', cursor: 'pointer' }}>
            Refresh Data
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px', color: '#888' }}>Loading users...</div>
        ) : users.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '50px', color: '#888', background: 'rgba(255,255,255,0.03)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.1)' }}>
            No active bots running right now.
          </div>
        ) : (
          <div style={{ overflowX: 'auto', background: 'rgba(255,255,255,0.03)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#a3a3a3', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '20px' }}>User Name</th>
                  <th style={{ padding: '20px' }}>Assistant</th>
                  <th style={{ padding: '20px' }}>Session ID</th>
                  <th style={{ padding: '20px' }}>Knowledge Base</th>
                  <th style={{ padding: '20px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '20px', fontWeight: 'bold' }}>
                      {user.name}
                      {user.status === 'session_invalid' && (
                        <span
                          title="This account's Instagram session expired. The user needs to submit a fresh Session ID."
                          style={{
                            display: 'inline-block',
                            marginLeft: '8px',
                            padding: '2px 8px',
                            fontSize: '0.7rem',
                            fontWeight: 'bold',
                            color: '#fca5a5',
                            background: 'rgba(239, 68, 68, 0.15)',
                            border: '1px solid rgba(239, 68, 68, 0.3)',
                            borderRadius: '999px',
                            verticalAlign: 'middle',
                          }}>
                          Session expired
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '20px', color: '#a78bfa' }}>{user.assistant_name}</td>
                    <td style={{ padding: '20px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ 
                          fontFamily: 'monospace', 
                          fontSize: '0.85rem',
                          color: '#888',
                          background: 'rgba(0,0,0,0.3)',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          filter: visibleSessions[user.id] ? 'none' : 'blur(4px)',
                          transition: 'filter 0.2s',
                          maxWidth: '150px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          display: 'inline-block'
                        }}>
                          {user.session_id}
                        </span>
                        <button
                          onClick={() => toggleSessionVisibility(user.id)}
                          style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', fontSize: '0.8rem', textDecoration: 'underline' }}>
                          {visibleSessions[user.id] ? 'Hide' : 'Show'}
                        </button>
                        <button
                          onClick={() => handleCopySession(user.id, user.session_id)}
                          style={{
                            background: copiedId === user.id ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255,255,255,0.08)',
                            border: '1px solid rgba(255,255,255,0.15)',
                            color: copiedId === user.id ? '#22c55e' : '#ccc',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            transition: 'all 0.2s',
                            whiteSpace: 'nowrap'
                          }}>
                          {copiedId === user.id ? 'Copied!' : 'Copy'}
                        </button>
                      </div>
                    </td>
                    <td style={{ padding: '20px', maxWidth: '300px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{
                          fontSize: '0.85rem',
                          color: '#a3a3a3',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          flex: 1
                        }}>
                          {user.bio}
                        </div>
                        <button
                          onClick={() => setViewingKb(user)}
                          style={{
                            background: 'rgba(96, 165, 250, 0.1)',
                            border: '1px solid rgba(96, 165, 250, 0.3)',
                            color: '#60a5fa',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            whiteSpace: 'nowrap'
                          }}>
                          View
                        </button>
                      </div>
                    </td>
                    <td style={{ padding: '20px', textAlign: 'right' }}>
                      <button 
                        onClick={() => handleDelete(user.id, user.name)}
                        style={{ 
                          background: 'rgba(239, 68, 68, 0.1)', 
                          border: '1px solid rgba(239, 68, 68, 0.3)', 
                          color: '#ef4444', 
                          padding: '8px 16px', 
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                          transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'}
                        onMouseOut={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'}
                      >
                        Delete & Stop Bot
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {viewingKb && (
          <div
            onClick={() => setViewingKb(null)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0,0,0,0.7)',
              backdropFilter: 'blur(4px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              padding: '20px'
            }}>
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                background: '#141414',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '16px',
                maxWidth: '700px',
                width: '100%',
                maxHeight: '80vh',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
              }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: '1.2rem', color: '#fff' }}>Knowledge Base</h2>
                  <p style={{ margin: '4px 0 0', color: '#888', fontSize: '0.85rem' }}>
                    {viewingKb.name} &middot; {viewingKb.assistant_name}
                  </p>
                </div>
                <button
                  onClick={() => setViewingKb(null)}
                  style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff', width: '32px', height: '32px', borderRadius: '8px', cursor: 'pointer', fontSize: '1rem' }}>
                  ✕
                </button>
              </div>
              <div style={{ padding: '24px', overflowY: 'auto' }}>
                <pre style={{
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontFamily: 'monospace',
                  fontSize: '0.85rem',
                  color: '#d4d4d4',
                  lineHeight: 1.6
                }}>
                  {viewingKb.bio || 'No knowledge base set for this bot.'}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
