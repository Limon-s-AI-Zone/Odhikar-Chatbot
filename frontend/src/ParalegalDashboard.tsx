import React, { useState, useRef } from 'react';
import axios from 'axios';
import { 
  AlertCircle, Clock, Check, Edit3, MessageSquare, 
  User, Bot, ShieldCheck, ChevronDown, ChevronUp,
  Volume2, VolumeX, Download, Printer, Loader2, FileText, Copy
} from 'lucide-react';
import { downloadDraftPdf, printDraftPdf } from './utils/draftPdfGenerator';

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
  address?: string;
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

const getCategoryLabel = (cat?: string | null): string => {
  if (!cat) return 'পারিবারিক — দেনমোহর ও ভরণপোষণ';
  const map: Record<string, string> = {
    'family_dower_maintenance': 'পারিবারিক — দেনমোহর ও ভরণপোষণ',
    'dowry': 'যৌতুক সংক্রান্ত বিরোধ ও নির্যাতন',
    'unpaid_wages': 'শ্রম ও কর্মসংস্থান — বকেয়া মজুরি আদায়',
    'land_dispute': 'ভূমি ও সম্পত্তি সংক্রান্ত বিরোধ',
    'out_of_scope': 'অন্যান্য / সাধারণ আইনি বিষয়'
  };
  return map[cat] || cat;
};

