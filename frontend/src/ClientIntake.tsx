import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Mic, MicOff, Send, AlertTriangle, PhoneCall, 
  CheckCircle2, RefreshCw, ArrowRightCircle,
  MessageSquare, User, Sparkles, RotateCcw,
  MapPin, Calendar, FileText, Copy, Check, X, ShieldAlert
} from 'lucide-react';

interface IntakeProps {
  onCaseSubmitted: () => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  isStreamActive?: boolean;
}

export const ClientIntake: React.FC<IntakeProps> = ({ onCaseSubmitted }) => {
  // Conversational state
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'আসসালামু আলাইকুম। আমি অধিকার (Odhikar) — আপনার এআই আইনি সহকারী। পারিবারিক দেনমোহর, যৌতুক, বকেয়া মজুরি বা জমিজমা সংক্রান্ত যেকোনো আইনি ঘটনা আপনি সহজ বাংলায় বলতে বা লিখে জানাতে পারেন।\n\nএটি একটি স্বয়ংক্রিয় আইন সহায়তা ব্যবস্থা এবং আপনার তথ্য সুরক্ষিত থাকবে। আপনার কী ধরনের আইনি সহায়তা প্রয়োজন?'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  
  // Voice Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const recordIntervalRef = useRef<any>(null);

  // Completed Session / Card state
  const [sessionState, setSessionState] = useState<any>(null);
  const [safetyFlag, setSafetyFlag] = useState(false);
  const [safetyMessage, setSafetyMessage] = useState<string | null>(null);
  const [requiresContinuation, setRequiresContinuation] = useState(false);
  const [continuationPrompt, setContinuationPrompt] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [rightsExplanation, setRightsExplanation] = useState<string | null>(null);
  const [draftComplaint, setDraftComplaint] = useState<string | null>(null);
  const [referralInfo, setReferralInfo] = useState<{ clinic: string; slot: string } | null>(null);
  const [caseId, setCaseId] = useState<number | null>(null);

  // Draft Complaint Modal
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [copiedDraft, setCopiedDraft] = useState(false);

  const messageStreamRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    if (messageStreamRef.current) {
      messageStreamRef.current.scrollTo({
        top: messageStreamRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  const adjustTextareaHeight = () => {
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${Math.min(Math.max(textareaRef.current.scrollHeight, 44), 130)}px`;
      }
    }, 20);
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, streamStatus, isComplete, safetyFlag, requiresContinuation]);

  // Voice recording simulation
  const handleToggleRecording = () => {
    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      if (recordIntervalRef.current) {
        clearInterval(recordIntervalRef.current);
      }
      if (!inputText) {
        const sample = "চার বছর আগে আমার বিয়ে হয়েছে। বিয়ের পর থেকে ওরা আমার বাবার কাছে টাকা চাইতে থাকে। বাবা জমি বিক্রি করে কিছু টাকা দিয়েছেন, তারপরও ওদের চাওয়া শেষ হয় না। কাবিনের টাকা আজও পাইনি। এখন বলছে বাড়ি ছেড়ে চলে যেতে। আমার একটা ছোট মেয়ে আছে, আমি কোথায় যাব?";
        setInputText(sample);
        adjustTextareaHeight();
      }
    } else {
      // Start recording
      setIsRecording(true);
      setRecordSeconds(0);
      recordIntervalRef.current = setInterval(() => {
        setRecordSeconds((prev) => {
          if (prev >= 30) {
            handleToggleRecording();
            return 30;
          }
          return prev + 1;
        });
      }, 1000);
    }
  };

  // Reset conversation to fresh state
  const handleResetChat = () => {
    setChatHistory([
      {
        role: 'assistant',
        content: 'আসসালামু আলাইকুম। আমি অধিকার (Odhikar) — আপনার এআই আইনি সহকারী। নতুন যেকোনো আইনি ঘটনার বিবরণ আপনি সহজ বাংলায় মুখে বলতে বা লিখে জানাতে পারেন।'
      }
    ]);
    setInputText('');
    setSessionState(null);
    setSafetyFlag(false);
    setSafetyMessage(null);
    setRequiresContinuation(false);
    setContinuationPrompt(null);
    setIsComplete(false);
    setRightsExplanation(null);
    setDraftComplaint(null);
    setReferralInfo(null);
    setCaseId(null);
    setStreamStatus(null);
    setIsStreaming(false);
    setIsLoading(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px';
    }
  };

  // Send message via native LangGraph SSE streaming
  const handleSendMessage = async (textToSend?: string, isContinuation: boolean = false) => {
    const message = textToSend !== undefined ? textToSend : inputText;
    if (!message.trim() && !isContinuation) return;

    setIsLoading(true);
    setIsStreaming(true);
    setStreamStatus('বিবরণ বিশ্লেষণ ও আইনি তথ্য যাচাই করা হচ্ছে...');
    setRequiresContinuation(false);

    // Optimistically append user message and streaming assistant placeholder
    if (message.trim()) {
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', content: message.trim() },
        { role: 'assistant', content: '', isStreamActive: true }
      ]);
    } else if (isContinuation) {
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', content: 'হ্যাঁ, পরবর্তী টোকেন ও বিস্তারিত বিশ্লেষণ সম্পন্ন করুন।' },
        { role: 'assistant', content: '', isStreamActive: true }
      ]);
    }
    setInputText('');

    try {
      const response = await fetch('/api/intake/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: message || "",
          existing_state: sessionState,
          is_continuation: isContinuation
        })
      });

      if (!response.ok || !response.body) {
        throw new Error('Streaming connection failed, falling back');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulatedAssistantText = '';
      let finalData: any = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const jsonStr = trimmed.replace('data: ', '').trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);
            if (event.type === 'status') {
              setStreamStatus(event.content);
            } else if (event.type === 'token') {
              accumulatedAssistantText += event.content;
              setStreamStatus(null);
              setChatHistory((prev) => {
                const copy = [...prev];
                if (copy.length > 0 && copy[copy.length - 1].role === 'assistant') {
                  copy[copy.length - 1] = {
                    role: 'assistant',
                    content: accumulatedAssistantText,
                    isStreamActive: true
                  };
                }
                return copy;
              });
            } else if (event.type === 'final') {
              finalData = event;
            }
          } catch (e) {
            console.error('SSE JSON parse error:', e);
          }
        }
      }

      // Finalize stream
      if (finalData) {
        setSessionState(finalData.session_state);
        
        // Remove stream active flag on last assistant bubble
        setChatHistory((prev) => {
          const copy = [...prev];
          if (copy.length > 0 && copy[copy.length - 1].role === 'assistant') {
            copy[copy.length - 1] = {
              ...copy[copy.length - 1],
              isStreamActive: false,
              content: copy[copy.length - 1].content || finalData.follow_up_question || ''
            };
          }
          return copy;
        });

        // 1. Safety Breakout
        if (finalData.safety_flag) {
          setSafetyFlag(true);
          setSafetyMessage(finalData.safety_message);
          onCaseSubmitted();
          return;
        }

        // 2. Token Budget Continuation
        if (finalData.requires_continuation) {
          setRequiresContinuation(true);
          setContinuationPrompt(finalData.continuation_prompt);
          return;
        }

        // 3. Intake Complete: Personal Rights Roadmap & Referral
        if (finalData.is_complete) {
          setIsComplete(true);
          setRightsExplanation(finalData.rights_explanation);
          setDraftComplaint(finalData.draft_complaint);
          setReferralInfo({
            clinic: finalData.referral_clinic || 'ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র, সদর শাখা',
            slot: finalData.referral_slot || 'বুধবার, সকাল ১০:০০ টা'
          });
          setCaseId(finalData.case_id);
          onCaseSubmitted();
        }
      }
    } catch (err) {
      console.warn('Streaming error, invoking REST fallback:', err);
      // Fallback
      try {
        const res = await axios.post('/api/intake/message', {
          transcript: message || "",
          existing_state: sessionState,
          is_continuation: isContinuation
        });
        const data = res.data;
        setSessionState(data.session_state);
        if (data.chat_history && data.chat_history.length > 0) {
          setChatHistory(data.chat_history);
        }
        if (data.safety_flag) {
          setSafetyFlag(true);
          setSafetyMessage(data.safety_message);
          onCaseSubmitted();
        } else if (data.requires_continuation) {
          setRequiresContinuation(true);
          setContinuationPrompt(data.continuation_prompt);
        } else if (data.is_complete) {
          setIsComplete(true);
          setRightsExplanation(data.rights_explanation);
          setDraftComplaint(data.draft_complaint);
          setReferralInfo({
            clinic: data.referral_clinic || 'ব্র্যাক মানবাধিকার ও আইনি সহায়তা কেন্দ্র, সদর শাখা',
            slot: data.referral_slot || 'বুধবার, সকাল ১০:০০ টা'
          });
          setCaseId(data.case_id);
          onCaseSubmitted();
        }
      } catch (fallbackErr) {
        console.error('Fallback endpoint failed:', fallbackErr);
        alert('বার্তা পাঠাতে সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।');
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamStatus(null);
    }
  };

  // Load demo scenarios for instant testing
  const handleLoadScenario = (type: 'dower' | 'wages' | 'violence' | 'long') => {
    let text = '';
    if (type === 'dower') {
      text = "আমার বিয়ে হয়েছে ছয় বছর হলো। দুই বছর ধরে আমার স্বামী আলাদা থাকে, কোনো খরচ দেয় না। আমি বাচ্চা নিয়ে বাবার বাড়িতে আছি। কাবিনে লেখা ছিল দুই লাখ টাকা, এক টাকাও পাইনি। ফোন করলে বলে টাকা নাই। আমি আর কতদিন বাবার ঘাড়ে বসে থাকব?";
    } else if (type === 'wages') {
      text = "ধান কাটার কাজ করছিলাম, দশ দিন। দিন হাজিরা সাড়ে পাঁচশ টাকা কথা ছিল। কাজ শেষে দিল তিন হাজার, বাকিটা পরে দিবে বলল। দুই মাস হয়ে গেছে। লিখিত কিছু নাই, গ্রামের লোক সবাই জানে।";
    } else if (type === 'violence') {
      text = "কাবিনের টাকা তো পাইনিই, উল্টো গত সপ্তাহে মারধর করে হাত ভেঙে দিয়েছে। ডাক্তারের কাছে যেতেও দেয়নি। আজকেও বলছে রাতে দেখে নিবে। আমি খুব ভয় পাচ্ছি।";
    } else if (type === 'long') {
      text = "চার বছর আগে আমার বিয়ে হয়েছে। বিয়ের পর থেকে ওরা আমার বাবার কাছে বারবার যৌতুকের জন্য টাকা চাইতে থাকে। বাবা জমি বিক্রি করে কিছু টাকা দিয়েছেন, প্রায় আশি হাজার টাকা। তারপরও ওদের চাওয়া শেষ হয় না। কাবিনের টাকা আজও এক পয়সাও পাইনি। এখন ওরা আমাকে এবং আমার ছোট মেয়েকে বাড়ি ছেড়ে চলে যেতে বাধ্য করতেছে। শাশুড়ি ও ভাশুররা হুমকি দিচ্ছে। কাবিননামার কাগজ বাবার কাছে রাখা আছে। আমি এখন কোথায় যাব, কী করব কিছুই বুঝতে পারছি না।";
    }
    setInputText(text);
    adjustTextareaHeight();
  };

  const copyToClipboard = () => {
    if (draftComplaint) {
      navigator.clipboard.writeText(draftComplaint);
      setCopiedDraft(true);
      setTimeout(() => setCopiedDraft(false), 2500);
    }
  };

  return (
    <div className="chat-shell">
      {/* CHAT HEADER */}
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="msg-avatar bot">অ</div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: '700', fontSize: '16px', color: '#0f172a' }}>
                অধিকার (Odhikar AI)
              </span>
              <span className="status-pill">
                <span className="status-dot"></span> সক্রিয় সহায়তা
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              প্যারালিগ্যাল সহায়তা ও আইনি পরামর্শ · ব্র্যাক
            </div>
          </div>
        </div>

        <button
          className="btn btn-outline"
          style={{ padding: '6px 12px', fontSize: '12.5px' }}
          onClick={handleResetChat}
          title="নতুন আবেদন শুরু করুন"
        >
          <RotateCcw size={14} /> নতুন সেশন
        </button>
      </div>

      {/* QUICK DEMO SCENARIOS BAR */}
      <div className="scenario-bar">
        <span className="scenario-label">
          <Sparkles size={14} color="#d97706" /> ডেমো পরিস্থিতি:
        </span>
        <button className="scenario-chip" onClick={() => handleLoadScenario('dower')}>
          দেনমোহর ও ভরণপোষণ
        </button>
        <button className="scenario-chip" onClick={() => handleLoadScenario('wages')}>
          বকেয়া মজুরি
        </button>
        <button className="scenario-chip urgent" onClick={() => handleLoadScenario('violence')}>
          জরুরি সহিংসতা (Break-out)
        </button>
        <button className="scenario-chip" onClick={() => handleLoadScenario('long')}>
          দীর্ঘ বিবরণ (টোকেন পরীক্ষা)
        </button>
      </div>

      {/* MESSAGE STREAM */}
      <div className="message-stream" ref={messageStreamRef}>
        {chatHistory.map((msg, idx) => (
          <div key={idx} className={`message-row ${msg.role}`}>
            <div className={`msg-avatar ${msg.role === 'user' ? 'user' : 'bot'}`}>
              {msg.role === 'user' ? <User size={18} /> : 'অ'}
            </div>

            <div className="bubble-content">
              {/* LIVE PROCESSING BADGE */}
              {isStreaming && idx === chatHistory.length - 1 && msg.role === 'assistant' && streamStatus && (
                <div className="live-status-pill">
                  <RefreshCw className="animate-spin" size={13} />
                  <span>{streamStatus}</span>
                </div>
              )}

              <div className={`msg-bubble ${msg.role}`}>
                <div style={{ whiteSpace: 'pre-line' }}>
                  {msg.content}
                  {isStreaming && idx === chatHistory.length - 1 && msg.role === 'assistant' && (
                    <span className="streaming-cursor"></span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* 1. SAFETY BREAKOUT IN-CHAT CARD */}
        {safetyFlag && (
          <div className="in-chat-card safety">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', color: '#be123c' }}>
              <AlertTriangle size={24} />
              <strong style={{ fontSize: '16px' }}>জরুরি নিরাপত্তা ও সহায়তা ব্রেক-আউট</strong>
            </div>
            <p style={{ fontSize: '14px', lineHeight: '1.6', marginBottom: '14px' }}>
              {safetyMessage || "শারীরিক নির্যাতনের ঝুঁকি চিহ্নিত হওয়ায় কথোপকথন বিরতি দেওয়া হয়েছে। আপনার ব্যক্তিগত নিরাপত্তা সবার আগে।"}
            </p>
            <div style={{ background: '#ffffff', border: '1px solid #fecdd3', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', color: '#9f1239', fontSize: '15px' }}>
                <PhoneCall size={18} /> সরকারি ও জাতীয় আইন সহায়তা হেল্পলাইন: ১৬৪৩০
              </div>
              <div style={{ fontSize: '12.5px', color: '#64748b', marginTop: '4px' }}>
                নারী ও শিশু নির্যাতন প্রতিরোধ হেল্পলাইন: ১০৯ (টোল-ফ্রি)
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                className="btn btn-urgent" 
                style={{ flex: 1, padding: '10px' }}
                onClick={() => window.open('tel:16430')}
              >
                <PhoneCall size={16} /> এখনই কল করুন (১৬৪৩০)
              </button>
            </div>
          </div>
        )}

        {/* 2. TOKEN BUDGET CONTINUATION IN-CHAT CARD */}
        {requiresContinuation && (
          <div className="in-chat-card token-budget">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', color: '#0369a1' }}>
              <ArrowRightCircle size={22} />
              <strong style={{ fontSize: '16px' }}>টোকেন বাজেট নিরীক্ষা ও বিশদ বিশ্লেষণ সম্মতি</strong>
            </div>
            <p style={{ fontSize: '14px', lineHeight: '1.6', marginBottom: '14px' }}>
              {continuationPrompt || "আপনার বক্তব্যটি দীর্ঘ। টোকেন বাজেট সীমার মধ্যে রেখে পূর্ণাঙ্গ আইনি বিশ্লেষণ সম্পন্ন করতে আপনার সম্মতি প্রয়োজন।"}
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                className="btn btn-outline" 
                style={{ flex: 1 }}
                onClick={() => {
                  setRequiresContinuation(false);
                  setInputText('');
                }}
              >
                সংক্ষেপ করুন
              </button>
              <button 
                className="btn btn-accent" 
                style={{ flex: 1.5 }}
                disabled={isLoading}
                onClick={() => handleSendMessage("", true)}
              >
                {isLoading ? <RefreshCw className="animate-spin" size={16} /> : <CheckCircle2 size={16} />}
                পরবর্তী বিশ্লেষণ সম্পন্ন করুন
              </button>
            </div>
          </div>
        )}

        {/* 3. RIGHTS ROADMAP & CLINIC REFERRAL IN-CHAT CARD */}
        {isComplete && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '6px' }}>
            {/* Rights Card */}
            {rightsExplanation && (
              <div className="in-chat-card rights">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0284c7', marginBottom: '10px' }}>
                  <CheckCircle2 size={22} />
                  <strong style={{ fontSize: '17px' }}>আপনার আইনি অধিকার ও প্রতিকারের পথ</strong>
                </div>
                <div style={{ fontSize: '14px', lineHeight: '1.7', color: '#334155', whiteSpace: 'pre-line' }}>
                  {rightsExplanation}
                </div>
              </div>
            )}

            {/* Referral Clinic Card */}
            <div className="in-chat-card referral">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534' }}>
                  <MapPin size={22} />
                  <strong style={{ fontSize: '16px' }}>নিকটতম ব্র্যাক লিগ্যাল এইড ক্লিনিক</strong>
                </div>
                {caseId && (
                  <span className="badge badge-approved" style={{ fontSize: '12px' }}>
                    মামলা আইডি: #{caseId.toString().padStart(4, '0')}
                  </span>
                )}
              </div>

              <div style={{ fontSize: '15px', fontWeight: '700', color: '#14532d', marginBottom: '4px' }}>
                {referralInfo?.clinic}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13.5px', color: '#15803d', marginBottom: '12px' }}>
                <Calendar size={15} />
                নির্ধারিত পরামর্শ সময়: <strong>{referralInfo?.slot}</strong>
              </div>

              <p style={{ fontSize: '12.5px', color: '#475569', marginBottom: '14px' }}>
                আপনার তথ্যের ভিত্তিতে আইনি সারসংক্ষেপ ও খসড়া প্রস্তুত করে প্যারালিগ্যাল ড্যাশবোর্ডে পাঠানো হয়েছে।
              </p>

              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button 
                  className="btn btn-primary" 
                  style={{ flex: 1 }}
                  onClick={() => setShowDraftModal(true)}
                >
                  <FileText size={16} /> আইনি অভিযোগের খসড়া দেখুন
                </button>
                <button 
                  className="btn btn-outline" 
                  onClick={handleResetChat}
                >
                  নতুন আবেদন
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* DOCKED INPUT FOOTER */}
      <div className="chat-footer">
        {isRecording && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: '#ffe4e6', borderRadius: '8px', fontSize: '13px', color: '#be123c', fontWeight: '600' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#e11d48', animation: 'pulse-dot 1s infinite' }}></span>
            <span>ভয়েস রেকর্ড হচ্ছে... (০০:{recordSeconds.toString().padStart(2, '0')}) · কথা শেষ হলে মাইকে আবার চাপ দিন</span>
          </div>
        )}

        <div className="input-row">
          <button
            className={`record-btn ${isRecording ? 'active' : ''}`}
            onClick={handleToggleRecording}
            title={isRecording ? 'রেকর্ড সম্পন্ন করুন' : 'ভয়েস রেকর্ড করুন'}
          >
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          <textarea
            ref={textareaRef}
            className="chat-textarea"
            value={inputText}
            rows={1}
            onChange={(e) => {
              setInputText(e.target.value);
              adjustTextareaHeight();
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
                if (textareaRef.current) {
                  textareaRef.current.style.height = '44px';
                }
              }
            }}
            placeholder={isRecording ? "ভয়েস রেকর্ড হচ্ছে..." : "আপনার আইনি ঘটনা বলুন বা বিস্তারিত বাংলায় লিখুন... (Enter এ সেন্ড, Shift+Enter এ নতুন লাইন)"}
            disabled={isLoading || isRecording}
          />

          <button
            className="send-btn"
            disabled={isLoading || (!inputText.trim() && !isRecording)}
            onClick={() => handleSendMessage()}
            title="বার্তা পাঠান"
          >
            {isLoading ? <RefreshCw className="animate-spin" size={18} /> : <Send size={18} />}
          </button>
        </div>
      </div>

      {/* COMPLAINT DRAFT MODAL */}
      {showDraftModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(3px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: '16px',
            maxWidth: '680px',
            width: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            border: '1px solid #e2e8f0',
            overflow: 'hidden'
          }}>
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid #e2e8f0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a' }}>
                  প্রাথমিক আইনি অভিযোগের খসড়া
                </h3>
                <div style={{ fontSize: '12.5px', color: '#64748b' }}>
                  ব্র্যাক লিগ্যাল এইড প্যারালিগ্যাল পর্যালোচনার জন্য প্রস্তুতকৃত খসড়া
                </div>
              </div>
              <button
                onClick={() => setShowDraftModal(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={22} />
              </button>
            </div>

            <div style={{
              padding: '20px 24px',
              overflowY: 'auto',
              flex: 1,
              backgroundColor: '#f8fafc',
              fontSize: '13.5px',
              lineHeight: '1.75',
              whiteSpace: 'pre-line',
              color: '#334155',
              fontFamily: 'inherit'
            }}>
              {draftComplaint || "খসড়া এখনো প্রস্তুত হয়নি।"}
            </div>

            <div style={{
              padding: '16px 24px',
              borderTop: '1px solid #e2e8f0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#ffffff'
            }}>
              <button
                className="btn btn-outline"
                onClick={copyToClipboard}
              >
                {copiedDraft ? <Check size={16} color="#059669" /> : <Copy size={16} />}
                {copiedDraft ? 'কপি সম্পন্ন হয়েছে' : 'কপি করুন'}
              </button>

              <button
                className="btn btn-primary"
                onClick={() => setShowDraftModal(false)}
              >
                বন্ধ করুন
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
