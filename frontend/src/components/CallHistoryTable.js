import React, { useState } from 'react';

export default function CallHistoryTable({ callLogs = [] }) {
  const [expandedId, setExpandedId] = useState(null);

  // Calculate statistics
  const totalCalls = callLogs.length;
  const totalDuration = callLogs.reduce((sum, call) => {
    const match = call.duration?.match(/(\d+)/);
    return sum + (match ? parseInt(match[1]) : 0);
  }, 0);

  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 rounded-xl p-6 backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium mb-1">Total Calls</p>
              <p className="text-white text-3xl font-bold">{totalCalls}</p>
            </div>
            <div className="p-3 bg-blue-500/30 rounded-lg">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/30 rounded-xl p-6 backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium mb-1">Total Duration</p>
              <p className="text-white text-3xl font-bold">{totalDuration}s</p>
            </div>
            <div className="p-3 bg-purple-500/30 rounded-lg">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500/20 to-green-600/10 border border-green-500/30 rounded-xl p-6 backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium mb-1">Avg. Duration</p>
              <p className="text-white text-3xl font-bold">{totalCalls > 0 ? Math.round(totalDuration / totalCalls) : 0}s</p>
            </div>
            <div className="p-3 bg-green-500/30 rounded-lg">
              <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-500/20 to-orange-600/10 border border-orange-500/30 rounded-xl p-6 backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium mb-1">Success Rate</p>
              <p className="text-white text-3xl font-bold">{totalCalls > 0 ? '100' : '0'}%</p>
            </div>
            <div className="p-3 bg-orange-500/30 rounded-lg">
              <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-slate-900/50 border border-white/10 rounded-xl overflow-hidden backdrop-blur">
        <div className="px-6 py-4 border-b border-white/10 bg-slate-950/50">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Call History
          </h3>
        </div>

        {callLogs.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <svg className="w-16 h-16 mx-auto text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-slate-400 text-lg">No call history yet</p>
            <p className="text-slate-500 text-sm mt-2">Start your first call to see the history here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-950/80 border-b border-white/10">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Date & Time</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Duration</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Transcript</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Intent</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {callLogs.map((call) => (
                  <React.Fragment key={call.id}>
                    <tr className="hover:bg-slate-800/30 transition-colors cursor-pointer" onClick={() => setExpandedId(expandedId === call.id ? null : call.id)}>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-white font-medium text-sm">{new Date(call.timestamp).toLocaleDateString()}</p>
                          <p className="text-slate-400 text-xs">{new Date(call.timestamp).toLocaleTimeString()}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-block bg-blue-500/20 text-blue-300 px-3 py-1 rounded-full text-sm font-medium">
                          {call.duration}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-slate-300 text-sm line-clamp-1">{call.summary || 'N/A'}</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-block bg-purple-500/20 text-purple-300 px-3 py-1 rounded-full text-sm font-medium">
                          {call.intent || 'general'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors" title="View Details">
                            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                    {expandedId === call.id && (
                      <tr className="bg-slate-950/50 border-t border-white/5">
                        <td colSpan={5} className="px-6 py-4">
                          <div className="space-y-3">
                            <div>
                              <p className="text-slate-400 text-xs font-semibold uppercase mb-1">Full Transcript</p>
                              <p className="text-slate-300 text-sm bg-slate-900/50 rounded p-3 border border-white/5">{call.summary || 'No transcript available'}</p>
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                              <div>
                                <p className="text-slate-400 text-xs font-semibold uppercase mb-1">Duration</p>
                                <p className="text-white text-sm">{call.duration}</p>
                              </div>
                              <div>
                                <p className="text-slate-400 text-xs font-semibold uppercase mb-1">Intent</p>
                                <p className="text-white text-sm">{call.intent || 'N/A'}</p>
                              </div>
                              <div>
                                <p className="text-slate-400 text-xs font-semibold uppercase mb-1">Status</p>
                                <p className="text-green-400 text-sm">Completed</p>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
