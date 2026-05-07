import React, { useState, useEffect } from 'react';

export default function ConversationHistory() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    setIsLoading(true);
    setErrorMessage('');

    try {
      const response = await fetch('/api/call_logs/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || response.statusText || 'Unable to load conversations');
      }

      const data = await response.json();
      const records = Array.isArray(data.calls) ? data.calls : [];

      const formattedData = records.map((record, index) => ({
        id: record.call_sid || `conversation-${index}`,
        caller: record.from_number || 'Unknown caller',
        toNumber: record.to_number || 'Unknown destination',
        direction: record.direction || 'unknown',
        call_status: record.call_status || 'unknown',
        duration: Number(record.duration) || 0,
        timestamp: record.timestamp,
        intent: record.intent || 'general',
        summary: record.call_status || 'Call record',
        transcript: record.transcript || [],
      }));

      setConversations(formattedData);
      setSelectedConversation(formattedData[0] || null);
    } catch (error) {
      console.error('Error loading conversations:', error);
      setErrorMessage('Could not load conversation history from the backend.');
      setConversations([]);
      setSelectedConversation(null);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    const secs = Number(seconds) || 0;
    const mins = Math.floor(secs / 60);
    const remaining = secs % 60;
    return `${mins}:${remaining.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const renderSummary = (conversation) => {
    if (!conversation) {
      return null;
    }

    return (
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-slate-400 mb-1">Caller</p>
          <p className="text-sm font-medium text-white">{conversation.caller}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400 mb-1">Destination</p>
          <p className="text-sm font-medium text-white">{conversation.toNumber}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400 mb-1">Direction</p>
          <p className="text-sm font-medium text-white capitalize">{conversation.direction}</p>
        </div>
        <div>
          <p className="text-xs text-slate-400 mb-1">Status</p>
          <p className="text-sm font-medium text-green-400">{conversation.call_status}</p>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">Conversation history</h2>
          <p className="text-slate-400 mt-2 max-w-2xl">
            Live conversation metadata is loaded from the Django backend API. Select a call to review its details.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={loadConversations}
            className="rounded-full bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-400 transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {errorMessage ? (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
          {errorMessage}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="rounded-3xl border border-slate-700 bg-slate-900/70 p-4 shadow-xl shadow-black/20">
            <div className="mb-4 px-3 py-4 border-b border-slate-700">
              <p className="text-sm font-semibold text-slate-300">Total conversations</p>
              <p className="text-3xl font-bold text-white">{conversations.length}</p>
            </div>
            <div className="grid gap-4">
              <div className="rounded-2xl bg-slate-950/80 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Total duration</p>
                <p className="mt-2 text-2xl font-semibold text-white">
                  {formatDuration(conversations.reduce((sum, item) => sum + item.duration, 0))}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-950/80 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Average duration</p>
                <p className="mt-2 text-2xl font-semibold text-white">
                  {conversations.length > 0 ? formatDuration(Math.round(conversations.reduce((sum, item) => sum + item.duration, 0) / conversations.length)) : '0:00'}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-950/80 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Backend</p>
                <p className="mt-2 text-2xl font-semibold text-white">Django</p>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="rounded-3xl border border-slate-700 bg-slate-900/70 shadow-xl shadow-black/20 overflow-hidden">
            <div className="border-b border-slate-700 bg-slate-950/80 px-6 py-5">
              <h3 className="text-lg font-semibold text-white">Recent call logs</h3>
            </div>
            <div className="divide-y divide-slate-800 max-h-[32rem] overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="p-8 text-center text-slate-500">
                  No backend call logs were found.
                </div>
              ) : (
                conversations.map((conversation) => (
                  <button
                    key={conversation.id}
                    onClick={() => setSelectedConversation(conversation)}
                    className={`w-full text-left p-4 transition ${selectedConversation?.id === conversation.id ? 'bg-blue-500/10' : 'hover:bg-slate-800/80'}`}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-white">{conversation.caller}</p>
                        <p className="text-xs text-slate-500">{formatDate(conversation.timestamp)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-slate-200">{formatDuration(conversation.duration)}</p>
                        <p className="text-xs text-slate-400">{conversation.call_status}</p>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-400">{conversation.direction}</span>
                      <span className="rounded-full bg-slate-800 px-2 py-1 text-slate-400">{conversation.intent}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-3xl border border-slate-700 bg-slate-900/70 shadow-xl shadow-black/20 overflow-hidden">
        <div className="border-b border-slate-700 bg-slate-950/80 px-6 py-5 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">Conversation details</h3>
            <p className="text-sm text-slate-500 mt-1">Detailed metadata from the backend call log API.</p>
          </div>
        </div>

        {selectedConversation ? (
          <div className="px-6 py-6 sm:px-8">
            <div className="grid gap-6 lg:grid-cols-3 mb-6">
              <div className="rounded-2xl bg-slate-950/80 p-5">
                <p className="text-xs text-slate-500 uppercase tracking-[0.16em] mb-2">Caller</p>
                <p className="text-sm font-semibold text-white">{selectedConversation.caller}</p>
              </div>
              <div className="rounded-2xl bg-slate-950/80 p-5">
                <p className="text-xs text-slate-500 uppercase tracking-[0.16em] mb-2">Duration</p>
                <p className="text-sm font-semibold text-white">{formatDuration(selectedConversation.duration)}</p>
              </div>
              <div className="rounded-2xl bg-slate-950/80 p-5">
                <p className="text-xs text-slate-500 uppercase tracking-[0.16em] mb-2">Status</p>
                <p className="text-sm font-semibold text-green-400">{selectedConversation.call_status}</p>
              </div>
            </div>

            {renderSummary(selectedConversation)}

            <div className="mt-6 rounded-2xl bg-slate-950/80 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm font-semibold text-white">Transcript</p>
                  <p className="text-xs text-slate-500 mt-1">This backend view is limited to stored call metadata.</p>
                </div>
                <button
                  onClick={() => setSelectedConversation(null)}
                  className="text-slate-400 hover:text-white transition"
                >
                  Clear
                </button>
              </div>

              {selectedConversation.transcript && selectedConversation.transcript.length > 0 ? (
                <div className="space-y-4 max-h-72 overflow-y-auto">
                  {selectedConversation.transcript.map((message, idx) => (
                    <div key={idx} className={`rounded-2xl p-4 ${message.sender === 'user' ? 'bg-blue-500/10 border border-blue-500/20' : 'bg-green-500/10 border border-green-500/20'}`}>
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <p className="text-sm font-semibold text-white">
                          {message.sender === 'user' ? 'User' : 'AI Assistant'}
                        </p>
                        {message.timestamp ? <span className="text-xs text-slate-500">{new Date(message.timestamp).toLocaleTimeString()}</span> : null}
                      </div>
                      <p className="text-slate-300 text-sm leading-relaxed">{message.text || message.message}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-8 text-center text-slate-400">
                  No conversation transcript has been stored for this call.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-12 text-center text-slate-500">
            Select a backend call log to review the conversation details.
          </div>
        )}
      </div>
    </div>
  );
}
