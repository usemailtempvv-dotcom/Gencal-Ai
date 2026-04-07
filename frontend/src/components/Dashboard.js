/**
 * Dashboard Component
 * Displays call status and incoming call information
 */
import React from 'react';

function Dashboard({ callStatus, incomingCall, backendStatus }) {
  return (
    <div className="card">
      <h2>📊 Dashboard</h2>
      
      {/* Backend Status Information */}
      {backendStatus === 'offline' && (
        <div className="error-box">
          <p>⚠️ Backend is offline. Please start the Django server.</p>
          <p>Run: <code>python manage.py runserver</code></p>
        </div>
      )}

      {backendStatus === 'not-configured' && (
        <div className="error-box">
          <p>⚠️ Twilio is not configured. Please update your .env file.</p>
        </div>
      )}

      {/* Call Status Display */}
      <div className={`call-status ${callStatus}`}>
        {callStatus === 'idle' && '📱 No Active Calls'}
        {callStatus === 'ringing' && '📞 Incoming Call...'}
        {callStatus === 'in-progress' && '🔊 Call In Progress'}
        {callStatus === 'ended' && '✓ Call Ended'}
      </div>

      {/* Incoming Call Alert */}
      {incomingCall && (
        <div className="incoming-call-alert">
          <h3>📞 Incoming Call</h3>
          <p><strong>From:</strong> {incomingCall.from || 'Unknown'}</p>
          <p><strong>Call SID:</strong> {incomingCall.callSid || 'N/A'}</p>
          <div style={{ marginTop: '1rem' }}>
            <button className="btn btn-success" onClick={incomingCall.accept}>
              ✓ Accept
            </button>
            <button className="btn btn-danger" onClick={incomingCall.reject}>
              ✗ Reject
            </button>
          </div>
        </div>
      )}

      {/* Information Section */}
      <div className="info-box">
        <p><strong>How to test:</strong></p>
        <p>1. Make sure Django backend is running</p>
        <p>2. Expose backend with ngrok: <code>ngrok http 8000</code></p>
        <p>3. Configure Twilio webhook to point to your ngrok URL</p>
        <p>4. Call your Twilio number to hear the AI greeting</p>
        <p>5. Use the button below to make outgoing test calls</p>
      </div>
    </div>
  );
}

export default Dashboard;
