/**
 * Main App component for GenCall AI
 * This is the root component that manages the entire application
 */
import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import TwilioClient from './components/TwilioClient';
import CallLogs from './components/CallLogs';

function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [twilioToken, setTwilioToken] = useState(null);
  const [callStatus, setCallStatus] = useState('idle');
  const [incomingCall, setIncomingCall] = useState(null);
  const [callLogs, setCallLogs] = useState([]);
  const [tokenRequested, setTokenRequested] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sttLoading, setSttLoading] = useState(false);
  const [sttText, setSttText] = useState('');
  const [sttUrduTranscript, setSttUrduTranscript] = useState('');
  const [sttEnglishTranscript, setSttEnglishTranscript] = useState('');
  const [sttDetectedLanguage, setSttDetectedLanguage] = useState('');
  const [sttRomanUrdu, setSttRomanUrdu] = useState('');
  const [sttIntent, setSttIntent] = useState(null);
  const [sttEmotion, setSttEmotion] = useState(null);
  const [sttError, setSttError] = useState('');
  const [answerMeta, setAnswerMeta] = useState({
    answerSource: '',
    answerSourceConfidence: null,
    adminVerified: false,
    responseTimeMs: null,
    detectedIntent: '',
    messageSource: '',
  });
  const [programQuery, setProgramQuery] = useState(null);
  const [naturalResponse, setNaturalResponse] = useState('');
  const [programInput, setProgramInput] = useState('');
  const [programLoading, setProgramLoading] = useState(false);
  const [programError, setProgramError] = useState('');
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsError, setTtsError] = useState('');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const monitorIntervalRef = useRef(null);
  const voiceMetricsRef = useRef(null);
  const answerAudioRef = useRef(null);
  const answerAudioUrlRef = useRef(null);

  // Check backend status on component mount
  useEffect(() => {
    checkBackendStatus();
    fetchCallLogs();
    // Poll for call logs every 10 seconds
    const interval = setInterval(fetchCallLogs, 10000);
    return () => clearInterval(interval);
  }, []);

  // Auto-request token when backend is ready (only once)
  useEffect(() => {
    if (backendStatus === 'ready' && !twilioToken && !tokenRequested) {
      console.log('Backend ready, requesting initial token...');
      setTokenRequested(true);
      requestTwilioToken();
    }
  }, [backendStatus, twilioToken, tokenRequested]);

  /**
   * Check if backend API is running
   */
  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/test/');
      const data = await parseJsonResponse(response, 'Backend test endpoint returned non-JSON');
      setBackendStatus(data.twilio_configured ? 'ready' : 'not-configured');
    } catch (error) {
      console.error('Backend check failed:', error);
      setBackendStatus('offline');
    }
  };

  /**
   * Fetch call logs from backend
   */
  const fetchCallLogs = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/call_logs/');
      const data = await parseJsonResponse(response, 'Call logs endpoint returned non-JSON');
      setCallLogs(data.calls || []);
    } catch (error) {
      console.error('Failed to fetch call logs:', error);
    }
  };

  /**
   * Request Twilio token from backend
   */
  const requestTwilioToken = async () => {
    try {
      console.log('Requesting Twilio token from backend...');
      const response = await fetch('http://localhost:8000/api/generate_token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ identity: 'web-user' }),
      });
      
      console.log('Token response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }
      
      const data = await parseJsonResponse(response, 'Token endpoint returned non-JSON');
      console.log('✓ Token received, length:', data.token ? data.token.length : 0);
      setTwilioToken(data.token);
      return data.token;
    } catch (error) {
      console.error('❌ Failed to get Twilio token:', error);
      console.error('Please check backend configuration and ensure it is running.');
      return null;
    }
  };

  const detectAnswerLanguage = (text) => {
    if (!text) {
      return 'en';
    }
    return /[\u0600-\u06FF]/.test(text) ? 'ur' : 'en';
  };

  const formatResponseTime = (durationMs) => {
    if (typeof durationMs !== 'number' || Number.isNaN(durationMs) || durationMs < 0) {
      return null;
    }

    if (durationMs < 1000) {
      return `${Math.round(durationMs)} ms`;
    }

    return `${(durationMs / 1000).toFixed(2)} s`;
  };

  const formatIntentLabel = (intentValue) => {
    if (!intentValue) {
      return '';
    }

    if (typeof intentValue === 'string') {
      return intentValue;
    }

    if (typeof intentValue === 'object') {
      const label = intentValue.label || intentValue.intent || intentValue.name || '';
      const confidence = typeof intentValue.confidence === 'number' ? Math.round(intentValue.confidence * 100) : null;
      return confidence !== null && label ? `${label} (${confidence}%)` : label;
    }

    return String(intentValue);
  };

  const buildNoAnswerMessage = (queryText) => {
    const trimmedQuery = (queryText || '').trim();
    if (trimmedQuery) {
      return `I could not find a direct answer for "${trimmedQuery}". Please rephrase it or ask about fee, duration, admission, or scholarship.`;
    }

    return 'I could not find a direct answer. Please rephrase your question or ask about fee, duration, admission, or scholarship.';
  };

  const parseJsonResponse = async (response, fallbackMessage) => {
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
  };

  const speakAnswer = async (answerText, languageHint = null) => {
    const text = (answerText || '').trim();
    if (!text) {
      return;
    }

    try {
      setTtsLoading(true);
      setTtsError('');

      const response = await fetch('http://localhost:8000/api/text_to_speech/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          language: languageHint || detectAnswerLanguage(text),
        }),
      });

      if (!response.ok) {
        let errorMessage = 'Text-to-speech failed';
        try {
          const data = await parseJsonResponse(response, 'Text-to-speech endpoint returned non-JSON');
          errorMessage = data.error || errorMessage;
        } catch (error) {
          errorMessage = `Text-to-speech failed (${response.status})`;
        }
        throw new Error(errorMessage);
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      if (!answerAudioRef.current) {
        answerAudioRef.current = new Audio();
      }

      if (answerAudioUrlRef.current) {
        URL.revokeObjectURL(answerAudioUrlRef.current);
      }

      answerAudioUrlRef.current = audioUrl;
      answerAudioRef.current.src = audioUrl;
      await answerAudioRef.current.play();
    } catch (error) {
      console.error('Answer TTS failed:', error);
      setTtsError(error.message || 'Could not play answer audio.');
    } finally {
      setTtsLoading(false);
    }
  };

  /**
   * Send recorded audio to backend speech-to-text endpoint.
   */
  const transcribeAudio = async (audioBlob, voiceFeatures = null) => {
    try {
      setSttLoading(true);
      setSttError('');
      const requestStart = performance.now();

      const formData = new FormData();
      formData.append('file', audioBlob, 'speech.webm');
      formData.append('language', 'auto');
      if (voiceFeatures) {
        formData.append('voice_features', JSON.stringify(voiceFeatures));
      }

      const response = await fetch('http://localhost:8000/api/speech_to_text/', {
        method: 'POST',
        body: formData,
      });

      const rawBody = await response.text();
      let data = {};
      try {
        data = JSON.parse(rawBody);
      } catch (parseError) {
        throw new Error(`Backend returned non-JSON response (status ${response.status}).`);
      }

      if (!response.ok) {
        throw new Error(data.error || 'Transcription failed');
      }

      setSttText(data.text || '');
      setSttUrduTranscript(data.urdu_transcript || '');
      setSttEnglishTranscript(data.english_transcript || '');
      setSttDetectedLanguage(data.detected_language || 'unknown');
      setSttRomanUrdu(data.roman_urdu || '');
      setSttIntent(data.intent || null);
      setSttEmotion(data.emotion || null);
      const responseTimeMs = performance.now() - requestStart;
      const resolvedProgramQuery = data.program_query || data.scholarship_query || data.admission_query || (data.program_data || data.scholarship_data || data.admission_data || data.natural_response
        ? {
            program_data: data.program_data || data.scholarship_data || data.admission_data || null,
            scholarship_data: data.scholarship_data || null,
            admission_data: data.admission_data || null,
            natural_response: data.natural_response || '',
            program_name: data.program_name || '',
            level: data.level || '',
            faculty: data.program_faculty || data.faculty || '',
            scholarship_category: data.scholarship_category || '',
            admission_summary: data.admission_data || null,
            follow_up: data.follow_up || null,
          }
        : null);

      setProgramQuery(resolvedProgramQuery);
      const answerText = data.natural_response || (resolvedProgramQuery && resolvedProgramQuery.natural_response) || data.natural_response_raw || (data.found === false ? buildNoAnswerMessage(data.text || sttText) : '');
      setNaturalResponse(answerText);
      setAnswerMeta({
        answerSource: data.answer_source || 'unknown',
        answerSourceConfidence: typeof data.answer_source_confidence === 'number' ? data.answer_source_confidence : null,
        adminVerified: Boolean(data.admin_verified),
        responseTimeMs,
        detectedIntent: formatIntentLabel(data.intent || data.intent_used || ''),
        messageSource: 'Microphone transcript',
      });
      if (answerText) {
        const ttsLang = data.detected_language || detectAnswerLanguage(answerText);
        await speakAnswer(answerText, ttsLang);
      }
    } catch (error) {
      console.error('Speech-to-text failed:', error);
      setSttError(error.message || 'Speech-to-text failed');
    } finally {
      setSttLoading(false);
    }
  };

  /**
   * Manual text query for program responses.
   */
  const handleProgramQuery = async () => {
    const query = programInput.trim();
    if (!query) {
      setProgramError('Please type a program question.');
      return;
    }

    try {
      setProgramLoading(true);
      setProgramError('');
      const requestStart = performance.now();

      const formData = new FormData();
      formData.append('query', query);
      formData.append('emotion', (sttEmotion && sttEmotion.label) || 'neutral');

      const response = await fetch('http://localhost:8000/api/program_query/', {
        method: 'POST',
        body: formData,
      });

      const data = await parseJsonResponse(response, 'Program query endpoint returned non-JSON');
      if (!response.ok) {
        throw new Error(data.error || 'Program query failed');
      }

      const responseTimeMs = performance.now() - requestStart;

      setProgramQuery({
        program_data: data.program_data || null,
        scholarship_data: data.scholarship_data || null,
        admission_data: data.admission_data || null,
        natural_response: data.natural_response || '',
        program_name: data.program_name || '',
        level: data.level || '',
        faculty: data.faculty || '',
        scholarship_category: data.scholarship_category || '',
        admission_summary: data.admission_data || null,
        follow_up: data.follow_up || null,
        intent_used: data.intent || '',
      });
      const answerText = data.natural_response || data.natural_response_raw || (data.found === false ? buildNoAnswerMessage(query) : '');
      setNaturalResponse(answerText);
      setAnswerMeta({
        answerSource: data.answer_source || 'unknown',
        answerSourceConfidence: typeof data.answer_source_confidence === 'number' ? data.answer_source_confidence : null,
        adminVerified: Boolean(data.admin_verified),
        responseTimeMs,
        detectedIntent: formatIntentLabel(data.intent || data.intent_used || ''),
        messageSource: 'Typed question',
      });
      if (answerText) {
        await speakAnswer(answerText, detectAnswerLanguage(answerText));
      }
    } catch (error) {
      setProgramError(error.message || 'Failed to fetch program response');
    } finally {
      setProgramLoading(false);
    }
  };

  /**
   * Toggle microphone recording for speech-to-text.
   */
  const handleMicClick = async () => {
    if (isRecording && mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setSttError('Microphone is not supported in this browser.');
      return;
    }

    try {
      setSttError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        if (monitorIntervalRef.current) {
          clearInterval(monitorIntervalRef.current);
          monitorIntervalRef.current = null;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());

        if (audioContextRef.current) {
          try {
            await audioContextRef.current.close();
          } catch (e) {
            console.warn('Audio context close failed:', e);
          }
          audioContextRef.current = null;
        }

        setIsRecording(false);

        const metrics = voiceMetricsRef.current;
        const voiceFeatures = metrics && metrics.samples > 0
          ? {
              rms_avg: metrics.rmsSum / metrics.samples,
              rms_max: metrics.rmsMax,
              peak_max: metrics.peakMax,
              zcr_avg: metrics.zcrSum / metrics.samples,
              samples: metrics.samples,
            }
          : null;

        if (audioBlob.size > 0) {
          await transcribeAudio(audioBlob, voiceFeatures);
        } else {
          setSttError('No audio captured. Please try again.');
        }
      };

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        const audioContext = new AudioContextClass();
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        source.connect(analyser);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        voiceMetricsRef.current = {
          rmsSum: 0,
          rmsMax: 0,
          peakMax: 0,
          zcrSum: 0,
          samples: 0,
        };

        const sampleBuffer = new Float32Array(analyser.fftSize);
        monitorIntervalRef.current = setInterval(() => {
          if (!analyserRef.current || !voiceMetricsRef.current) {
            return;
          }

          analyserRef.current.getFloatTimeDomainData(sampleBuffer);

          let sumSquares = 0;
          let peak = 0;
          let zeroCrossings = 0;
          for (let i = 0; i < sampleBuffer.length; i += 1) {
            const v = sampleBuffer[i];
            sumSquares += v * v;
            if (Math.abs(v) > peak) {
              peak = Math.abs(v);
            }
            if (i > 0 && ((sampleBuffer[i - 1] >= 0 && v < 0) || (sampleBuffer[i - 1] < 0 && v >= 0))) {
              zeroCrossings += 1;
            }
          }

          const rms = Math.sqrt(sumSquares / sampleBuffer.length);
          const zcr = zeroCrossings / sampleBuffer.length;
          const m = voiceMetricsRef.current;
          m.rmsSum += rms;
          m.zcrSum += zcr;
          m.samples += 1;
          if (rms > m.rmsMax) {
            m.rmsMax = rms;
          }
          if (peak > m.peakMax) {
            m.peakMax = peak;
          }
        }, 120);
      }

      mediaRecorder.start();
      setIsRecording(true);
      setSttText('');
      setSttUrduTranscript('');
      setSttEnglishTranscript('');
      setSttDetectedLanguage('');
      setSttRomanUrdu('');
      setSttIntent(null);
      setSttEmotion(null);
      setAnswerMeta({
        answerSource: '',
        answerSourceConfidence: null,
        adminVerified: false,
        responseTimeMs: null,
        detectedIntent: '',
        messageSource: '',
      });
      setProgramQuery(null);
      setNaturalResponse('');
    } catch (error) {
      console.error('Microphone access denied or failed:', error);
      setSttError('Could not access microphone. Please allow microphone permission.');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 GenCall AI</h1>
        <p>AI-Powered Call Management System</p>
        <div className={`status-badge ${backendStatus}`}>
          Backend: {backendStatus === 'ready' ? '✓ Ready' : 
                   backendStatus === 'checking' ? '⌛ Checking...' : 
                   backendStatus === 'not-configured' ? '⚠ Not Configured' :
                   '✗ Offline'}
        </div>
      </header>

      <main className="App-main">
        {/* Home page speech-to-text card */}
        <div className="card">
          <h2>🎤 Speech To Text (Auto Urdu/English)</h2>
          <p className="stt-help-text">
            Click the mic, speak in Urdu or English, then click again to convert speech to text.
          </p>

          <div style={{ marginBottom: '16px' }}>
            <h3 style={{ marginBottom: '8px' }}>💬 Ask Program Question (Text)</h3>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <input
                type="text"
                placeholder="Example: fee of BS Computer Science"
                value={programInput}
                onChange={(e) => setProgramInput(e.target.value)}
                style={{
                  flex: '1 1 280px',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #cfd8dc',
                  fontSize: '14px',
                }}
              />
              <button
                className="btn btn-success"
                onClick={handleProgramQuery}
                disabled={programLoading}
              >
                {programLoading ? 'Checking...' : 'Get Answer'}
              </button>
            </div>
            {programError && <p className="stt-error" style={{ marginTop: '8px' }}>{programError}</p>}
            {ttsError && <p className="stt-error" style={{ marginTop: '8px' }}>{ttsError}</p>}
          </div>

          <button
            className={`btn ${isRecording ? 'btn-danger' : 'btn-primary'}`}
            onClick={handleMicClick}
            disabled={sttLoading}
          >
            {isRecording ? '⏹ Stop Recording' : '🎙 Start Microphone'}
          </button>

          {sttLoading && <p className="stt-status">Transcribing audio...</p>}
          {sttError && <p className="stt-error">{sttError}</p>}

          {naturalResponse && (
            <div style={{
              backgroundColor: '#e8f5e9',
              borderLeft: '5px solid #4caf50',
              padding: '18px',
              marginBottom: '18px',
              borderRadius: '6px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{ color: '#2e7d32', marginTop: 0, fontSize: '18px' }}>📋 Answer</h3>
              <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#1b5e20', lineHeight: '1.6', marginBottom: '12px' }}>
                {naturalResponse}
              </p>
              {(answerMeta.answerSource || answerMeta.responseTimeMs !== null) && (
                <div style={{
                  marginBottom: '12px',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  backgroundColor: '#f1f8f4',
                  border: '1px solid #c8e6c9',
                  fontSize: '13px',
                  color: '#2e7d32',
                }}>
                  {answerMeta.answerSource && (
                    <p style={{ margin: '4px 0' }}><strong>Source:</strong> {answerMeta.answerSource}</p>
                  )}
                  {answerMeta.messageSource && (
                    <p style={{ margin: '4px 0' }}><strong>Message source:</strong> {answerMeta.messageSource}</p>
                  )}
                  {answerMeta.detectedIntent && (
                    <p style={{ margin: '4px 0' }}><strong>Detected intent:</strong> {answerMeta.detectedIntent}</p>
                  )}
                  {typeof answerMeta.answerSourceConfidence === 'number' && (
                    <p style={{ margin: '4px 0' }}><strong>Confidence:</strong> {Math.round(answerMeta.answerSourceConfidence * 100)}%</p>
                  )}
                  <p style={{ margin: '4px 0' }}><strong>Admin verified:</strong> {answerMeta.adminVerified ? 'Yes' : 'No'}</p>
                  {formatResponseTime(answerMeta.responseTimeMs) && (
                    <p style={{ margin: '4px 0' }}><strong>Time taken:</strong> {formatResponseTime(answerMeta.responseTimeMs)}</p>
                  )}
                </div>
              )}
              <button
                className="btn btn-success"
                onClick={() => speakAnswer(naturalResponse, detectAnswerLanguage(naturalResponse))}
                disabled={ttsLoading}
                style={{ marginBottom: '12px' }}
              >
                {ttsLoading ? '🔊 Speaking...' : '🔊 Speak Answer'}
              </button>
              {programQuery && programQuery.program_data && (
                <div style={{ marginTop: '15px', fontSize: '14px', color: '#333', backgroundColor: '#f1f8f4', padding: '12px', borderRadius: '4px' }}>
                  {programQuery.program_data.program && (
                    <p style={{ margin: '6px 0' }}><strong>🎓 Program:</strong> {programQuery.program_data.program}</p>
                  )}
                  {programQuery.program_data.level && (
                    <p style={{ margin: '6px 0' }}><strong>📚 Level:</strong> {programQuery.program_data.level}</p>
                  )}
                  {!programQuery.program_data.level && programQuery.level && (
                    <p style={{ margin: '6px 0' }}><strong>📚 Level:</strong> {programQuery.level}</p>
                  )}
                  {(programQuery.program_data.faculty || programQuery.faculty) && (
                    <p style={{ margin: '6px 0' }}><strong>🏫 Faculty:</strong> {programQuery.program_data.faculty || programQuery.faculty}</p>
                  )}
                  {programQuery.program_data.admission_fee && (
                    <p style={{ margin: '6px 0' }}><strong>💳 Admission Fee:</strong> {programQuery.program_data.admission_fee}</p>
                  )}
                  {programQuery.program_data.semesters && (
                    <p style={{ margin: '6px 0' }}><strong>⏱️ Duration:</strong> {programQuery.program_data.semesters} Semesters</p>
                  )}
                  {programQuery.program_data.total_fee && (
                    <p style={{ margin: '6px 0' }}><strong>💰 Total Fee:</strong> {programQuery.program_data.total_fee}</p>
                  )}
                  {Array.isArray(programQuery.program_data.faculties) && programQuery.program_data.faculties.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      <p style={{ margin: '6px 0', fontWeight: 'bold' }}>🏫 Faculties:</p>
                      <ul style={{ margin: '0 0 0 18px', padding: 0 }}>
                        {programQuery.program_data.faculties.map((f) => (
                          <li key={f}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {Array.isArray(programQuery.program_data.programs) && programQuery.program_data.programs.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      <p style={{ margin: '6px 0', fontWeight: 'bold' }}>🎓 Programs:</p>
                      <ul style={{ margin: '0 0 0 18px', padding: 0 }}>
                        {programQuery.program_data.programs.map((p, idx) => (
                          <li key={`${p.program}-${idx}`}>{p.program}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {programQuery.program_data.policy_count !== undefined && (
                    <div style={{ marginTop: '8px' }}>
                      <p style={{ margin: '6px 0' }}><strong>🎓 Scholarship Policies:</strong> {programQuery.program_data.policy_count}</p>
                      <p style={{ margin: '6px 0' }}><strong>🏷️ Categories:</strong> {programQuery.program_data.category_count}</p>
                      {Array.isArray(programQuery.program_data.categories) && programQuery.program_data.categories.length > 0 && (
                        <div>
                          <p style={{ margin: '6px 0', fontWeight: 'bold' }}>📚 Available Categories:</p>
                          <ul style={{ margin: '0 0 0 18px', padding: 0 }}>
                            {programQuery.program_data.categories.map((item) => (
                              <li key={item}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                  {Array.isArray(programQuery.program_data) && programQuery.scholarship_category && (
                    <div style={{ marginTop: '8px' }}>
                      <p style={{ margin: '6px 0', fontWeight: 'bold' }}>🎓 Scholarship Category:</p>
                      <p style={{ margin: '6px 0' }}>{programQuery.scholarship_category}</p>
                      <p style={{ margin: '6px 0', fontWeight: 'bold' }}>📄 Policy Rows:</p>
                      <ul style={{ margin: '0 0 0 18px', padding: 0 }}>
                        {programQuery.program_data.map((policy, idx) => (
                          <li key={`${policy.category}-${idx}`}>
                            {policy.category} - {policy.criteria}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {programQuery.admission_data && !Array.isArray(programQuery.admission_data) && (
                    <div style={{ marginTop: '8px' }}>
                      <p style={{ margin: '6px 0' }}><strong>🏫 University:</strong> {programQuery.admission_data.university || 'N/A'}</p>
                      {programQuery.admission_data.admission_open !== undefined && (
                        <p style={{ margin: '6px 0' }}><strong>📢 Admission Open:</strong> {programQuery.admission_data.admission_open}</p>
                      )}
                      {programQuery.admission_data.intakes && (
                        <p style={{ margin: '6px 0' }}><strong>🗓️ Intakes:</strong> {programQuery.admission_data.intakes}</p>
                      )}
                      {programQuery.admission_data.required_documents && (
                        <div style={{ marginTop: '8px' }}>
                          <p style={{ margin: '6px 0', fontWeight: 'bold' }}>📄 Required Documents:</p>
                          <ul style={{ margin: '0 0 0 18px', padding: 0 }}>
                            {programQuery.admission_data.required_documents.map((doc) => (
                              <li key={doc}>{doc}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {programQuery.admission_data.deadlines && (
                        <div style={{ marginTop: '8px' }}>
                          <p style={{ margin: '6px 0', fontWeight: 'bold' }}>⏳ Deadlines:</p>
                          <p style={{ margin: '6px 0' }}>Spring: {programQuery.admission_data.deadlines.spring_last_date || 'N/A'}</p>
                          <p style={{ margin: '6px 0' }}>Fall: {programQuery.admission_data.deadlines.fall_last_date || 'N/A'}</p>
                        </div>
                      )}
                      {programQuery.admission_data.eligibility && (
                        <div style={{ marginTop: '8px' }}>
                          <p style={{ margin: '6px 0', fontWeight: 'bold' }}>✅ Eligibility:</p>
                          <p style={{ margin: '6px 0' }}>Qualification: {programQuery.admission_data.eligibility.minimum_qualification || 'N/A'}</p>
                          <p style={{ margin: '6px 0' }}>Marks: {programQuery.admission_data.eligibility.minimum_marks || 'N/A'}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
              {programQuery && programQuery.follow_up && (
                <div style={{ marginTop: '10px', padding: '10px', background: '#fff8e1', borderLeft: '4px solid #ffb300', borderRadius: '4px' }}>
                  <strong>Next Step:</strong> {programQuery.follow_up.type === 'choose_level' && 'Please choose one level: Associate, Undergraduate, or Postgraduate.'}
                  {programQuery.follow_up.type === 'choose_faculty' && 'Please choose a faculty from the list above.'}
                  {programQuery.follow_up.type === 'choose_scholarship_category' && 'Please ask about a scholarship category like Merit, Alumni, Kinship, Sports, Talent, Corporate, or Loan.'}
                </div>
              )}
            </div>
          )}

          {sttText && (
            <div className="stt-result">
              <h3>Transcribed Text</h3>
              <p>{sttText}</p>
              <p><strong>Detected Language:</strong> {sttDetectedLanguage}</p>
              {sttUrduTranscript && (
                <>
                  <h3>Urdu Transcript</h3>
                  <p>{sttUrduTranscript}</p>
                </>
              )}
              {sttEnglishTranscript && (
                <>
                  <h3>English Transcript</h3>
                  <p>{sttEnglishTranscript}</p>
                </>
              )}
              {sttIntent && (
                <p>
                  <strong>Intent:</strong> {formatIntentLabel(sttIntent) || 'unknown'}
                </p>
              )}
              {sttEmotion && (
                <p>
                  <strong>Emotion:</strong> {sttEmotion.label || 'unknown'}
                  {typeof sttEmotion.confidence === 'number' ? ` (${Math.round(sttEmotion.confidence * 100)}%)` : ''}
                </p>
              )}
              {sttRomanUrdu && (
                <>
                  <h3>Roman Urdu</h3>
                  <p>{sttRomanUrdu}</p>
                </>
              )}
            </div>
          )}
        </div>

        {/* Dashboard showing call status */}
        <Dashboard 
          callStatus={callStatus}
          incomingCall={incomingCall}
          backendStatus={backendStatus}
        />

        {/* Twilio Client for making calls */}
        <TwilioClient
          token={twilioToken}
          onRequestToken={requestTwilioToken}
          onCallStatusChange={setCallStatus}
          onIncomingCall={setIncomingCall}
          backendStatus={backendStatus}
        />

        {/* Call Logs */}
        <CallLogs logs={callLogs} onRefresh={fetchCallLogs} />
      </main>

      <footer className="App-footer">
        <p>GenCall AI © 2026 | Built with Django & React | Powered by Twilio</p>
      </footer>
    </div>
  );
}

export default App;
