import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ClientIntake } from './ClientIntake';
import { ParalegalDashboard } from './ParalegalDashboard';
import { Shield, MessageSquareText, Users, HeartHandshake } from 'lucide-react';
import './style.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'client' | 'paralegal'>('client');
  const [cases, setCases] = useState<any[]>([]);

  const fetchCases = async () => {
    try {
      const res = await axios.get('/api/cases/');
      setCases(res.data);
    } catch (err) {
      console.error('Failed to fetch cases:', err);
    }
  };

  useEffect(() => {
    fetchCases();
    // Poll cases every 10 seconds for real-time paralegal queue updates
    const interval = setInterval(fetchCases, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* HEADER / NAVIGATION */}
      <header className="navbar">
        <div className="logo-area">
          <div className="logo-mark">
            অ
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="brand-title">অধিকার (Odhikar)</span>
              <span className="brand-badge">BRAC Legal Aid</span>
            </div>
            <div className="brand-subtitle">AI Paralegal · আইনি সহায়তা ও অধিকার সেবা</div>
          </div>
        </div>

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
      </header>

      {/* MAIN BODY */}
      <main className={`main-content ${activeTab === 'client' ? 'client-mode' : 'paralegal-mode'}`}>
        {activeTab === 'client' ? (
          <ClientIntake onCaseSubmitted={fetchCases} />
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
