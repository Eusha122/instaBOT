'use client';
import { useState } from 'react';

export default function Home() {
  const [formData, setFormData] = useState({
    name: '',
    assistantName: 'Steve',
    sessionId: '',
    bio: ''
  });
  const [status, setStatus] = useState('');
  const [showGuide, setShowGuide] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('deploying');

    try {
      const res = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        console.error('Signup error:', data);
        setStatus('error');
        alert(data.error || 'Failed to save. Please try again.');
        return;
      }

      setStatus('success');
    } catch (err) {
      console.error('Signup request failed:', err);
      setStatus('error');
      alert('Network error. Please try again.');
    }
  };

  return (
    <div className="layout-wrapper">
      <div className="header-section">
        <h1>Your Personal AI Clone</h1>
        <p>
          Connect your Instagram account and let a customized AI assistant handle your DMs,
          learn your personality, and answer exactly how you would.
        </p>
      </div>

      <div className="form-card">
        <form onSubmit={handleSubmit}>

          <div className="form-group">
            <label htmlFor="name">Your Name</label>
            <input
              type="text"
              id="name"
              placeholder="e.g. Eusha Ibna Akbor"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="assistantName">Assistant Name</label>
            <input
              type="text"
              id="assistantName"
              placeholder="e.g. Steve"
              value={formData.assistantName}
              onChange={(e) => setFormData({...formData, assistantName: e.target.value})}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="sessionId">Instagram Session ID</label>
            <input
              type="password"
              id="sessionId"
              placeholder="e.g. 17668980636%3AjzoNR..."
              value={formData.sessionId}
              onChange={(e) => setFormData({...formData, sessionId: e.target.value})}
              required
            />
            <button
              type="button"
              onClick={() => setShowGuide((v) => !v)}
              style={{
                background: 'none',
                border: 'none',
                color: '#a78bfa',
                cursor: 'pointer',
                fontSize: '0.85rem',
                padding: '6px 0 0',
                textDecoration: 'underline',
              }}
            >
              {showGuide ? 'Hide guide' : "Where do I find my Session ID?"}
            </button>

            {showGuide && (
              <div
                style={{
                  marginTop: '12px',
                  padding: '16px 18px',
                  background: 'rgba(167, 139, 250, 0.08)',
                  border: '1px solid rgba(167, 139, 250, 0.25)',
                  borderRadius: '10px',
                  fontSize: '0.85rem',
                  lineHeight: 1.6,
                  color: '#cbd5e1',
                }}
              >
                <strong style={{ color: '#fff', display: 'block', marginBottom: '8px' }}>
                  How to get your Instagram Session ID (desktop browser)
                </strong>
                <ol style={{ margin: 0, paddingLeft: '20px', display: 'grid', gap: '6px' }}>
                  <li>
                    Open <strong>instagram.com</strong> in Chrome or Edge on a computer and{' '}
                    <strong>log in</strong> to the account you want the assistant to run.
                  </li>
                  <li>
                    Press <strong>F12</strong> (or right-click the page → <em>Inspect</em>) to open
                    Developer Tools.
                  </li>
                  <li>
                    Go to the <strong>Application</strong> tab. (If you don&apos;t see it, click the{' '}
                    <strong>&raquo;</strong> arrow at the top of the DevTools panel.)
                  </li>
                  <li>
                    In the left sidebar, expand <strong>Cookies</strong> and click{' '}
                    <strong>https://www.instagram.com</strong>.
                  </li>
                  <li>
                    In the list, find the row named <strong>sessionid</strong>.
                  </li>
                  <li>
                    Double-click its <strong>Value</strong>, select all of it, copy it, and paste it
                    into the field above.
                  </li>
                </ol>
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="bio">Your Knowledge Base <span className="muted">(Facts, Rules, Vibes)</span></label>
            <textarea
              id="bio"
              rows={4}
              placeholder="Tell your AI assistant everything it needs to know to pretend to be you..."
              value={formData.bio}
              onChange={(e) => setFormData({...formData, bio: e.target.value})}
              required
            ></textarea>
          </div>

          <button type="submit" className="btn-submit" disabled={status === 'deploying'}>
            {status === 'deploying' ? 'Deploying...' :
             status === 'success' ? 'Deployed Successfully!' :
             'Deploy My Assistant'}
          </button>
        </form>
      </div>
    </div>
  );
}
