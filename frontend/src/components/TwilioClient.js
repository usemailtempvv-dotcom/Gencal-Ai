/**
 * TwilioClient Component
 * Handles Twilio Voice SDK integration for making and receiving calls
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Device } from '@twilio/voice-sdk';

function TwilioClient({ token, onRequestToken, onCallStatusChange, onIncomingCall, backendStatus }) {
  const [device, setDevice] = useState(null);
  const [isReady, setIsReady] = useState(false);
  const [currentCall, setCurrentCall] = useState(null);
  const [callNumber, setCallNumber] = useState('');
  const [initError, setInitError] = useState(null);
  const deviceRef = useRef(null);
  const initializingRef = useRef(false);

  /**
   * Initialize Twilio Device when token is available
   */
  /**
   * Refresh token when it expires or becomes invalid
   */
  const handleTokenRefresh = useCallback(async () => {
    console.log('Refreshing token...');
    
    // Destroy current device
    if (deviceRef.current) {
      deviceRef.current.destroy();
      deviceRef.current = null;
      setDevice(null);
      setIsReady(false);
    }
    
    // Reset error and initializing state
    setInitError(null);
    initializingRef.current = false;
    
    // Request new token
    const newToken = await onRequestToken();
    if (newToken) {
      // The useEffect will reinitialize with the new token
      console.log('New token received, reinitializing device...');
    }
  }, [onRequestToken]);

  /**
   * Initialize Twilio Device with token
   */
  const initializeTwilioDevice = useCallback(async (accessToken) => {
    if (initializingRef.current) {
      console.log('⚠️ Already initializing, skipping...');
      return;
    }
    
    initializingRef.current = true;
    setInitError(null);
    
    try {
      console.log('=== Initializing Twilio Device ===');
      console.log('Token received:', accessToken ? 'YES' : 'NO');
      console.log('Token length:', accessToken ? accessToken.length : 0);
      console.log('Token preview:', accessToken ? accessToken.substring(0, 50) + '...' : 'null');
      
      if (!accessToken) {
        throw new Error('No access token provided');
      }
      
      console.log('Creating Device instance...');
      const newDevice = new Device(accessToken, {
        codecPreferences: ['opus', 'pcmu'],
        fakeLocalDTMF: true,
        enableRingingState: true,
      });
      console.log('Device instance created successfully');

      // Device ready event
      newDevice.on('registered', () => {
        console.log('✓ Twilio Device is ready and registered!');
        setIsReady(true);
      });

      // Device error event
      newDevice.on('error', (error) => {
        console.error('❌ Twilio Device error event:', error);
        console.error('Error code:', error?.code);
        console.error('Error message:', error?.message);
        console.error('Error type:', typeof error);
        console.error('Error keys:', error ? Object.keys(error) : 'N/A');
        
        // Check if it's a token-related error
        if (error?.code === 20101 || error?.code === 20104) {
          // AccessTokenInvalid or AccessTokenExpired
          console.log('Token error detected, requesting new token...');
          handleTokenRefresh();
        } else {
          const msg = error?.message || error?.toString?.() || 'Unknown Twilio error';
          console.error('⚠️ Twilio Error:', msg);
        }
      });

      // Incoming call event
      newDevice.on('incoming', (call) => {
        console.log('Incoming call from:', call.parameters.From);
        
        onIncomingCall({
          from: call.parameters.From,
          callSid: call.parameters.CallSid,
          accept: () => acceptCall(call),
          reject: () => rejectCall(call),
        });

        onCallStatusChange('ringing');
        
        // Setup call event handlers
        setupCallHandlers(call);
      });

      console.log('Registering Twilio Device...');
      // Register the device
      await newDevice.register();
      console.log('✓ Device registered successfully!');
      
      deviceRef.current = newDevice;
      setDevice(newDevice);
      console.log('=== Twilio Device initialization complete ===');
      
    } catch (error) {
      console.error('=== Failed to initialize Twilio Device ===');
      console.error('Error type:', typeof error);
      console.error('Error constructor:', error?.constructor?.name);
      console.error('Error object:', error);
      
      // Safely log error properties
      if (error) {
        console.error('Error name:', error.name || 'N/A');
        console.error('Error message:', error.message || 'N/A');
        console.error('Error code:', error.code || 'N/A');
        console.error('Error stack:', error.stack || 'N/A');
        
        // Try to get all enumerable properties
        try {
          const errorProps = {};
          for (let key in error) {
            try {
              errorProps[key] = error[key];
            } catch (e) {
              errorProps[key] = 'Unable to read';
            }
          }
          console.error('Error properties:', errorProps);
        } catch (e) {
          console.error('Could not enumerate error properties');
        }
      }
      
      // Show more specific error message
      let errorMsg = 'Unknown error';
      if (error?.message) {
        errorMsg = error.message;
      } else if (error?.toString && typeof error.toString === 'function') {
        try {
          errorMsg = error.toString();
        } catch (e) {
          errorMsg = 'Error toString() failed';
        }
      }
      
      setInitError(errorMsg);
      console.error('🚨 FAILED TO INITIALIZE TWILIO:', errorMsg);
      console.error('🔍 Please check the detailed error information above');
    } finally {
      initializingRef.current = false;
    }
  }, [handleTokenRefresh, onIncomingCall, onCallStatusChange]);

  useEffect(() => {
    if (token && !deviceRef.current && !initializingRef.current) {
      console.log('Token changed, attempting to initialize device...');
      initializeTwilioDevice(token);
    }

    return () => {
      // Cleanup on unmount
      if (deviceRef.current) {
        console.log('Cleaning up device on unmount');
        deviceRef.current.destroy();
        deviceRef.current = null;
      }
      initializingRef.current = false;
    };
  }, [token, initializeTwilioDevice]);

  /**
   * Setup event handlers for a call
   */
  const setupCallHandlers = (call) => {
    call.on('accept', () => {
      console.log('Call accepted');
      setCurrentCall(call);
      onCallStatusChange('in-progress');
      onIncomingCall(null);
    });

    call.on('disconnect', () => {
      console.log('Call disconnected');
      setCurrentCall(null);
      onCallStatusChange('ended');
      setTimeout(() => onCallStatusChange('idle'), 3000);
    });

    call.on('cancel', () => {
      console.log('Call cancelled');
      setCurrentCall(null);
      onCallStatusChange('idle');
      onIncomingCall(null);
    });

    call.on('reject', () => {
      console.log('Call rejected');
      setCurrentCall(null);
      onCallStatusChange('idle');
      onIncomingCall(null);
    });
  };

  /**
   * Accept an incoming call
   */
  const acceptCall = (call) => {
    console.log('Accepting call...');
    call.accept();
  };

  /**
   * Reject an incoming call
   */
  const rejectCall = (call) => {
    console.log('Rejecting call...');
    call.reject();
  };

  /**
   * Make an outgoing call to Twilio number
   */
  const makeCall = async () => {
    if (!device) {
      alert('Twilio Device not initialized. Requesting token...');
      const newToken = await onRequestToken();
      if (!newToken) return;
      return;
    }

    if (!callNumber) {
      alert('Please enter a phone number to call');
      return;
    }

    try {
      console.log('Making call to:', callNumber);
      const call = await device.connect({
        params: {
          To: callNumber,
        },
      });

      setCurrentCall(call);
      onCallStatusChange('in-progress');
      setupCallHandlers(call);
      
    } catch (error) {
      console.error('Failed to make call:', error);
      console.error('Call error message:', error?.message || 'Unknown');
    }
  };

  /**
   * Hang up current call
   */
  const hangUp = () => {
    if (currentCall) {
      console.log('Hanging up call...');
      currentCall.disconnect();
    }
  };

  /**
   * Initialize Twilio Device by requesting token
   */
  const handleInitialize = async () => {
    console.log('Manual initialization requested...');
    setInitError(null);
    initializingRef.current = false;
    await onRequestToken();
  };

  return (
    <div className="card">
      <h2>📞 Twilio Client</h2>

      {/* Device Status */}
      <div style={{ marginBottom: '1rem' }}>
        <p>
          <strong>Status:</strong>{' '}
          {!device && !isReady && !initError && (
            <span style={{ color: '#f57c00' }}>Not Connected</span>
          )}
          {!device && !isReady && initError && (
            <span style={{ color: '#f44336' }}>❌ Error</span>
          )}
          {device && isReady && (
            <span style={{ color: '#4caf50' }}>✓ Ready</span>
          )}
          {device && !isReady && (
            <span style={{ color: '#ff9800' }}>Connecting...</span>
          )}
        </p>
      </div>

      {/* Error Display */}
      {initError && !device && (
        <div style={{
          backgroundColor: '#ffebee',
          border: '1px solid #f44336',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          color: '#d32f2f'
        }}>
          <strong>⚠️ Initialization Error:</strong>
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem' }}>
            {initError}
          </p>
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem', color: '#666' }}>
            Open browser console (F12) for detailed error information.
          </p>
          <button 
            className="btn btn-secondary" 
            onClick={handleInitialize}
            style={{ marginTop: '0.5rem' }}
          >
            🔄 Retry Connection
          </button>
        </div>
      )}

      {/* Initialize Button */}
      {!device && backendStatus === 'ready' && (
        <div>
          <button className="btn btn-primary" onClick={handleInitialize}>
            🔌 Connect to Twilio
          </button>
          <p style={{ marginTop: '1rem', color: '#666' }}>
            Click to initialize Twilio client
          </p>
        </div>
      )}

      {/* Call Controls */}
      {device && isReady && (
        <div>
          {!currentCall && (
            <div>
              <h3>Make a Test Call</h3>
              <div style={{ marginBottom: '1rem' }}>
                <input
                  type="tel"
                  placeholder="Enter phone number (e.g., +1234567890)"
                  value={callNumber}
                  onChange={(e) => setCallNumber(e.target.value)}
                  style={{
                    padding: '0.75rem',
                    fontSize: '1rem',
                    borderRadius: '8px',
                    border: '2px solid #ddd',
                    width: '100%',
                    maxWidth: '400px',
                  }}
                />
              </div>
              <button 
                className="btn btn-success" 
                onClick={makeCall}
                disabled={!callNumber}
              >
                📞 Call
              </button>
            </div>
          )}

          {currentCall && (
            <div>
              <p style={{ color: '#4caf50', marginBottom: '1rem' }}>
                Call in progress...
              </p>
              <button className="btn btn-danger" onClick={hangUp}>
                ✗ Hang Up
              </button>
            </div>
          )}
        </div>
      )}

      {/* Information */}
      {device && isReady && (
        <div className="info-box" style={{ marginTop: '1rem' }}>
          <p><strong>💡 Tips:</strong></p>
          <p>• Enter your Twilio number to test the AI greeting</p>
          <p>• Make sure your backend is exposed via ngrok</p>
          <p>• Check Django logs to see webhook activity</p>
        </div>
      )}
    </div>
  );
}

export default TwilioClient;
