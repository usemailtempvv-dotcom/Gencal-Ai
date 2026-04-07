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
      const data = await response.json();
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
      const data = await response.json();
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
      
      const data = await response.json();
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
          const data = await response.json();
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
      const resolvedProgramQuery = data.program_query || data.scholarship_query || (data.program_data || data.scholarship_data || data.natural_response
        ? {
            program_data: data.program_data || data.scholarship_data || null,
            scholarship_data: data.scholarship_data || null,
            natural_response: data.natural_response || '',
            program_name: data.program_name || '',
            level: data.level || '',
            faculty: data.program_faculty || data.faculty || '',
            scholarship_category: data.scholarship_category || '',
            follow_up: data.follow_up || null,
          }
        : null);

      setProgramQuery(resolvedProgramQuery);
      const answerText = data.natural_response || resolvedProgramQuery?.natural_response || '';
      setNaturalResponse(answerText);
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

      const formData = new FormData();
      formData.append('query', query);
      formData.append('emotion', sttEmotion?.label || 'neutral');

      const response = await fetch('http://localhost:8000/api/program_query/', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Program query failed');
      }

      setProgramQuery({
        program_data: data.program_data || null,
        scholarship_data: data.scholarship_data || null,
        natural_response: data.natural_response || '',
        program_name: data.program_name || '',
        level: data.level || '',
        faculty: data.faculty || '',
        scholarship_category: data.scholarship_category || '',
        follow_up: data.follow_up || null,
        intent_used: data.intent || '',
      });
      const answerText = data.natural_response || '';
      setNaturalResponse(answerText);
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
              <button
                className="btn btn-success"
                onClick={() => speakAnswer(naturalResponse, detectAnswerLanguage(naturalResponse))}
                disabled={ttsLoading}
                style={{ marginBottom: '12px' }}
              >
                {ttsLoading ? '🔊 Speaking...' : '🔊 Speak Answer'}
              </button>
              {programQuery?.program_data && (
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
                </div>
              )}
              {programQuery?.follow_up && (
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
                  <strong>Intent:</strong> {sttIntent.label || 'unknown'}
                  {typeof sttIntent.confidence === 'number' ? ` (${Math.round(sttIntent.confidence * 100)}%)` : ''}
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
