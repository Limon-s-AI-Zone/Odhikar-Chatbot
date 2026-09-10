import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ClientIntake } from './ClientIntake';
import { ParalegalDashboard } from './ParalegalDashboard';
import { Shield, MessageSquareText, Users, HeartHandshake, Wifi, WifiOff, AlertTriangle, RefreshCw, X } from 'lucide-react';
import './style.css';

interface LlmStatusState {
  connected: boolean;
  model?: string;
  status_code?: number;
  title?: string;
  message_bn?: string;
  message_en?: string;
  error_type?: string;
  raw_error?: string;
  troubleshooting_bn?: string[];
  provider_name?: string;
}

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'client' | 'paralegal'>('client');
  const [cases, setCases] = useState<any[]>([]);
  const [llmStatus, setLlmStatus] = useState<LlmStatusState | null>(null);
  const [showStatusModal, setShowStatusModal] = useState<boolean>(false);
  const [isCheckingLlm, setIsCheckingLlm] = useState<boolean>(false);

  const fetchCases = async () => {
    try {
      const res = await axios.get('/api/cases/');
      setCases(res.data);
    } catch (err) {
      console.error('Failed to fetch cases:', err);
    }
  };

  const fetchLlmStatus = async () => {
    setIsCheckingLlm(true);
    try {
      const res = await axios.get('/api/llm/status');
      setLlmStatus(res.data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setLlmStatus({
          connected: false,
          status_code: 401,
          error_type: 'authentication_error',
          title: 'LLM অথেন্টিকেশন ত্রুটি (401)',
          message_bn: 'API Key বা টোকেন সঠিক নয় অথবা মেয়াদোত্তীর্ণ। backend/.env পরীক্ষা করুন।'
        });
      } else {
        setLlmStatus({
          connected: false,
          status_code: 503,
          error_type: 'connection_error',
          title: 'LLM সংযোগ বিচ্ছিন্ন (Not Connected)',
          message_bn: 'এআই সার্ভারের সাথে সংযোগ করা যাচ্ছে না। সার্ভার ও ইন্টারনেট যাচাই করুন।'
        });
      }
    } finally {
      setIsCheckingLlm(false);
    }
  };

  useEffect(() => {
    fetchCases();
    fetchLlmStatus();
    // Poll cases and LLM status every 15 seconds
    const interval = setInterval(() => {
      fetchCases();
      fetchLlmStatus();
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* HEADER / NAVIGATION */}
      <header className="navbar">
        <div className="logo-area">
          <div style={{ backgroundColor: '#d92d20', color: 'white', padding: '6px 10px', borderRadius: '8px', fontWeight: '800', fontSize: '18px' }}>
            অ
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="brand-title">অধিকার (Odhikar)</span>
              <span className="logo-tag">BRAC Legal Aid</span>
            </div>
            <div className="brand-subtitle">AI Paralegal for Legal Aid Clients</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {/* LLM Status Badge */}
          {llmStatus && (
            <button
              onClick={() => setShowStatusModal(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '600',
                border: llmStatus.connected ? '1px solid #bbf7d0' : '1px solid #fecdd3',
                backgroundColor: llmStatus.connected ? '#f0fdf4' : '#fff1f2',
                color: llmStatus.connected ? '#15803d' : '#be123c',
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
              }}
              title="এআই সংযোগ স্থিতি ও বিস্তারিত দেখতে ক্লিক করুন"
            >
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: llmStatus.connected ? '#16a34a' : '#e11d48',
                  display: 'inline-block'
                }}
              />
              {llmStatus.connected ? (
                <span>LLM সংযুক্ত ({llmStatus.model?.split('/')[1] || 'Online'})</span>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <AlertTriangle size={13} />
                  {llmStatus.status_code === 401 ? 'LLM 401 ত্রুটি' : llmStatus.status_code === 429 ? 'টোকেন কোটা শেষ (429)' : 'LLM সংযোগহীন'}
                </span>
              )}
            </button>
          )}

          <nav className="nav-links">
            <button
              className={`nav-btn ${activeTab === 'client' ? 'active' : ''}`}
              onClick={() => setActiveTab('client')}
            >
              <MessageSquareText size={18} />
              ক্লায়েন্ট সেবা (Client Intake)
            </button>
            <button
              className={`nav-btn ${activeTab === 'paralegal' ? 'active' : ''}`}
              onClick={() => setActiveTab('paralegal')}
            >
              <Users size={18} />
              প্যারালিগ্যাল ড্যাশবোর্ড ({cases.length})
            </button>
          </nav>
        </div>
      </header>

      {/* LLM Status Details Modal */}
      {showStatusModal && llmStatus && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 999,
          padding: '20px'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            maxWidth: '520px',
            width: '100%',
            padding: '24px',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)',
            border: llmStatus.connected ? '1px solid #bbf7d0' : '1px solid #fecdd3'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                {llmStatus.connected ? (
                  <div style={{ backgroundColor: '#dcfce7', color: '#15803d', padding: '8px', borderRadius: '8px' }}>
                    <Wifi size={22} />
                  </div>
                ) : (
                  <div style={{ backgroundColor: '#ffe4e6', color: '#be123c', padding: '8px', borderRadius: '8px' }}>
                    <WifiOff size={22} />
                  </div>
                )}
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a', margin: 0 }}>
                    {llmStatus.title || (llmStatus.connected ? 'LLM সংযুক্ত' : 'LLM ত্রুটি')}
                  </h3>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>
                    মডেল: <code>{llmStatus.model || 'Unknown'}</code> · কোড: {llmStatus.status_code || (llmStatus.connected ? '200 OK' : 'Error')}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowStatusModal(false)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={20} />
              </button>
            </div>

            <p style={{ fontSize: '14px', lineHeight: '1.6', color: '#334155', marginBottom: '16px' }}>
              {llmStatus.message_bn}
            </p>

            {llmStatus.message_en && (
              <div style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                padding: '10px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#475569',
                marginBottom: '16px',
                fontFamily: 'monospace'
              }}>
                {llmStatus.message_en}
              </div>
            )}

            {!llmStatus.connected && (
              <div style={{ backgroundColor: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', fontWeight: '700', color: '#9f1239', marginBottom: '4px' }}>
                  সম্ভাব্য সমাধান (Troubleshooting):
                </div>
                <ul style={{ fontSize: '12px', color: '#881337', margin: 0, paddingLeft: '18px', lineHeight: '1.6' }}>
                  {llmStatus.troubleshooting_bn && llmStatus.troubleshooting_bn.length > 0 ? (
                    llmStatus.troubleshooting_bn.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))
                  ) : llmStatus.status_code === 401 ? (
                    <li><code>backend/.env</code> ফাইলে আপনার মডেল সেটিংস বা API কী (Vertex AI / OpenRouter) পরীক্ষা করুন।</li>
                  ) : llmStatus.status_code === 429 ? (
                    <li>টোকেন রেট লিমিট বা কোটা শেষ হয়েছে। কিছুক্ষণ পর পুনরায় চেষ্টা করুন।</li>
                  ) : (
                    <li>ইন্টারনেট ও ব্যাকএন্ড সার্ভার (Port 8000) অথবা লোকাল এলএলএম সার্ভার সচল আছে কি না পরীক্ষা করুন।</li>
                  )}
                </ul>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                className="btn btn-outline"
                style={{ fontSize: '13px', padding: '8px 16px' }}
                onClick={() => setShowStatusModal(false)}
              >
                বন্ধ করুন
              </button>
              <button
                className="btn btn-primary"
                style={{ fontSize: '13px', padding: '8px 16px' }}
                disabled={isCheckingLlm}
                onClick={fetchLlmStatus}
              >
                <RefreshCw className={isCheckingLlm ? 'animate-spin' : ''} size={14} />
                {isCheckingLlm ? 'যাচাই হচ্ছে...' : 'পুনরায় যাচাই করুন'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MAIN BODY */}
      <main className="main-content">
        {activeTab === 'client' ? (
          <div>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a' }}>
                আইনি অভিযোগ ভয়েস ও টেক্সট গ্রহণ সেবা
              </h2>
              <p style={{ fontSize: '14px', color: '#64748b' }}>
                সহজ সাধারণ বাংলায় আপনার ঘটনা বলুন বা লিখুন — আমাদের সিস্টেম আপনার অভিযোগ প্রস্তুত করবে।
              </p>
            </div>
            <ClientIntake onCaseSubmitted={fetchCases} />
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a' }}>
                প্যারালিগ্যাল ও সমন্বয়ক ড্যাশবোর্ড
              </h1>
              <p style={{ fontSize: '14px', color: '#64748b' }}>
                আগত অভিযোগসমূহের সারসংক্ষেপ পর্যালোচনা ও অনুমোদনের ইন্টারফেস (Human-in-the-Loop)।
              </p>
            </div>
            <ParalegalDashboard cases={cases} onRefresh={fetchCases} />
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
