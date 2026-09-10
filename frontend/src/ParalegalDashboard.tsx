import React, { useState } from 'react';
import axios from 'axios';
import { 
  AlertCircle, Clock, Check, Edit3, MessageSquare, 
  User, Bot, ShieldCheck, ChevronDown, ChevronUp 
} from 'lucide-react';

interface ChatMessage {
  role: string;
  content: string;
  timestamp?: string;
}

interface CaseItem {
  id: number;
  category: string;
  status: string;
  received_at: string;
  applicant_name: string;
  respondent: string;
  marriage_date?: string;
  marriage_date_inferred?: boolean;
  dower_amount?: string;
  dowry_paid?: string;
  unpaid_wages_claim?: string;
  current_status?: string;
  evidence?: string;
  safety_flag?: string;
  original_transcript?: string;
  draft_complaint?: string;
  referral_clinic?: string;
  referral_slot?: string;
  chat_history?: ChatMessage[];
}

interface DashboardProps {
  cases: CaseItem[];
  onRefresh: () => void;
}

export const ParalegalDashboard: React.FC<DashboardProps> = ({ cases, onRefresh }) => {
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(cases[0] || null);
  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraft, setEditedDraft] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [showFullChat, setShowFullChat] = useState(true);

  const handleSelectCase = (c: CaseItem) => {
    setSelectedCase(c);
    setEditedDraft(c.draft_complaint || '');
    setIsEditingDraft(false);
  };

  const handleSaveDraft = async () => {
    if (!selectedCase) return;
    setIsUpdating(true);
    try {
      const res = await axios.put(`/api/cases/${selectedCase.id}`, {
        draft_complaint: editedDraft,
        status: 'Approved'
      });
      setSelectedCase(res.data);
      setIsEditingDraft(false);
      onRefresh();
      alert('খসড়া সফলভাবে হালনাগাদ ও অনুমোদন করা হয়েছে!');
    } catch (err) {
      console.error(err);
      alert('হালনাগাদ করতে ব্যর্থ হয়েছে।');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="dashboard-grid">
      {/* LEFT COLUMN: CASE QUEUE */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '700' }}>
            আগত মামলার তালিকা ({cases.length})
          </h2>
          <button className="btn btn-outline" style={{ fontSize: '13px', padding: '6px 12px' }} onClick={onRefresh}>
            রিফ্রেশ
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {cases.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', color: '#64748b' }}>
              বর্তমানে কোনো নতুন মামলা নেই।
            </div>
          ) : (
            cases.map((c) => {
              const isUrgent = c.status === 'URGENT';
              const isSelected = selectedCase?.id === c.id;

              return (
                <div
                  key={c.id}
                  onClick={() => handleSelectCase(c)}
                  className={`dashboard-case-item ${isSelected ? 'selected' : ''}`}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                    <span style={{ fontWeight: '700', fontSize: '15px', color: '#1e293b' }}>
                      #{c.id.toString().padStart(4, '0')}
                    </span>
                    <span className={`badge ${isUrgent ? 'badge-urgent' : c.status === 'Approved' ? 'badge-approved' : 'badge-new'}`}>
                      {c.status}
                    </span>
                  </div>

                  <div style={{ fontSize: '14px', fontWeight: '600', color: isUrgent ? '#be123c' : '#334155', marginBottom: '4px' }}>
                    {c.category}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#64748b' }}>
                    <span>{c.applicant_name}</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> {new Date(c.received_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* RIGHT COLUMN: CASE DETAILS, CHAT HISTORY & REVIEW */}
      <div>
        {selectedCase ? (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '14px', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: '700' }}>
                  মামলা সারসংক্ষেপ · #{selectedCase.id.toString().padStart(4, '0')}
                </h2>
                <div style={{ fontSize: '13px', color: '#64748b' }}>
                  {selectedCase.category} · গ্রহণ: {new Date(selectedCase.received_at).toLocaleString()}
                </div>
              </div>

              {selectedCase.status === 'URGENT' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#ffe4e6', color: '#be123c', padding: '6px 12px', borderRadius: '6px', fontWeight: '700', fontSize: '13px' }}>
                  <AlertCircle size={18} />
                  জরুরি নিরাপত্তা ঝুঁকি
                </div>
              )}
            </div>

            {/* STRUCTURED SUMMARY TABLE */}
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '10px', color: '#334155' }}>
                কাঠামোগত তথ্য (Structured Facts):
              </h3>

              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <tbody>
                  <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '8px', color: '#64748b', width: '35%' }}>আবেদনকারী</td>
                    <td style={{ padding: '8px', fontWeight: '600' }}>{selectedCase.applicant_name}</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '8px', color: '#64748b' }}>বিবাদী</td>
                    <td style={{ padding: '8px', fontWeight: '600' }}>{selectedCase.respondent}</td>
                  </tr>
                  {selectedCase.marriage_date && (
                    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px', color: '#64748b' }}>বিবাহের সময়</td>
                      <td style={{ padding: '8px' }}>
                        {selectedCase.marriage_date}
                        {selectedCase.marriage_date_inferred && <span className="inferred-tag">inferred</span>}
                      </td>
                    </tr>
                  )}
                  {selectedCase.dower_amount && (
                    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px', color: '#64748b' }}>দেনমোহর</td>
                      <td style={{ padding: '8px', fontWeight: '600', color: '#0369a1' }}>{selectedCase.dower_amount}</td>
                    </tr>
                  )}
                  {selectedCase.dowry_paid && (
                    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px', color: '#64748b' }}>যৌতুক দাবি / প্রদত্ত</td>
                      <td style={{ padding: '8px' }}>{selectedCase.dowry_paid}</td>
                    </tr>
                  )}
                  {selectedCase.unpaid_wages_claim && (
                    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px', color: '#64748b' }}>বকেয়া মজুরি দাবি</td>
                      <td style={{ padding: '8px', fontWeight: '600', color: '#0369a1' }}>{selectedCase.unpaid_wages_claim}</td>
                    </tr>
                  )}
                  {selectedCase.current_status && (
                    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px', color: '#64748b' }}>বর্তমান পরিস্থিতি</td>
                      <td style={{ padding: '8px' }}>{selectedCase.current_status}</td>
                    </tr>
                  )}
                  {selectedCase.evidence && (
                    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '8px', color: '#64748b' }}>প্রমাণাদি / সাক্ষী</td>
                      <td style={{ padding: '8px' }}>{selectedCase.evidence}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* CHAT HISTORY SECTION */}
            <div style={{ marginBottom: '24px' }}>
              <div 
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', marginBottom: '10px' }}
                onClick={() => setShowFullChat(!showFullChat)}
              >
                <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#334155', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MessageSquare size={16} color="#0284c7" />
                  কথোপকথনের সম্পূর্ণ ইতিহাস (Chat History):
                </h3>
                <span style={{ fontSize: '12px', color: '#0284c7', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {showFullChat ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  {showFullChat ? 'সংক্ষেপ করুন' : 'বিস্তারিত দেখুন'}
                </span>
              </div>

              {showFullChat && (
                <div style={{ backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '280px', overflowY: 'auto' }}>
                  {selectedCase.chat_history && selectedCase.chat_history.length > 0 ? (
                    selectedCase.chat_history.map((msg, idx) => (
                      <div 
                        key={idx} 
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#64748b', marginBottom: '3px' }}>
                          {msg.role === 'user' ? (
                            <><span>ক্লায়েন্ট</span> <User size={12} /></>
                          ) : (
                            <><Bot size={12} /> <span>অধিকার এআই</span></>
                          )}
                        </div>
                        <div 
                          style={{
                            backgroundColor: msg.role === 'user' ? '#e0f2fe' : '#ffffff',
                            color: msg.role === 'user' ? '#0369a1' : '#334155',
                            border: msg.role === 'user' ? '1px solid #bae6fd' : '1px solid #e2e8f0',
                            padding: '10px 14px',
                            borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                            fontSize: '13px',
                            maxWidth: '88%',
                            lineHeight: '1.5',
                            whiteSpace: 'pre-wrap'
                          }}
                        >
                          {msg.content}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ fontSize: '13px', color: '#64748b', fontStyle: 'italic' }}>
                      "{selectedCase.original_transcript}"
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* DRAFT FIRST COMPLAINT */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#334155' }}>
                  আবেদনের খসড়া (Draft First Complaint)
                </h3>
                <button
                  className="btn btn-outline"
                  style={{ fontSize: '12px', padding: '4px 8px' }}
                  onClick={() => {
                    setIsEditingDraft(!isEditingDraft);
                    setEditedDraft(selectedCase.draft_complaint || '');
                  }}
                >
                  <Edit3 size={14} /> {isEditingDraft ? 'বাতিল' : 'সম্পাদনা করুন'}
                </button>
              </div>

              {isEditingDraft ? (
                <div>
                  <textarea
                    rows={8}
                    value={editedDraft}
                    onChange={(e) => setEditedDraft(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      border: '1px solid #38bdf8',
                      fontFamily: 'inherit',
                      fontSize: '13px',
                      marginBottom: '10px'
                    }}
                  />
                  <button
                    className="btn btn-primary"
                    style={{ fontSize: '13px', padding: '6px 14px' }}
                    disabled={isUpdating}
                    onClick={handleSaveDraft}
                  >
                    হালনাগাদ ও অনুমোদন করুন
                  </button>
                </div>
              ) : (
                <div style={{ backgroundColor: '#fdf4ff', padding: '14px', borderRadius: '8px', border: '1px solid #f5d0fe', fontSize: '13px', whiteSpace: 'pre-line', color: '#334155', maxHeight: '200px', overflowY: 'auto' }}>
                  {selectedCase.draft_complaint}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="card" style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
            বিস্তারিত দেখতে বাম পাশের তালিকা থেকে একটি মামলা সিলেক্ট করুন।
          </div>
        )}
      </div>
    </div>
  );
};
