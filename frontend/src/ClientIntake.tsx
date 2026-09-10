import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Send, AlertTriangle, PhoneCall, 
  CheckCircle2, ChevronRight, RefreshCw, ArrowRightCircle,
  MessageSquare, User, Bot, WifiOff, KeyRound, AlertOctagon, XCircle,
  Volume2, VolumeX, FileText, Mic, Square, Radio
} from 'lucide-react';

interface IntakeProps {
  onCaseSubmitted: () => void;
}

interface ChatMessage {
  role: string;
  content: string;
}

export interface LlmErrorInfo {
  title: string;
  message: string;
  code?: string | number;
  details?: string;
  errorType?: string;
  troubleshooting?: string[];
}

export const ClientIntake: React.FC<IntakeProps> = ({ onCaseSubmitted }) => {
  const [step, setStep] = useState<'welcome' | 'recording' | 'follow_up' | 'continuation' | 'rights' | 'referral' | 'safety'>('welcome');
  const [textNarrative, setTextNarrative] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  
  // LLM Error and Retry tracking
  const [llmError, setLlmError] = useState<LlmErrorInfo | null>(null);
  const [lastAttemptedMessage, setLastAttemptedMessage] = useState<string>('');

  // Session & Chat History State
  const [sessionState, setSessionState] = useState<any>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [followUpQuestion, setFollowUpQuestion] = useState<string | null>(null);
  const [continuationPrompt, setContinuationPrompt] = useState<string | null>(null);
  const [safetyMessage, setSafetyMessage] = useState<string | null>(null);
  const [rightsExplanation, setRightsExplanation] = useState<string | null>(null);
  const [draftComplaint, setDraftComplaint] = useState<string | null>(null);
  const [referralInfo, setReferralInfo] = useState<{ clinic: string; slot: string } | null>(null);
  const [caseId, setCaseId] = useState<number | null>(null);

  // Audio Playback / Voice Output (TTS) State
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
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
    setIsLoadingAudio(false);
    setCurrentPlayingText(null);
  };

  const playVoice = async (text: string) => {
    if (!text || !text.trim()) return;

    // Toggle stop if already playing or loading the same text
    if ((isPlayingAudio || isLoadingAudio) && currentPlayingText === text) {
      stopVoice();
      return;
    }

    stopVoice();
    setIsLoadingAudio(true);
    setCurrentPlayingText(text);

    try {
      // 1. Prepare stream via POST to avoid HTTP 431 URL length limits on long text
      const res = await axios.post('/api/tts/prepare', { text: text.trim() });
      const streamUrl = res.data.audio_url;

      const audio = new Audio(streamUrl);
      audioRef.current = audio;

      audio.onplay = () => {
        setIsLoadingAudio(false);
        setIsPlayingAudio(true);
      };

      audio.onended = () => {
        setIsPlayingAudio(false);
        setIsLoadingAudio(false);
        setCurrentPlayingText(null);
        audioRef.current = null;
      };

      audio.onerror = (e) => {
        console.warn('Audio streaming failed, trying fallback:', e);
        setIsLoadingAudio(false);
        playBrowserSpeechFallback(text);
      };

      await audio.play();
    } catch (err) {
      console.warn('TTS prepare failed, falling back to direct GET:', err);
      try {
        const audioUrl = `/api/tts?text=${encodeURIComponent(text.trim().slice(0, 500))}`;
        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        audio.onplay = () => {
          setIsLoadingAudio(false);
          setIsPlayingAudio(true);
        };

        audio.onended = () => {
          setIsPlayingAudio(false);
          setIsLoadingAudio(false);
          setCurrentPlayingText(null);
          audioRef.current = null;
        };

        audio.onerror = () => {
          setIsLoadingAudio(false);
          playBrowserSpeechFallback(text);
        };

        await audio.play();
      } catch {
        setIsLoadingAudio(false);
        playBrowserSpeechFallback(text);
      }
    }
  };

  const playBrowserSpeechFallback = (text: string) => {
    if (!('speechSynthesis' in window)) {
      setIsPlayingAudio(false);
      setIsLoadingAudio(false);
      setCurrentPlayingText(null);
      return;
    }
    const cleanText = text.replace(/[*#_`]/g, '').slice(0, 300);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'bn-BD';
    const voices = window.speechSynthesis.getVoices();
    const bnVoice = voices.find((v) => v.lang.startsWith('bn'));
    if (bnVoice) utterance.voice = bnVoice;
    utterance.rate = 0.92;
    utterance.onend = () => {
      setIsPlayingAudio(false);
      setIsLoadingAudio(false);
      setCurrentPlayingText(null);
    };
    utterance.onerror = () => {
      setIsPlayingAudio(false);
      setIsLoadingAudio(false);
      setCurrentPlayingText(null);
    };
    window.speechSynthesis.speak(utterance);
  };

  // 100% Pure Frontend Voice Typing (Browser-Native Web Speech API - Zero backend overhead)
  const [isListening, setIsListening] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [voiceStatus, setVoiceStatus] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const timerIntervalRef = useRef<any>(null);
  const shouldBeListeningRef = useRef<boolean>(false);
  const accumulatedTextRef = useRef<string>('');

  const stopVoiceTyping = () => {
    shouldBeListeningRef.current = false;
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
      recognitionRef.current = null;
    }
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    setIsListening(false);
  };

  const startVoiceTyping = async () => {
    stopVoice(); // Stop any TTS speech playback
    setVoiceStatus(null);

    const SpeechRecognitionClass =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      setVoiceStatus('আপনার ব্রাউজারে ভয়েস টাইপিং সমর্থিত নয়। অনুগ্রহ করে Google Chrome বা Edge ব্রাউজার ব্যবহার করুন।');
      return;
    }

    try {
      // Explicitly request mic access so browser prompts "Allow" cleanly
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Immediately release tracks so SpeechRecognition has full exclusive access to the microphone
      stream.getTracks().forEach((track) => track.stop());
    } catch (err: any) {
      console.warn('Microphone permission denied:', err);
      setVoiceStatus('মাইক্রোফোনের অনুমতি প্রয়োজন। ব্রাউজারে Microphone "Allow" করুন।');
      return;
    }

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.lang = 'bn-BD';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      // Preserve already typed text
      accumulatedTextRef.current = textNarrative.trim();

      recognition.onstart = () => {
        setIsListening(true);
        shouldBeListeningRef.current = true;
        setVoiceStatus('কথা বলুন, আপনার কথা সরাসরি বাংলায় লেখা হচ্ছে...');
        setRecordingSeconds(0);
        if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = setInterval(() => {
          setRecordingSeconds((prev) => prev + 1);
        }, 1000);
      };

      recognition.onresult = (event: any) => {
        let currentInterim = '';
        let currentFinal = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i];
          const transcript = item[0]?.transcript || '';
          if (item.isFinal) {
            currentFinal += transcript;
          } else {
            currentInterim += transcript;
          }
        }

        if (currentFinal) {
          accumulatedTextRef.current = accumulatedTextRef.current
            ? `${accumulatedTextRef.current} ${currentFinal.trim()}`
            : currentFinal.trim();
        }

        const fullDisplay = [accumulatedTextRef.current, currentInterim.trim()]
          .filter(Boolean)
          .join(' ')
          .trim();

        setTextNarrative(fullDisplay);
      };

      recognition.onerror = (event: any) => {
        console.warn('[SpeechRecognition Error]', event.error);
        if (event.error === 'no-speech') {
          // Harmless pause in speech, ignore so auto-restart continues
          return;
        }
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          shouldBeListeningRef.current = false;
          setIsListening(false);
          setVoiceStatus('মাইক্রোফোনের অনুমতি পাওয়া যায়নি। ব্রাউজার সেটিংসে গিয়ে পারমিশন দিন।');
          return;
        }
        if (event.error === 'aborted') {
          return;
        }
        setVoiceStatus(`ভয়েস টাইপিং সাময়িক ব্যাহত (${event.error})। আবার কথা বলুন।`);
      };

      recognition.onend = () => {
        // Auto-restart if user has not explicitly tapped "থামান"
        if (shouldBeListeningRef.current) {
          try {
            recognition.start();
          } catch (_) {}
        } else {
          setIsListening(false);
          if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
          }
          setVoiceStatus('ভয়েস টাইপিং সম্পন্ন। নিচের টেক্সটটি যাচাই করে জমা দিন।');
        }
      };

      recognitionRef.current = recognition;
      shouldBeListeningRef.current = true;
      recognition.start();
    } catch (err: any) {
      console.error('Speech recognition start failed:', err);
      setVoiceStatus('ভয়েস টাইপিং শুরু করা যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন।');
      setIsListening(false);
      shouldBeListeningRef.current = false;
    }
  };

  useEffect(() => {
    return () => {
      stopVoiceTyping();
      stopVoice();
    };
  }, []);

  const renderVoiceTypingButton = () => (
    <button
      type="button"
      onClick={isListening ? stopVoiceTyping : startVoiceTyping}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 14px',
        fontSize: '13px',
        fontWeight: '600',
        borderRadius: '20px',
        border: isListening ? '1px solid #ef4444' : '1px solid #bae6fd',
        cursor: 'pointer',
        backgroundColor: isListening ? '#fef2f2' : '#f0f9ff',
        color: isListening ? '#b91c1c' : '#0284c7',
        transition: 'all 0.15s ease'
      }}
      title={isListening ? 'রেকর্ডিং বন্ধ করুন' : 'মুখে বলে বাংলায় লিখুন'}
    >
      {isListening ? (
        <>
          <span className="mic-recording-pulse" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#dc2626', display: 'inline-block' }} />
          <Square size={13} fill="#dc2626" />
          <span>থামান ({String(Math.floor(recordingSeconds / 60)).padStart(2, '0')}:{String(recordingSeconds % 60).padStart(2, '0')})</span>
        </>
      ) : (
        <>
          <Mic size={14} />
          <span>মুখে বলুন (Voice Typing)</span>
        </>
      )}
    </button>
  );


  const handleSendMessage = async (textToSend?: string, isContinuation: boolean = false) => {
    stopVoiceTyping();
    const message = textToSend !== undefined ? textToSend : textNarrative;
    if (!message.trim() && !isContinuation) return;

    stopVoice();
    setVoiceStatus(null);
    setLlmError(null);
    setLastAttemptedMessage(message || "");
    setIsLoading(true);
    setIsStreaming(true);
    setStreamStatus('বিবরণ বিশ্লেষণ ও আইনি তথ্য যাচাই করা হচ্ছে...');

    // Optimistically push the user's message and an active assistant placeholder
    if (message.trim()) {
      setChatHistory((prev) => [
        ...prev,
        { role: 'user', content: message.trim() },
        { role: 'assistant', content: '' }
      ]);
    }
    setTextNarrative('');

    // Switch to conversational view immediately so the user sees live activity
    if (step === 'recording') {
      setStep('follow_up');
    }

    try {
      // Connect to SSE streaming endpoint
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
        throw new Error('Streaming connection failed, activating fallback');
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
            } else if (event.type === 'error') {
              const errDetails = event.llm_error_details || {};
              setLlmError({
                title: errDetails.title || 'এলএলএম ত্রুটি (LLM Error)',
                message: event.llm_error || errDetails.message_bn || 'এআই মডেলের সাথে যোগাযোগে ত্রুটি ঘটেছে।',
                code: errDetails.status_code || errDetails.error_type || 500,
                details: errDetails.message_en || errDetails.raw_error || '',
                errorType: errDetails.error_type
              });
              setStreamStatus(null);
            } else if (event.type === 'token') {
              accumulatedAssistantText += event.content;
              setStreamStatus(null);
              setChatHistory((prev) => {
                const copy = [...prev];
                if (copy.length > 0 && copy[copy.length - 1].role === 'assistant') {
                  copy[copy.length - 1] = { role: 'assistant', content: accumulatedAssistantText };
                }
                return copy;
              });
            } else if (event.type === 'final') {
              finalData = event;
            }
          } catch (e) {
            console.error('SSE token parse error:', e);
          }
        }
      }

      if (finalData) {
        if (finalData.llm_error) {
          const errDetails = finalData.llm_error_details || {};
          setLlmError({
            title: errDetails.title || 'এলএলএম ত্রুটি (LLM Error)',
            message: finalData.llm_error,
            code: errDetails.status_code || errDetails.error_type || 500,
            details: errDetails.message_en || errDetails.raw_error || '',
            errorType: errDetails.error_type
          });
          setChatHistory((prev) => prev.filter(m => m.content.trim() !== ''));
          return;
        }

        setSessionState(finalData.session_state);
        if (finalData.chat_history && finalData.chat_history.length > 0) {
          setChatHistory(finalData.chat_history);
        }

        // 1. Safety Breakout
        if (finalData.safety_flag) {
          setSafetyMessage(finalData.safety_message);
          setStep('safety');
          onCaseSubmitted();
          return;
        }

        // 2. Token Budget Continuation
        if (finalData.requires_continuation) {
          setContinuationPrompt(finalData.continuation_prompt);
          setStep('continuation');
          return;
        }

        // 3. Follow-up or Legal Rights Solution
        if (finalData.follow_up_question) {
          setFollowUpQuestion(finalData.follow_up_question);
          setStep('follow_up');
        } else if (finalData.is_complete) {
          setRightsExplanation(finalData.rights_explanation);
          setDraftComplaint(finalData.draft_complaint);
          setReferralInfo({
            clinic: finalData.referral_clinic || 'ব্র্যাক আইনি সহায়তা কেন্দ্র, সদর শাখা',
            slot: finalData.referral_slot || 'বুধবার, সকাল ১০:০০ টা'
          });
          setCaseId(finalData.case_id);
          setStep('rights');
          onCaseSubmitted();
        }
      }
    } catch (err) {
      console.warn('Streaming failed, fallback to standard endpoint:', err);
      // Seamless fallback to standard HTTP endpoint
      try {
        const fallbackRes = await axios.post('/api/intake/message', {
          transcript: message || "",
          existing_state: sessionState,
          is_continuation: isContinuation
        });

        const data = fallbackRes.data;
        if (data.llm_error) {
          const errDetails = data.llm_error_details || {};
          setLlmError({
            title: errDetails.title || 'এলএলএম ত্রুটি (LLM Error)',
            message: data.llm_error,
            code: errDetails.status_code || errDetails.error_type || 500,
            details: errDetails.message_en || errDetails.raw_error || '',
            errorType: errDetails.error_type
          });
          setChatHistory((prev) => prev.filter(m => m.content.trim() !== ''));
          return;
        }

        setSessionState(data.session_state);

        if (data.chat_history && data.chat_history.length > 0) {
          setChatHistory(data.chat_history);
        }

        if (data.safety_flag) {
          setSafetyMessage(data.safety_message);
          setStep('safety');
          onCaseSubmitted();
        } else if (data.requires_continuation) {
          setContinuationPrompt(data.continuation_prompt);
          setStep('continuation');
        } else if (data.follow_up_question) {
          setFollowUpQuestion(data.follow_up_question);
          setStep('follow_up');
        } else if (data.is_complete) {
          setRightsExplanation(data.rights_explanation);
          setDraftComplaint(data.draft_complaint);
          setReferralInfo({
            clinic: data.referral_clinic || 'ব্র্যাক আইনি সহায়তা কেন্দ্র, সদর শাখা',
            slot: data.referral_slot || 'বুধবার, সকাল ১০:০০ টা'
          });
          setCaseId(data.case_id);
          setStep('rights');
          onCaseSubmitted();
        }
      } catch (fallbackErr: any) {
        console.error('Fallback endpoint also failed:', fallbackErr);
        let errorTitle = 'সার্ভার সংযোগ ত্রুটি';
        let errorMsg = 'সার্ভারের সাথে যোগাযোগ করা যাচ্ছে না।';
        let errCode: string | number = 'CONNECTION_ERROR';
        let errDetails = '';
        let errType = 'connection_error';

        let troubleshootingList: string[] | undefined;

        if (fallbackErr.response) {
          const status = fallbackErr.response.status;
          errCode = status;
          const detail = fallbackErr.response.data?.detail;
          if (detail && typeof detail === 'object') {
            errorTitle = detail.title || errorTitle;
            errorMsg = detail.message_bn || detail.message || errorMsg;
            errType = detail.error_type || errType;
            troubleshootingList = detail.troubleshooting_bn;
            errDetails = detail.message_en || detail.error || '';
          } else if (typeof detail === 'string') {
            errorMsg = detail;
            errDetails = detail;
          } else if (status === 401) {
            errorTitle = 'এলএলএম অথেন্টিকেশন ত্রুটি (Error 401 Unauthorized)';
            errorMsg = 'এআই মডেলের API কী বা ক্রেডেনশিয়াল সঠিক নয়। backend/.env ফাইলে সেটিংস (Local / Vertex AI / OpenRouter) যাচাই করুন।';
            errDetails = 'Invalid, missing, or expired API token (HTTP 401 Unauthorized).';
            errType = 'authentication_error';
          } else if (status === 429) {
            errorTitle = 'টোকেন কোটা বা রেট লিমিট অতিক্রম (Error 429)';
            errorMsg = 'টোকেন কোটা শেষ অথবা রেট লিমিট অতিক্রম করেছে। অনুগ্রহ করে কিছুক্ষণ পর পুনরায় চেষ্টা করুন।';
            errDetails = 'Rate limit reached or token quota exhausted (HTTP 429 Rate Limit).';
            errType = 'rate_limit_error';
          } else if (status === 402) {
            errorTitle = 'টোকেন ব্যালেন্স ত্রুটি (Error 402 Payment Required)';
            errorMsg = 'আপনার একাউন্টে পর্যাপ্ত টোকেন ব্যালেন্স বা ক্রেডিট নেই। অনুগ্রহ করে টোকেন রিচার্জ করুন।';
            errDetails = 'Insufficient token credits or balance (HTTP 402).';
            errType = 'token_credit_error';
          }
        } else if (fallbackErr.request) {
          errorTitle = 'এলএলএম / সার্ভার সংযোগ বিচ্ছিন্ন (Not Connected)';
          errorMsg = 'এআই মডেল বা ব্যাকএন্ড সার্ভারের সাথে সংযোগ স্থাপন সম্ভব হয়নি। অনুগ্রহ করে ইন্টারনেট ও সার্ভার চালু আছে কি না দেখুন।';
          errDetails = fallbackErr.message || 'Network connection failed.';
          errType = 'connection_error';
        }

        setLlmError({
          title: errorTitle,
          message: errorMsg,
          code: errCode,
          details: errDetails,
          errorType: errType,
          troubleshooting: troubleshootingList
        });
        setChatHistory((prev) => prev.filter(m => m.content.trim() !== ''));
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamStatus(null);
    }
  };

  // Quick fill sample narratives for demo
  const handleLoadSample = (sampleType: 'dower' | 'wages' | 'violence' | 'long') => {
    if (sampleType === 'dower') {
      setTextNarrative("আমার বিয়ে হয়েছে ছয় বছর হলো। দুই বছর ধরে আমার স্বামী আলাদা থাকে, কোনো খরচ দেয় না। আমি বাচ্চা নিয়ে বাবার বাড়িতে আছি। কাবিনে লেখা ছিল দুই লাখ টাকা, এক টাকাও পাইনি। ফোন করলে বলে টাকা নাই। আমি আর কতদিন বাবার ঘাড়ে বসে থাকব?");
    } else if (sampleType === 'wages') {
      setTextNarrative("ধান কাটার কাজ করছিলাম, দশ দিন। দিন হাজিরা সাড়ে পাঁচশ টাকা কথা ছিল। কাজ শেষে দিল তিন হাজার, বাকিটা পরে দিবে বলল। দুই মাস হয়ে গেছে। লিখিত কিছু নাই, গ্রামের লোক সবাই জানে।");
    } else if (sampleType === 'violence') {
      setTextNarrative("কাবিনের টাকা তো পাইনিই, উল্টো গত সপ্তাহে হাত ভেঙে দিয়েছে। ডাক্তারের কাছে যেতেও দেয়নি। আজকেও বলছে রাতে দেখে নিবে। আমি খুব ভয় পাচ্ছি।");
    } else if (sampleType === 'long') {
      setTextNarrative("চার বছর আগে আমার বিয়ে হয়েছে। বিয়ের পর থেকে ওরা আমার বাবার কাছে বারবার যৌতুকের জন্য টাকা চাইতে থাকে। বাবা জমি বিক্রি করে কিছু টাকা দিয়েছেন, প্রায় আশি হাজার টাকা। তারপরও ওদের চাওয়া শেষ হয় না। কাবিনের টাকা আজও এক পয়সাও পাইনি। এখন ওরা আমাকে এবং আমার ছোট মেয়েকে বাড়ি ছেড়ে চলে যেতে বাধ্য করতেছে। শাশুড়ি ও ভাশুররা হুমকি দিচ্ছে। কাবিননামার কাগজ বাবার কাছে রাখা আছে। আমি এখন কোথায় যাব, কী করব কিছুই বুঝতে পারছি না।");
    }
  };

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto' }}>
      {/* GLOBAL LLM ERROR BANNER (401, Disconnection, Token / Rate Limits) */}
      {llmError && (
        <div 
          className="card" 
          style={{ 
            border: '2px solid #f43f5e', 
            backgroundColor: '#fff1f2', 
            marginBottom: '20px',
            boxShadow: '0 4px 12px rgba(244, 63, 94, 0.12)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
            <div style={{ 
              backgroundColor: '#ffe4e6', 
              color: '#e11d48', 
              borderRadius: '10px', 
              padding: '10px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              flexShrink: 0
            }}>
              {llmError.errorType === 'authentication_error' || llmError.code === 401 ? (
                <KeyRound size={26} />
              ) : llmError.errorType === 'connection_error' ? (
                <WifiOff size={26} />
              ) : (
                <AlertOctagon size={26} />
              )}
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap', gap: '6px' }}>
                <h3 style={{ fontSize: '17px', fontWeight: '700', color: '#9f1239', margin: 0 }}>
                  {llmError.title}
                </h3>
                {llmError.code && (
                  <span style={{ 
                    fontSize: '12px', 
                    fontWeight: '700', 
                    padding: '2px 8px', 
                    borderRadius: '6px', 
                    backgroundColor: '#fecdd3', 
                    color: '#881337',
                    border: '1px solid #fda4af'
                  }}>
                    {typeof llmError.code === 'number' ? `Error ${llmError.code}` : llmError.code}
                  </span>
                )}
              </div>

              <p style={{ fontSize: '14px', lineHeight: '1.6', color: '#881337', margin: '4px 0 10px' }}>
                {llmError.message}
              </p>

              {/* Troubleshooting helper tips */}
              <div style={{ backgroundColor: 'white', padding: '10px 14px', borderRadius: '8px', border: '1px solid #fecdd3', marginBottom: '12px' }}>
                <div style={{ fontSize: '12px', fontWeight: '700', color: '#be123c', marginBottom: '4px' }}>
                  সম্ভাব্য সমাধান (Troubleshooting):
                </div>
                <ul style={{ fontSize: '12px', color: '#475569', margin: 0, paddingLeft: '18px', lineHeight: '1.6' }}>
                  {llmError.troubleshooting && llmError.troubleshooting.length > 0 ? (
                    llmError.troubleshooting.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))
                  ) : llmError.code === 401 || llmError.errorType === 'authentication_error' ? (
                    <>
                      <li>প্রকল্পের <code>backend/.env</code> ফাইলে API কী বা ক্রেডেনশিয়াল (Vertex AI / OpenRouter) সঠিক আছে কি না তা যাচাই করুন।</li>
                      <li>কী বা সেটিংস পরিবর্তন করলে ব্যাকএন্ড সার্ভার রিস্টার্ট করুন।</li>
                    </>
                  ) : llmError.code === 429 || llmError.errorType === 'rate_limit_error' ? (
                    <>
                      <li>মডেলের বর্তমান রিকোয়েস্ট লিমিট বা কোটা শেষ হয়েছে — কিছুক্ষণ অপেক্ষা করে পুনরায় চেষ্টা করুন।</li>
                      <li>অথবা <code>backend/.env</code> ফাইলে ব্যাকআপ প্রোভাইডার কনফিগার করুন।</li>
                    </>
                  ) : llmError.code === 402 || llmError.errorType === 'token_credit_error' ? (
                    <>
                      <li>আপনার প্রোভাইডার একাউন্টে টোকেন ব্যালেন্স বা ক্রেডিট যোগ করুন।</li>
                    </>
                  ) : (
                    <>
                      <li>আপনার কম্পিউটার ও ব্যাকএন্ড সার্ভার (Port 8000) অথবা লোকাল এলএলএম সচল আছে কি না পরীক্ষা করুন।</li>
                      <li>ইন্টারনেট সংযোগ চালু আছে কি না দেখুন।</li>
                    </>
                  )}
                </ul>
                {llmError.details && (
                  <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px dashed #fecdd3', fontSize: '11px', color: '#64748b', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                    <strong>Technical Details:</strong> {llmError.details}
                  </div>
                )}
              </div>

              {/* Action buttons */}
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button
                  className="btn btn-primary"
                  style={{ fontSize: '13px', padding: '7px 16px', backgroundColor: '#e11d48' }}
                  disabled={isLoading}
                  onClick={() => handleSendMessage(lastAttemptedMessage || undefined)}
                >
                  <RefreshCw className={isLoading ? 'animate-spin' : ''} size={14} /> পুনরায় চেষ্টা করুন (Retry)
                </button>
                <button
                  className="btn btn-outline"
                  style={{ fontSize: '13px', padding: '7px 14px', borderColor: '#fda4af', color: '#9f1239', backgroundColor: 'white' }}
                  onClick={() => setLlmError(null)}
                >
                  <XCircle size={14} /> বন্ধ করুন (Dismiss)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SCREEN: SAFETY BREAKOUT */}
      {step === 'safety' && (
        <div className="card" style={{ border: '2px solid #e11d48', backgroundColor: '#fff1f2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#e11d48' }}>
              <AlertTriangle size={32} />
              <h2 style={{ fontSize: '22px', fontWeight: '700', margin: 0 }}>জরুরি সহায়তা · BREAK-OUT</h2>
            </div>
            <button
              className="btn btn-outline"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '13px',
                padding: '6px 12px',
                borderColor: '#fda4af',
                color: '#be123c',
                backgroundColor: 'white'
              }}
              onClick={() => playVoice(safetyMessage || "আপনি এখনই বিপদে আছেন বলে মনে হচ্ছে। আপনার নিরাপত্তা সবার আগে।")}
            >
              {isLoadingAudio && currentPlayingText?.includes(safetyMessage || '') ? (
                <><RefreshCw className="animate-spin" size={16} /> <span>প্রস্তুত হচ্ছে...</span></>
              ) : isPlayingAudio && currentPlayingText?.includes(safetyMessage || '') ? (
                <><VolumeX size={16} /> <span>থামান</span></>
              ) : (
                <><Volume2 size={16} /> <span>শুনুন</span></>
              )}
            </button>
          </div>
          <p style={{ fontSize: '16px', lineHeight: '1.7', marginBottom: '20px', color: '#881337', whiteSpace: 'pre-line' }}>
            {safetyMessage || "আপনি এখনই বিপদে আছেন বলে মনে হচ্ছে। আপনার নিরাপত্তা সবার আগে।"}
          </p>
          <div style={{ background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid #fecdd3', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '18px', fontWeight: '700', color: '#be123c', marginBottom: '8px' }}>
              <PhoneCall size={20} />
              জাতীয় হেল্পলাইন: ১৬৪৩০ / ১০৯
            </div>
            <p style={{ fontSize: '14px', color: '#475569' }}>
              আমাদের স্বয়ংক্রিয় প্রশ্নোত্তরের পরিবর্তে আপনার অভিযোগটি জরুরি (URGENT) হিসেবে তাৎক্ষণিক প্যারালিগ্যাল ও সহায়তা টিমে পাঠানো হয়েছে।
            </p>
          </div>
          <button 
            className="btn btn-urgent" 
            style={{ width: '100%', padding: '14px', fontSize: '16px' }}
            onClick={() => window.open('tel:16430')}
          >
            এখনই কল করুন (১৬৪৩০)
          </button>
        </div>
      )}

      {/* SCREEN: TOKEN BUDGET CONTINUATION DIALOG */}
      {step === 'continuation' && (
        <div className="card" style={{ border: '2px solid #0284c7', backgroundColor: '#f0f9ff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#0284c7' }}>
              <ArrowRightCircle size={32} />
              <h2 style={{ fontSize: '20px', fontWeight: '700', margin: 0 }}>টোকেন ও বিস্তারিত বিশ্লেষণ সম্মতি</h2>
            </div>
            {continuationPrompt && (
              <button
                className="btn btn-outline"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '13px',
                  padding: '6px 12px',
                  borderColor: '#bae6fd',
                  color: '#0284c7',
                  backgroundColor: 'white'
                }}
                onClick={() => playVoice(continuationPrompt)}
              >
                {isLoadingAudio && currentPlayingText === continuationPrompt ? (
                  <><RefreshCw className="animate-spin" size={16} /> <span>প্রস্তুত হচ্ছে...</span></>
                ) : isPlayingAudio && currentPlayingText === continuationPrompt ? (
                  <><VolumeX size={16} /> <span>থামান</span></>
                ) : (
                  <><Volume2 size={16} /> <span>শুনুন</span></>
                )}
              </button>
            )}
          </div>
          <p style={{ fontSize: '15px', lineHeight: '1.7', marginBottom: '20px', color: '#0c4a6e' }}>
            {continuationPrompt}
          </p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => {
                stopVoice();
                setStep('recording');
                setTextNarrative('');
              }}
            >
              সংক্ষেপ করুন
            </button>
            <button
              className="btn btn-primary"
              style={{ flex: 1.5, backgroundColor: '#0284c7' }}
              disabled={isLoading}
              onClick={() => {
                stopVoice();
                handleSendMessage("", true);
              }}
            >
              {isLoading ? <RefreshCw className="animate-spin" size={18} /> : 'হ্যাঁ, পরবর্তী টোকেন সম্পন্ন করুন'}
            </button>
          </div>
        </div>
      )}

      {/* SCREEN 1: WELCOME */}
      {step === 'welcome' && (
        <div className="card" style={{ textAlign: 'center', padding: '40px 24px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', backgroundColor: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
            <FileText size={32} />
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '12px' }}>অধিকার (Odhikar)</h1>
          <p style={{ fontSize: '16px', color: '#475569', marginBottom: '24px', lineHeight: '1.6' }}>
            এটি একটি স্বয়ংক্রিয় আইন সহায়তা সেবা — কোনো আইনজীবী নয়।<br />
            আপনার আইনি সমস্যা বা ঘটনার বিবরণ নিজের ভাষায় লিখুন।
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              className="btn btn-outline"
              style={{
                padding: '12px 20px',
                fontSize: '15px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                borderColor: (isPlayingAudio || isLoadingAudio) && currentPlayingText?.includes('এটি একটি স্বয়ংক্রিয় আইন সহায়তা') ? '#e11d48' : '#0284c7',
                color: (isPlayingAudio || isLoadingAudio) && currentPlayingText?.includes('এটি একটি স্বয়ংক্রিয় আইন সহায়তা') ? '#e11d48' : '#0284c7'
              }}
              onClick={() => playVoice('অধিকার। এটি একটি স্বয়ংক্রিয় আইন সহায়তা সেবা — কোনো আইনজীবী নয়। আপনার আইনি সমস্যা বা ঘটনার বিবরণ নিজের ভাষায় লিখুন।')}
            >
              {isLoadingAudio && currentPlayingText?.includes('এটি একটি স্বয়ংক্রিয় আইন সহায়তা') ? (
                <><RefreshCw className="animate-spin" size={18} /> <span>প্রস্তুত হচ্ছে...</span></>
              ) : isPlayingAudio && currentPlayingText?.includes('এটি একটি স্বয়ংক্রিয় আইন সহায়তা') ? (
                <><VolumeX size={18} /> <span>থামান</span></>
              ) : (
                <><Volume2 size={18} /> <span>শুনুন (Voice)</span></>
              )}
            </button>
            <button
              className="btn btn-primary"
              style={{ padding: '12px 28px', fontSize: '16px' }}
              onClick={() => {
                stopVoice();
                setStep('recording');
              }}
            >
              হ্যাঁ, শুরু করুন
            </button>
          </div>
        </div>
      )}

      {/* SCREEN 2: INTAKE / NARRATIVE INPUT */}
      {step === 'recording' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>যা ঘটেছে, নিজের ভাষায় বলুন বা লিখুন</h2>
              <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>
                আপনার আইনি সমস্যা মুখে বলুন (সরাসরি লেখা হবে) অথবা বাংলায় টাইপ করুন:
              </p>
            </div>
            {renderVoiceTypingButton()}
          </div>

          {voiceStatus && (
            <div style={{
              fontSize: '12px',
              padding: '8px 12px',
              borderRadius: '6px',
              marginBottom: '14px',
              backgroundColor: isListening ? '#eff6ff' : '#f0fdf4',
              color: isListening ? '#1e40af' : '#15803d',
              border: `1px solid ${isListening ? '#bfdbfe' : '#bbf7d0'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              {isListening ? <Radio size={14} className="mic-recording-pulse" /> : <CheckCircle2 size={14} />}
              <span>{voiceStatus}</span>
            </div>
          )}

          <textarea
            rows={5}
            value={textNarrative}
            onChange={(e) => setTextNarrative(e.target.value)}
            placeholder="আপনার সমস্যা বা ঘটনার বিবরণ বিস্তারিতভাবে বাংলায় বলুন বা লিখুন... (কথা বললে সরাসরি এখানে লেখা হবে)"
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: '8px',
              border: isListening ? '1.5px solid #0284c7' : '1px solid #cbd5e1',
              fontFamily: 'inherit',
              fontSize: '15px',
              lineHeight: '1.6',
              marginBottom: '16px',
              boxSizing: 'border-box',
              transition: 'border-color 0.2s ease',
              boxShadow: isListening ? '0 0 0 3px rgba(2, 132, 199, 0.15)' : 'none'
            }}
          />

          {/* Demo Scenario Selectors */}
          <div style={{ marginBottom: '20px', padding: '12px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: '#64748b', display: 'block', marginBottom: '8px' }}>
              অথবা সরাসরি ডেমো পরিস্থিতি বাছাই করুন:
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button className="btn btn-outline" style={{ fontSize: '12px', padding: '5px 10px' }} onClick={() => handleLoadSample('dower')}>
                দেনমোহর ও ভরণপোষণ (N1)
              </button>
              <button className="btn btn-outline" style={{ fontSize: '12px', padding: '5px 10px' }} onClick={() => handleLoadSample('wages')}>
                বকেয়া মজুরি (N4)
              </button>
              <button className="btn btn-outline" style={{ fontSize: '12px', padding: '5px 10px', borderColor: '#fca5a5', color: '#b91c1c' }} onClick={() => handleLoadSample('violence')}>
                সহিংসতা ব্রেক-আউট (N6)
              </button>
              <button className="btn btn-outline" style={{ fontSize: '12px', padding: '5px 10px', borderColor: '#bae6fd', color: '#0284c7' }} onClick={() => handleLoadSample('long')}>
                দীর্ঘ বিবরণ (টোকেন কন্টিনিউয়েশন টেস্ট)
              </button>
            </div>
          </div>

          <button
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', fontSize: '15px' }}
            disabled={isLoading || !textNarrative.trim()}
            onClick={() => handleSendMessage()}
          >
            {isLoading ? <RefreshCw className="animate-spin" size={18} /> : <Send size={18} />}
            {isLoading ? 'বিশ্লেষণ করা হচ্ছে...' : 'জমা দিন'}
          </button>
        </div>
      )}

      {/* SCREEN 3: FOLLOW-UP QUESTION & CHAT HISTORY */}
      {step === 'follow_up' && (
        <div className="card">
          {/* Ongoing Conversation History Bubble Thread */}
          {chatHistory.length > 0 && (
            <div style={{ marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <MessageSquare size={14} /> পূর্ববর্তী বার্তা ও প্রশ্নোত্তর
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '180px', overflowY: 'auto' }}>
                {chatHistory.map((msg, idx) => (
                  <div 
                    key={idx}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                    }}
                  >
                    <div 
                      style={{
                        backgroundColor: msg.role === 'user' ? '#e0f2fe' : '#f8fafc',
                        color: msg.role === 'user' ? '#0369a1' : '#334155',
                        border: msg.role === 'user' ? '1px solid #bae6fd' : '1px solid #e2e8f0',
                        padding: '8px 12px',
                        borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                        fontSize: '13px',
                        maxWidth: '90%'
                      }}
                    >
                      {msg.content ? (
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                          <span>
                            {msg.content}
                            {isStreaming && idx === chatHistory.length - 1 && msg.role === 'assistant' && (
                              <span style={{ display: 'inline-block', width: '6px', height: '14px', backgroundColor: '#0284c7', marginLeft: '4px', verticalAlign: 'middle', animation: 'pulse 1s infinite' }}></span>
                            )}
                          </span>
                          {msg.role === 'assistant' && msg.content && !isStreaming && (
                            <button
                              onClick={() => playVoice(msg.content)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                padding: '2px',
                                color: (isPlayingAudio || isLoadingAudio) && currentPlayingText === msg.content ? '#e11d48' : '#0284c7',
                                display: 'flex',
                                alignItems: 'center'
                              }}
                              title="বার্তাটি শুনুন"
                            >
                              {isLoadingAudio && currentPlayingText === msg.content ? (
                                <RefreshCw className="animate-spin" size={14} />
                              ) : isPlayingAudio && currentPlayingText === msg.content ? (
                                <VolumeX size={14} />
                              ) : (
                                <Volume2 size={14} />
                              )}
                            </button>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: '#64748b', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <RefreshCw className="animate-spin" size={14} /> {streamStatus || 'আইনি তথ্য বিশ্লেষণ করা হচ্ছে...'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '10px', marginBottom: '16px' }}>
            <div>
              <div style={{ fontSize: '13px', color: '#0284c7', fontWeight: '600', marginBottom: '8px' }}>
                অতিরিক্ত তথ্য প্রয়োজন (Follow-up)
              </div>
              <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                {followUpQuestion || (isStreaming ? 'প্রশ্ন প্রস্তুত হচ্ছে...' : '')}
              </h2>
            </div>
            {followUpQuestion && (
              <button
                className="btn btn-outline"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '13px',
                  padding: '6px 12px',
                  flexShrink: 0,
                  borderColor: (isPlayingAudio || isLoadingAudio) && currentPlayingText === followUpQuestion ? '#e11d48' : '#0284c7',
                  color: (isPlayingAudio || isLoadingAudio) && currentPlayingText === followUpQuestion ? '#e11d48' : '#0284c7'
                }}
                onClick={() => playVoice(followUpQuestion)}
                title="প্রশ্নটি শুনুন"
              >
                {isLoadingAudio && currentPlayingText === followUpQuestion ? (
                  <><RefreshCw className="animate-spin" size={16} /> <span>প্রস্তুত হচ্ছে...</span></>
                ) : isPlayingAudio && currentPlayingText === followUpQuestion ? (
                  <><VolumeX size={16} /> <span>থামান</span></>
                ) : (
                  <><Volume2 size={16} /> <span>শুনুন</span></>
                )}
              </button>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '600', color: '#475569' }}>আপনার উত্তর মুখে বলুন বা লিখুন:</span>
            {renderVoiceTypingButton()}
          </div>

          {voiceStatus && (
            <div style={{
              fontSize: '12px',
              padding: '6px 12px',
              borderRadius: '6px',
              marginBottom: '10px',
              backgroundColor: isListening ? '#eff6ff' : '#f0fdf4',
              color: isListening ? '#1e40af' : '#15803d',
              border: `1px solid ${isListening ? '#bfdbfe' : '#bbf7d0'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              {isListening ? <Radio size={13} className="mic-recording-pulse" /> : <CheckCircle2 size={13} />}
              <span>{voiceStatus}</span>
            </div>
          )}

          <textarea
            rows={3}
            value={textNarrative}
            onChange={(e) => setTextNarrative(e.target.value)}
            placeholder="উত্তর মুখে বলুন বা এখানে লিখুন... (কথা বললে সরাসরি লেখা হবে)"
            style={{
              width: '100%',
              padding: '12px',
              borderRadius: '8px',
              border: isListening ? '1.5px solid #0284c7' : '1px solid #cbd5e1',
              fontFamily: 'inherit',
              fontSize: '15px',
              marginBottom: '16px',
              boxSizing: 'border-box',
              transition: 'border-color 0.2s ease',
              boxShadow: isListening ? '0 0 0 3px rgba(2, 132, 199, 0.15)' : 'none'
            }}
          />

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              className="btn btn-outline"
              style={{ flex: 1 }}
              onClick={() => {
                stopVoice();
                handleSendMessage("জানি না / মনে নেই");
              }}
            >
              জানি না / মনে নেই
            </button>
            <button
              className="btn btn-primary"
              style={{ flex: 1 }}
              disabled={isLoading || !textNarrative.trim()}
              onClick={() => {
                stopVoice();
                handleSendMessage();
              }}
            >
              {isLoading ? <RefreshCw className="animate-spin" size={18} /> : 'উত্তর দিন'}
            </button>
          </div>
        </div>
      )}

      {/* SCREEN 4: YOUR RIGHTS */}
      {step === 'rights' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0e7090' }}>
              <CheckCircle2 size={24} />
              <h2 style={{ fontSize: '20px', fontWeight: '700', margin: 0 }}>আপনার আইনি অধিকার ও পথ</h2>
            </div>
            {rightsExplanation && (
              <button
                className="btn btn-outline"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '13px',
                  padding: '6px 14px',
                  borderColor: (isPlayingAudio || isLoadingAudio) && currentPlayingText === rightsExplanation ? '#e11d48' : '#0e7090',
                  color: (isPlayingAudio || isLoadingAudio) && currentPlayingText === rightsExplanation ? '#e11d48' : '#0e7090'
                }}
                onClick={() => playVoice(rightsExplanation)}
              >
                {isLoadingAudio && currentPlayingText === rightsExplanation ? (
                  <><RefreshCw className="animate-spin" size={16} /> <span>প্রস্তুত হচ্ছে...</span></>
                ) : isPlayingAudio && currentPlayingText === rightsExplanation ? (
                  <><VolumeX size={16} /> <span>থামান</span></>
                ) : (
                  <><Volume2 size={16} /> <span>আবার শুনুন (Listen)</span></>
                )}
              </button>
            )}
          </div>
          <p style={{ fontSize: '15px', lineHeight: '1.7', whiteSpace: 'pre-line', color: '#334155', marginBottom: '24px' }}>
            {rightsExplanation}
          </p>

          <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary" onClick={() => { stopVoice(); setStep('referral'); }}>
              এগিয়ে যান (ক্লিনিক ও আবেদন) <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* SCREEN 5: REFERRAL & DRAFT COMPLAINT */}
      {step === 'referral' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '700', margin: 0 }}>নিকটতম আইন সহায়তা কেন্দ্র</h2>
            <button
              className="btn btn-outline"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '13px',
                padding: '6px 12px',
                borderColor: '#bbf7d0',
                color: '#15803d',
                backgroundColor: 'white'
              }}
              onClick={() => playVoice(`আপনার নিকটতম আইন সহায়তা কেন্দ্র ${referralInfo?.clinic || ''}। নির্ধারিত সাক্ষাৎ ${referralInfo?.slot || ''}। আপনার তথ্যের ভিত্তিতে প্রাথমিক সারসংক্ষেপ ও খসড়া তৈরি করে প্যারালেগ্যাল বরাবর পাঠানো হয়েছে।`)}
            >
              {isLoadingAudio && currentPlayingText?.includes('নিকটতম আইন সহায়তা কেন্দ্র') ? (
                <><RefreshCw className="animate-spin" size={16} /> <span>প্রস্তুত হচ্ছে...</span></>
              ) : isPlayingAudio && currentPlayingText?.includes('নিকটতম আইন সহায়তা কেন্দ্র') ? (
                <><VolumeX size={16} /> <span>থামান</span></>
              ) : (
                <><Volume2 size={16} /> <span>শুনুন</span></>
              )}
            </button>
          </div>
          <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
            <div style={{ fontWeight: '700', fontSize: '17px', color: '#166534', marginBottom: '4px' }}>
              {referralInfo?.clinic}
            </div>
            <div style={{ fontSize: '14px', color: '#15803d' }}>
              নির্ধারিত সাক্ষাৎ: {referralInfo?.slot}
            </div>
            <div style={{ fontSize: '13px', color: '#475569', marginTop: '8px' }}>
              আপনার তথ্যের ভিত্তিতে প্রাথমিক সারসংক্ষেপ ও খসড়া তৈরি করে প্যারালেগ্যাল বরাবর পাঠানো হয়েছে (মামলা আইডি: #{caseId})।
            </div>
          </div>

          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
            প্রাথমিক অভিযোগের খসড়া (প্যারালেগ্যাল পর্যালোচনার জন্য):
          </h3>
          <div style={{ backgroundColor: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '13px', whiteSpace: 'pre-line', color: '#334155', maxHeight: '200px', overflowY: 'auto', marginBottom: '20px' }}>
            {draftComplaint}
          </div>

          <button 
            className="btn btn-primary" 
            style={{ width: '100%' }}
            onClick={() => {
              stopVoice();
              setStep('welcome');
              setTextNarrative('');
              setSessionState(null);
              setChatHistory([]);
            }}
          >
            নতুন আবেদন শুরু করুন
          </button>
        </div>
      )}
    </div>
  );
};
