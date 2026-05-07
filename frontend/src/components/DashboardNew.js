import React, { useState } from 'react';
import CallPage from './CallPage';
import CallHistoryTable from './CallHistoryTable';
import ConversationHistory from './ConversationHistory';

export default function DashboardNew({
  isCallActive,
  callPhase,
  onStartCall,
  onEndCall,
  onToggleMute,
  isMuted,
  lastUserUtterance,
  lastAssistantResponse,
  sttDetectedLanguage,
  sttIntentLabel,
  sttEmotion,
  sttLoading,
  ttsLoading,
  sttError,
  ttsError,
  turns,
  callLogs,
  backendStatus,
}) {
  const [activeTab, setActiveTab] = useState('call');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-950/95 backdrop-blur-xl border-b border-white/10 sticky top-0 z-50 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-5 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-bold text-lg">G</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">GenCall AI</h1>
              <p className="text-xs text-slate-400">Voice Intelligence Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/50 rounded-full border border-slate-700">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-medium text-slate-300">System Active</span>
            </div>
            <button className="p-2 hover:bg-slate-900 rounded-lg transition-colors">
              <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="border-b border-white/10 bg-slate-950/50 sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab('call')}
              className={`px-6 py-4 font-semibold text-sm transition-all border-b-2 ${
                activeTab === 'call'
                  ? 'border-blue-500 text-white'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                Start Call
              </span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-4 font-semibold text-sm transition-all border-b-2 ${
                activeTab === 'history'
                  ? 'border-blue-500 text-white'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Call History
              </span>
            </button>
            <button
              onClick={() => setActiveTab('conversations')}
              className={`px-6 py-4 font-semibold text-sm transition-all border-b-2 ${
                activeTab === 'conversations'
                  ? 'border-blue-500 text-white'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Conversations
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'call' ? (
          <div>
            <CallPage
              isCallActive={isCallActive}
              callPhase={callPhase}
              onStartCall={onStartCall}
              onEndCall={onEndCall}
              onToggleMute={onToggleMute}
              isMuted={isMuted}
              lastUserUtterance={lastUserUtterance}
              lastAssistantResponse={lastAssistantResponse}
              sttDetectedLanguage={sttDetectedLanguage}
              sttIntentLabel={sttIntentLabel}
              sttEmotion={sttEmotion}
              sttLoading={sttLoading}
              ttsLoading={ttsLoading}
              sttError={sttError}
              ttsError={ttsError}
              turns={turns}
              backendStatus={backendStatus}
            />
          </div>
        ) : activeTab === 'history' ? (
          <div>
            <CallHistoryTable callLogs={callLogs} />
          </div>
        ) : (
          <div>
            <ConversationHistory />
          </div>
        )}
      </main>
    </div>
  );
}
