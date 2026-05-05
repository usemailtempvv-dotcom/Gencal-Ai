import React from 'react';

export default function HistoryPage({ callLogs = [] }) {
  return (
    <div className="min-h-screen bg-surface-container-lowest p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-semibold mb-6">Call History</h1>
        <div className="glass-surface rounded-2xl overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-surface-variant/60">
              <tr>
                <th className="p-4">Date</th>
                <th className="p-4">Caller</th>
                <th className="p-4">Duration</th>
                <th className="p-4">Summary</th>
                <th className="p-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {callLogs.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-6 text-center text-on-surface-variant">No calls yet</td>
                </tr>
              )}
              {callLogs.map((c) => (
                <tr key={c.id} className="border-t border-white/5">
                  <td className="p-4 align-top">{new Date(c.timestamp).toLocaleString()}</td>
                  <td className="p-4 align-top">{c.from}</td>
                  <td className="p-4 align-top">{c.duration}</td>
                  <td className="p-4 align-top max-w-xl line-clamp-2">{c.summary}</td>
                  <td className="p-4 align-top">
                    <button className="mr-2 p-2 rounded-md bg-surface-variant/50">Play</button>
                    <button className="p-2 rounded-md bg-surface-variant/50">Details</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
