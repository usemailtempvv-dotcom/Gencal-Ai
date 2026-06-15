import React, { useCallback, useEffect, useRef, useState } from 'react';
import './App.css';
import DashboardNew from './components/DashboardNew';
import AdminApp from './admin/AdminApp';
import Login from './pages/Login';
import Signup from './pages/Signup';
import { supabase, useAuth } from './contexts/AuthContext';

const SILENCE_TIMEOUT_MS = 1600;
const MIN_VALID_TEXT_LENGTH = 3;
const ADMIN_SESSION_KEY = 'admin_authenticated';
const BACKEND_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'https://gencal-ai-production.up.railway.app';

function App() {
  const { isAuthenticated, loading, user } = useAuth();

  const [locationPath, setLocationPath] = useState(() => (typeof window !== 'undefined' ? window.location.pathname : '/'));
  const [backendStatus, setBackendStatus] = useState('checking');

  const [isCallActive, setIsCallActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  const [sttError, setSttError] = useState('');
  const [ttsError, setTtsError] = useState('');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [lastUserUtterance, setLastUserUtterance] = useState('');
  const [lastAssistantResponse, setLastAssistantResponse] = useState('');
  const [intentLabel, setIntentLabel] = useState('conversation');

  const [conversationTurns, setConversationTurns] = useState([]);
  const [historyLogs, setHistoryLogs] = useState([]);

  const loadHistoryFromSupabase = useCallback(async () => {
    if (!user?.id) return;

    try {
      const { data, error } = await supabase
        .from('call_history')
        .select('id, created_at, duration_seconds, summary, intent, turn_count')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) {
        console.warn('Could not load history from Supabase:', error.message);
        return;
      }

      const mapped = (data || []).map((row) => ({
        id: String(row.id),
        timestamp: row.created_at,
        from: 'Web User',
        duration: `${row.duration_seconds || 0}s`,
        summary: row.summary || 'Call completed',
        intent: row.intent || 'general',
        turnCount: row.turn_count || 0,
      }));

      setHistoryLogs(mapped);
    } catch (error) {
      console.warn('Supabase history load failed:', error);
    }
  }, [user?.id]);

  const saveHistoryToSupabase = useCallback(async (entry) => {
    if (!user?.id) return;

    const durationSeconds = Number(String(entry.duration || '0').replace(/[^0-9]/g, '')) || 0;

    try {
      const { error } = await supabase.from('call_history').insert({
        user_id: user.id,
        duration_seconds: durationSeconds,
        summary: entry.summary || null,
        intent: entry.intent || null,
        turn_count: entry.turnCount || 0,
        metadata: {
          from: entry.from || 'Web User',
          timestamp: entry.timestamp,
        },
      });

      if (error) {
        console.warn('Could not save history to Supabase:', error.message);
      }
    } catch (error) {
      console.warn('Supabase history save failed:', error);
    }
  }, [user?.id]);

  const recognitionRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const shouldRestartRef = useRef(false);
  const speechDetectedRef = useRef(false);
  const latestChunkRef = useRef('');
  const callStartRef = useRef(null);
  const finalTranscriptRef = useRef('');
  const interimTranscriptRef = useRef('');

  const isCallActiveRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const isProcessingRef = useRef(false);
  const isMutedRef = useRef(false);

  const isAdminRoute = locationPath.startsWith('/admin');
  const isAuthRoute = locationPath === '/login' || locationPath === '/signup';

  const hasAdminSession = useCallback(() => {
    if (typeof window === 'undefined') return false;
    return window.sessionStorage.getItem(ADMIN_SESSION_KEY) === 'true';
  }, []);

  const parseJsonResponse = useCallback(async (response, fallbackMessage) => {
    const rawBody = await response.text();
    try {
      return JSON.parse(rawBody || '{}');
    } catch (error) {
      const snippet = (rawBody || '').slice(0, 120).replace(/\s+/g, ' ').trim();
      const message = snippet
        ? `${fallbackMessage} (status ${response.status}). Response starts with: ${snippet}`
        : `${fallbackMessage} (status ${response.status}).`;
      throw new Error(message);
    }
  }, []);

  useEffect(() => {
    isCallActiveRef.current = isCallActive;
  }, [isCallActive]);

  useEffect(() => {
    isSpeakingRef.current = isSpeaking;
  }, [isSpeaking]);

  useEffect(() => {
    isProcessingRef.current = isProcessing;
  }, [isProcessing]);

  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  const handleNavigate = useCallback((nextPath) => {
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', nextPath);
    }
    setLocationPath(nextPath);
  }, []);

  useEffect(() => {
    const handlePopState = () => setLocationPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setBackendStatus(SpeechRecognition ? 'ready' : 'offline');

    if (typeof window !== 'undefined') {
      const savedHistory = window.localStorage.getItem('mockCallHistory');
      if (savedHistory) {
        try {
          setHistoryLogs(JSON.parse(savedHistory));
        } catch (error) {
          console.warn('Could not parse stored call history:', error);
        }
      }
    }
  }, []);

  useEffect(() => {
    loadHistoryFromSupabase();
  }, [loadHistoryFromSupabase]);

  useEffect(() => {
    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
      window.speechSynthesis.cancel();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (error) {
          console.warn('Recognition stop on unmount failed:', error);
        }
      }

    };
  }, []);

  const cleanupSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  const stopListening = useCallback(() => {
    shouldRestartRef.current = false;
    cleanupSilenceTimer();
    setIsListening(false);

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (error) {
        console.warn('Recognition stop failed:', error);
      }
    }
  }, [cleanupSilenceTimer]);

  const speakResponse = useCallback((responseText) => {
    const text = (responseText || '').trim();
    if (!text) return;

    stopListening();
    setIsSpeaking(true);
    setTtsError('');

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onend = () => {
      setIsSpeaking(false);
      if (isCallActiveRef.current && !isMutedRef.current) {
        setTimeout(() => {
          if (isCallActiveRef.current && !isMutedRef.current) {
            shouldRestartRef.current = true;
            if (recognitionRef.current) {
              try {
                recognitionRef.current.start();
                setIsListening(true);
              } catch (error) {
                console.warn('Recognition restart failed:', error);
              }
            }
          }
        }, 180);
      }
    };

    utterance.onerror = (event) => {
      setIsSpeaking(false);
      setTtsError(event.error || 'Speech synthesis failed');
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }, [stopListening]);

  const handleSpeech = useCallback((event) => {
    let finalText = '';
    let interimText = '';

    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const piece = event.results[i][0].transcript || '';
      if (event.results[i].isFinal) {
        finalText += `${piece} `;
      } else {
        interimText += `${piece} `;
      }
    }

    const normalizedFinal = finalText.replace(/[^a-zA-Z0-9\u0600-\u06FF\s]/g, '').trim();
    const normalizedInterim = interimText.replace(/[^a-zA-Z0-9\u0600-\u06FF\s]/g, '').trim();

    if (normalizedFinal.length >= MIN_VALID_TEXT_LENGTH) {
      finalTranscriptRef.current = `${finalTranscriptRef.current} ${normalizedFinal}`.trim();
      speechDetectedRef.current = true;
      latestChunkRef.current = finalTranscriptRef.current;
    }

    interimTranscriptRef.current = normalizedInterim;
    const visibleTranscript = [finalTranscriptRef.current, interimTranscriptRef.current].filter(Boolean).join(' ').trim();
    setLiveTranscript(visibleTranscript);

    const candidate = (finalTranscriptRef.current || normalizedInterim).trim();
    if (candidate.length >= MIN_VALID_TEXT_LENGTH) {
      speechDetectedRef.current = true;
      latestChunkRef.current = candidate;
    }
  }, []);

  const processUserUtterance = useCallback(async (utterance) => {
    const text = (utterance || '').trim();
    if (text.length < MIN_VALID_TEXT_LENGTH || isProcessingRef.current || isSpeakingRef.current) {
      return;
    }

    isProcessingRef.current = true;
    setIsProcessing(true);
    setIsListening(false);
    setLastUserUtterance(text);

    try {
      const response = await fetch(`${BACKEND_BASE_URL}/api/program_query/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: text,
          emotion: 'neutral',
        }),
      });

      const data = await parseJsonResponse(response, 'Program query endpoint returned non-JSON');
      if (!response.ok) {
        throw new Error(data.error || 'Backend query failed');
      }

      const backendAnswer = data.natural_response || data.natural_response_raw || `You said: ${text}`;
      const backendIntent = data.intent || data.intent_used || 'conversation';
      const backendSource = data.answer_source || 'backend';

      setIntentLabel(backendIntent);
      setLastAssistantResponse(backendAnswer);
      setConversationTurns((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          userText: text,
          replyText: backendAnswer,
          intent: backendIntent,
          source: backendSource,
          timestamp: new Date().toISOString(),
        },
      ]);

      speakResponse(backendAnswer);
    } catch (error) {
      console.error('Backend routing failed:', error);
      console.error('Error details:', error.message, error.stack);
      const fallback = `You said: ${text}. This is a fallback response because the backend did not return an answer.`;
      setTtsError(`Backend error: ${error.message}` || 'Backend query failed');
      setLastAssistantResponse(fallback);
      setConversationTurns((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          userText: text,
          replyText: fallback,
          intent: 'fallback',
          source: 'frontend_fallback',
          timestamp: new Date().toISOString(),
        },
      ]);

      speakResponse(fallback);
    }

    setIsProcessing(false);
    isProcessingRef.current = false;
  }, [parseJsonResponse, speakResponse]);

  const detectSilence = useCallback(() => {
    cleanupSilenceTimer();

    silenceTimerRef.current = setTimeout(async () => {
      if (!isCallActiveRef.current || isSpeakingRef.current || isProcessingRef.current) {
        return;
      }

      const chunk = (latestChunkRef.current || '').trim();
      const wordCount = chunk.split(/\s+/).filter(Boolean).length;
      const hasMeaningfulSpeech = speechDetectedRef.current && chunk.length >= MIN_VALID_TEXT_LENGTH && wordCount >= 1;

      if (!hasMeaningfulSpeech) {
        return;
      }

      stopListening();
      await processUserUtterance(chunk);
      speechDetectedRef.current = false;
      latestChunkRef.current = '';
      finalTranscriptRef.current = '';
      interimTranscriptRef.current = '';
      setLiveTranscript('');
    }, SILENCE_TIMEOUT_MS);
  }, [cleanupSilenceTimer, processUserUtterance, stopListening]);

  const startListening = useCallback(() => {
    if (!isCallActiveRef.current || isSpeakingRef.current || isProcessingRef.current || isMutedRef.current) {
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSttError('SpeechRecognition is not supported in this browser.');
      return;
    }

    if (!recognitionRef.current) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        handleSpeech(event);

        const merged = Array.from(event.results)
          .map((result) => result[0]?.transcript || '')
          .join(' ')
          .trim();

        const normalized = merged.replace(/[^a-zA-Z0-9\u0600-\u06FF\s]/g, '').trim();
        const appearsVoiceLike = normalized.length >= MIN_VALID_TEXT_LENGTH;

        if (appearsVoiceLike) {
          detectSilence();
        }
      };

      recognition.onerror = (event) => {
        setIsListening(false);

        if (event.error === 'no-speech' || event.error === 'audio-capture' || event.error === 'network') {
          setSttError(`Speech recognition: ${event.error}`);
        }

        if (isCallActiveRef.current && !isSpeakingRef.current && !isProcessingRef.current && !isMutedRef.current) {
          setTimeout(() => {
            try {
              recognition.start();
              setIsListening(true);
              setSttError('');
            } catch (error) {
              console.warn('Recognition recover start failed:', error);
            }
          }, 300);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        if (shouldRestartRef.current && isCallActiveRef.current && !isSpeakingRef.current && !isProcessingRef.current && !isMutedRef.current) {
          setTimeout(() => {
            try {
              recognition.start();
              setIsListening(true);
            } catch (error) {
              console.warn('Recognition onend restart failed:', error);
            }
          }, 150);
        }
      };

      recognitionRef.current = recognition;
    }

    shouldRestartRef.current = true;
    speechDetectedRef.current = false;
    latestChunkRef.current = '';
    finalTranscriptRef.current = '';
    interimTranscriptRef.current = '';
    setSttError('');

    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch (error) {
      if (!String(error?.message || '').includes('already started')) {
        setSttError('Could not start recognition. Please allow microphone permissions.');
      }
    }
  }, [detectSilence, handleSpeech]);

  const startVoiceCall = useCallback(() => {
    setIsCallActive(true);
    isCallActiveRef.current = true;
    setIsMuted(false);
    setSttError('');
    setTtsError('');
    setLiveTranscript('');
    setLastUserUtterance('');
    setLastAssistantResponse('');
    setConversationTurns([]);
    callStartRef.current = Date.now();
    startListening();
  }, [startListening]);

  const endVoiceCall = useCallback(async () => {
    const startedAt = callStartRef.current || Date.now();
    const durationSec = Math.max(1, Math.floor((Date.now() - startedAt) / 1000));

    setIsCallActive(false);
    isCallActiveRef.current = false;
    setIsListening(false);
    setIsProcessing(false);
    setIsSpeaking(false);
    cleanupSilenceTimer();
    stopListening();
    window.speechSynthesis.cancel();

    if (conversationTurns.length > 0) {
      const summaryText = conversationTurns[conversationTurns.length - 1].replyText || 'Call completed';
      const lastTurn = conversationTurns[conversationTurns.length - 1];
      const detectedIntent = lastTurn?.intent || intentLabel || 'general';
      
      const newEntry = {
        id: `${Date.now()}`,
        timestamp: new Date().toISOString(),
        from: 'Web User',
        duration: `${durationSec}s`,
        summary: summaryText,
        intent: detectedIntent,
        turnCount: conversationTurns.length,
      };

      setHistoryLogs((prev) => {
        const updated = [newEntry, ...prev];
        if (typeof window !== 'undefined') {
          window.localStorage.setItem('mockCallHistory', JSON.stringify(updated));
        }
        return updated;
      });

      saveHistoryToSupabase(newEntry);
    }
  }, [cleanupSilenceTimer, conversationTurns, stopListening, intentLabel, saveHistoryToSupabase]);

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => {
      const next = !prev;
      if (next) {
        stopListening();
      } else if (isCallActiveRef.current && !isSpeakingRef.current && !isProcessingRef.current) {
        setTimeout(() => startListening(), 120);
      }
      return next;
    });
  }, [startListening, stopListening]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: '#131313', color: '#e5e2e1' }}>
        <div>
          <h2>Loading...</h2>
          <p>Please wait while we initialize your session</p>
        </div>
      </div>
    );
  }

  if (locationPath === '/login' && !isAuthenticated) {
    return <Login />;
  }

  if (locationPath === '/signup') {
    return <Signup />;
  }

  if (isAuthRoute && isAuthenticated) {
    window.location.href = '/dashboard';
    return null;
  }

  if (!isAuthenticated && !isAdminRoute && locationPath !== '/login' && locationPath !== '/signup') {
    return <Login />;
  }

  if (isAdminRoute) {
    if (locationPath === '/admin' || locationPath === '/admin/') {
      handleNavigate('/admin/login');
      return null;
    }

    if (locationPath === '/admin/login') {
      return <AdminApp pathname={locationPath} onNavigate={handleNavigate} />;
    }

    if (!hasAdminSession()) {
      handleNavigate('/admin/login');
      return null;
    }

    return <AdminApp pathname={locationPath} onNavigate={handleNavigate} />;
  }

  const callPhase = isSpeaking ? 'speaking' : isProcessing ? 'processing' : isListening ? 'listening' : isCallActive ? 'active' : 'idle';

  return (
    <DashboardNew
      isCallActive={isCallActive}
      callPhase={callPhase}
      onStartCall={startVoiceCall}
      onEndCall={endVoiceCall}
      onToggleMute={toggleMute}
      isMuted={isMuted}
      lastUserUtterance={lastUserUtterance || liveTranscript}
      lastAssistantResponse={lastAssistantResponse}
      backendStatus={backendStatus}
      sttDetectedLanguage={'en-US'}
      sttIntentLabel={intentLabel}
      sttEmotion={null}
      sttLoading={isProcessing}
      ttsLoading={isSpeaking}
      sttError={sttError}
      ttsError={ttsError}
      turns={conversationTurns}
      callLogs={historyLogs}
    />
  );
}

export default App;