export const ParalegalDashboard: React.FC<DashboardProps> = ({ cases, onRefresh }) => {
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(cases[0] || null);
  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraft, setEditedDraft] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [copiedDraft, setCopiedDraft] = useState(false);
  const [showFullChat, setShowFullChat] = useState(true);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [currentPlayingText, setCurrentPlayingText] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const stopVoice = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(false);
    setCurrentPlayingText(null);
  };

  const playVoice = (text: string) => {
    if (!text || !text.trim()) return;

    if (isPlayingAudio && currentPlayingText === text) {
      stopVoice();
      return;
    }

    stopVoice();
    setIsPlayingAudio(true);
    setCurrentPlayingText(text);

    try {
      const audioUrl = `/api/tts?text=${encodeURIComponent(text.trim())}`;
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlayingAudio(false);
        setCurrentPlayingText(null);
        audioRef.current = null;
      };

      audio.onerror = () => {
        playBrowserSpeechFallback(text);
      };

      audio.play().catch(() => {
        playBrowserSpeechFallback(text);
      });
    } catch {
      playBrowserSpeechFallback(text);
    }
  };

  const playBrowserSpeechFallback = (text: string) => {
    if (!('speechSynthesis' in window)) {
      setIsPlayingAudio(false);
      setCurrentPlayingText(null);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'bn-BD';
    const voices = window.speechSynthesis.getVoices();
    const bnVoice = voices.find((v) => v.lang.startsWith('bn'));
    if (bnVoice) utterance.voice = bnVoice;
    utterance.rate = 0.92;
    utterance.onend = () => {
      setIsPlayingAudio(false);
      setCurrentPlayingText(null);
    };
    utterance.onerror = () => {
      setIsPlayingAudio(false);
      setCurrentPlayingText(null);
    };
    window.speechSynthesis.speak(utterance);
  };

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

  const handleCopyDraft = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedDraft(true);
    setTimeout(() => setCopiedDraft(false), 2000);
  };

  const handleDownloadDraftPdf = async () => {
    if (!selectedCase) return;
    const textToExport = isEditingDraft ? editedDraft : (selectedCase.draft_complaint || '');
    if (!textToExport.trim()) {
      alert('কোনো খসড়া পাওয়া যায়নি।');
      return;
    }
    try {
      setIsDownloadingPdf(true);
      await downloadDraftPdf({
        draftText: textToExport,
        caseId: selectedCase.id,
        category: selectedCase.category,
        categoryBangla: getCategoryLabel(selectedCase.category),
        applicantName: selectedCase.applicant_name,
        respondent: selectedCase.respondent,
        address: selectedCase.address || '[ঠিকানা — অপ্রতিষ্ঠিত]',
        clinicName: selectedCase.referral_clinic,
        appointmentSlot: selectedCase.referral_slot,
        status: selectedCase.status
      });
    } catch (err: any) {
      console.error('PDF generation error:', err);
      alert('পিডিএফ তৈরিতে সমস্যা হয়েছে: ' + (err?.message || 'অনুগ্রহ করে পুনরায় চেষ্টা করুন'));
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handlePrintDraft = () => {
    if (!selectedCase) return;
    const textToExport = isEditingDraft ? editedDraft : (selectedCase.draft_complaint || '');
    if (!textToExport.trim()) {
      alert('কোনো খসড়া পাওয়া যায়নি।');
      return;
    }
    printDraftPdf({
      draftText: textToExport,
      caseId: selectedCase.id,
      category: selectedCase.category,
      categoryBangla: getCategoryLabel(selectedCase.category),
      applicantName: selectedCase.applicant_name,
      respondent: selectedCase.respondent,
      address: selectedCase.address || '[ঠিকানা — অপ্রতিষ্ঠিত]',
      clinicName: selectedCase.referral_clinic,
      appointmentSlot: selectedCase.referral_slot,
      status: selectedCase.status
    });
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
                  style={{
                    backgroundColor: isSelected ? '#f0f9ff' : 'white',
                    border: isSelected ? '2px solid #0284c7' : isUrgent ? '1px solid #fca5a5' : '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '14px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.04)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                    <span style={{ fontWeight: '700', fontSize: '15px', color: '#1e293b' }}>
                      #{c.id.toString().padStart(4, '0')}
                    </span>
                    <span className={`badge ${isUrgent ? 'badge-urgent' : c.status === 'Approved' ? 'badge-booked' : 'badge-new'}`}>
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
                            whiteSpace: 'pre-wrap',
                            display: 'flex',
                            gap: '8px',
                            alignItems: 'flex-start'
                          }}
                        >
                          <div style={{ flex: 1 }}>{msg.content}</div>
                          <button
                            onClick={() => playVoice(msg.content)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              cursor: 'pointer',
                              padding: '2px',
                              color: isPlayingAudio && currentPlayingText === msg.content ? '#e11d48' : '#0284c7',
                              display: 'flex',
                              alignItems: 'center',
                              flexShrink: 0
                            }}
                            title="ভয়েস শুনুন"
                          >
                            {isPlayingAudio && currentPlayingText === msg.content ? <VolumeX size={14} /> : <Volume2 size={14} />}
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ fontSize: '13px', color: '#64748b', fontStyle: 'italic', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>"{selectedCase.original_transcript}"</span>
                      {selectedCase.original_transcript && (
                        <button
                          className="btn btn-outline"
                          style={{ fontSize: '12px', padding: '3px 8px', display: 'flex', alignItems: 'center', gap: '4px' }}
                          onClick={() => playVoice(selectedCase.original_transcript || '')}
                        >
                          {isPlayingAudio && currentPlayingText === selectedCase.original_transcript ? <VolumeX size={13} /> : <Volume2 size={13} />}
                          <span>{isPlayingAudio && currentPlayingText === selectedCase.original_transcript ? 'থামান' : 'শুনুন'}</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* DRAFT FIRST COMPLAINT */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#334155', display: 'flex', alignItems: 'center', gap: '6px', margin: 0 }}>
                  <FileText size={16} color="#d92d20" />
                  <span>আবেদনের খসড়া (Draft First Complaint)</span>
                </h3>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button
                    onClick={handleDownloadDraftPdf}
                    disabled={isDownloadingPdf}
                    style={{
                      backgroundColor: '#d92d20',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '5px 12px',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: isDownloadingPdf ? 'wait' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      boxShadow: '0 1px 3px rgba(217, 45, 32, 0.25)'
                    }}
                    title="অনুমোদিত খসড়াটি অফিশিয়াল PDF হিসেবে ডাউনলোড করুন"
                  >
                    {isDownloadingPdf ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <Download size={13} />}
                    <span>{isDownloadingPdf ? 'পিডিএফ হচ্ছে...' : 'PDF ডাউনলোড'}</span>
                  </button>

                  <button
                    onClick={handlePrintDraft}
                    style={{
                      backgroundColor: '#f8fafc',
                      border: '1px solid #cbd5e1',
                      borderRadius: '6px',
                      padding: '5px 10px',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: '#334155'
                    }}
                    title="প্রিন্ট প্রিভিউ ও প্রিন্ট"
                  >
                    <Printer size={13} />
                    <span>প্রিন্ট</span>
                  </button>

                  <button
                    onClick={() => handleCopyDraft(isEditingDraft ? editedDraft : (selectedCase.draft_complaint || ''))}
                    style={{
                      background: 'none',
                      border: '1px solid #cbd5e1',
                      borderRadius: '6px',
                      padding: '5px 9px',
                      fontSize: '12px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: copiedDraft ? '#16a34a' : '#475569'
                    }}
                    title="খসড়ার টেক্সট কপি করুন"
                  >
                    {copiedDraft ? <Check size={13} /> : <Copy size={13} />}
                    <span>{copiedDraft ? 'কপি হয়েছে' : 'কপি'}</span>
                  </button>

                  <button
                    className="btn btn-outline"
                    style={{ fontSize: '12px', padding: '5px 10px' }}
                    onClick={() => {
                      setIsEditingDraft(!isEditingDraft);
                      setEditedDraft(selectedCase.draft_complaint || '');
                    }}
                  >
                    <Edit3 size={13} /> {isEditingDraft ? 'বাতিল' : 'সম্পাদনা করুন'}
                  </button>
                </div>
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
