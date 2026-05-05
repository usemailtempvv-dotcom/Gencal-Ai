import React from 'react';

export default function CallPage({
  isCallActive = false,
  callPhase = 'idle',
  onStartCall = () => {},
  onEndCall = () => {},
  onToggleMute = () => {},
  isMuted = false,
  lastUserUtterance = '',
  lastAssistantResponse = '',
  backendStatus = 'checking',
  answerMeta = {},
  sttDetectedLanguage = '',
  sttIntentLabel = '',
  sttEmotion = null,
  sttLoading = false,
  ttsLoading = false,
  sttError = '',
  ttsError = '',
  turns = [],
}) {
  const getPhaseLabel = () => {
    if (!isCallActive) return 'Ready to start';
    if (callPhase === 'listening') return 'Listening...';
    if (callPhase === 'processing') return 'Processing your query...';
    if (callPhase === 'speaking') return 'Assistant is speaking...';
    if (callPhase === 'ended') return 'Call ended';
    return 'In call';
  };

  const getPhaseClass = () => {
    if (!isCallActive) return 'idle';
    if (callPhase === 'listening') return 'listening';
    if (callPhase === 'processing') return 'processing';
    if (callPhase === 'speaking') return 'speaking';
    return 'idle';
  };

  return (
    <section className="call-shell">
      <div className="call-hero">
        <div className="call-hero-top">
          <div className="call-avatar">
            <span className="material-symbols-outlined">support_agent</span>
          </div>
          <div>
            <h2>Live Assistant Call</h2>
            <p>One continuous call. Pause after each query and the assistant responds automatically.</p>
          </div>
        </div>

        <div className={`call-phase-badge ${getPhaseClass()}`}>
          <span>{getPhaseLabel()}</span>
          <small>Backend: {backendStatus}</small>
        </div>

        <div className="call-controls">
          {!isCallActive ? (
            <button className="btn btn-primary" onClick={onStartCall}>
              Start Call
            </button>
          ) : (
            <>
              <button className="btn btn-secondary" onClick={onToggleMute}>
                {isMuted ? 'Unmute' : 'Mute'}
              </button>
              <button className="btn btn-danger" onClick={onEndCall}>
                End Call
              </button>
            </>
          )}
        </div>

        {(sttLoading || ttsLoading) && (
          <p className="call-state-hint">{sttLoading ? 'Detecting intent...' : 'Playing response...'}</p>
        )}

        {sttError && <p className="call-error">{sttError}</p>}
        {ttsError && <p className="call-error">{ttsError}</p>}

        <div className="call-grid">
          <article className="call-card">
            <h3>User said</h3>
            <p>{lastUserUtterance || 'Waiting for speech...'}</p>
            <div className="call-meta-row">
              <span>Language: {sttDetectedLanguage || 'N/A'}</span>
              <span>Intent: {sttIntentLabel || 'N/A'}</span>
            </div>
          </article>

          <article className="call-card">
            <h3>Assistant replied</h3>
            <p>{lastAssistantResponse || 'Response will appear here after your first query.'}</p>
            <div className="call-meta-row">
              <span>Source: {answerMeta.answerSource || 'N/A'}</span>
              <span>Time: {answerMeta.responseTimeMs ? `${Math.round(answerMeta.responseTimeMs)} ms` : 'N/A'}</span>
            </div>
          </article>

          <article className="call-card">
            <h3>Live status</h3>
            <p>{sttEmotion?.label ? `Detected emotion: ${sttEmotion.label}` : 'No emotion signal yet.'}</p>
            <div className="call-meta-row">
              <span>Muted: {isMuted ? 'Yes' : 'No'}</span>
              <span>Call: {isCallActive ? 'Active' : 'Inactive'}</span>
            </div>
          </article>
        </div>

        <div className="call-turns">
          <h3>Conversation</h3>
          {turns.length === 0 ? (
            <p className="call-turn-empty">Your conversation turns will appear here in real time.</p>
          ) : (
            turns.slice().reverse().map((turn) => (
              <div key={turn.id} className="call-turn-item">
                <p><strong>User:</strong> {turn.userText}</p>
                <p><strong>AI:</strong> {turn.replyText}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
