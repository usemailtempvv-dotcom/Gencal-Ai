/**
 * CallLogs Component
 * Displays call history from backend
 */
import React from 'react';

function CallLogs({ logs, onRefresh }) {
  /**
   * Format timestamp to readable format
   */
  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  /**
   * Format phone number for display
   */
  const formatPhoneNumber = (number) => {
    if (!number) return 'Unknown';
    // Simple formatting for US numbers
    if (number.startsWith('+1') && number.length === 12) {
      return `+1 (${number.slice(2, 5)}) ${number.slice(5, 8)}-${number.slice(8)}`;
    }
    return number;
  };

  /**
   * Get status badge class
   */
  const getStatusClass = (status) => {
    if (!status) return '';
    const lowerStatus = status.toLowerCase();
    if (lowerStatus.includes('completed') || lowerStatus.includes('answered')) {
      return 'completed';
    }
    if (lowerStatus.includes('progress') || lowerStatus.includes('ringing')) {
      return 'in-progress';
    }
    return 'no-answer';
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>📋 Call Logs</h2>
        <button className="btn btn-secondary" onClick={onRefresh} style={{ margin: 0 }}>
          🔄 Refresh
        </button>
      </div>

      {logs.length === 0 ? (
        <div className="info-box">
          <p>No call logs yet. Make a call to see logs here!</p>
        </div>
      ) : (
        <div>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            Showing {logs.length} most recent calls
          </p>
          {logs.map((log, index) => (
            <div key={index} className="call-log-item">
              <div className="call-log-info">
                <div className="call-log-number">
                  {log.direction === 'inbound' ? '📞 Incoming' : '📱 Outgoing'}:{' '}
                  {formatPhoneNumber(log.from_number)}
                </div>
                <div className="call-log-time">
                  {formatTime(log.timestamp)}
                  {log.duration && ` • ${log.duration}s`}
                </div>
              </div>
              <div className={`call-log-status ${getStatusClass(log.call_status)}`}>
                {log.call_status}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CallLogs;
