# GenCall AI Frontend

React frontend for GenCall AI - AI-powered call management system with Twilio integration.

## Features

- **Real-time Call Status**: Monitor call status (idle, ringing, in progress, ended)
- **Incoming Call Notifications**: Visual alerts for incoming calls
- **Outgoing Calls**: Make test calls to Twilio numbers
- **Call Logs**: View recent call history from backend
- **Twilio Client Integration**: Full Twilio Voice SDK integration
- **Responsive Design**: Works on desktop and mobile devices

## Setup Instructions

### 1. Install Node.js Dependencies

Make sure you have Node.js installed (version 14 or higher recommended).

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### 2. Configure Environment Variables

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

The default configuration points to `http://localhost:8000` for the backend.

### 3. Start the Development Server

```bash
npm start
```

The app will open at `http://localhost:3000/`

### 4. Connect to Backend

1. Make sure the Django backend is running at `http://localhost:8000`
2. The frontend will automatically check backend status
3. Click "Connect to Twilio" button to initialize the Twilio client

## How to Use

### Making Test Calls

1. Click "Connect to Twilio" button in the Twilio Client section
2. Enter a phone number (including country code, e.g., +1234567890)
3. Click "Call" button
4. To test the AI greeting, call your Twilio number

### Viewing Call Logs

- Call logs automatically refresh every 10 seconds
- Click "Refresh" button to manually update logs
- Logs show:
  - Caller/Called number
  - Call direction (incoming/outgoing)
  - Timestamp
  - Call status
  - Duration (when available)

### Monitoring Call Status

The dashboard shows real-time call status:
- 📱 **Idle**: No active calls
- 📞 **Ringing**: Incoming call
- 🔊 **In Progress**: Active call
- ✓ **Ended**: Call completed

## Project Structure

```
frontend/
├── public/
│   ├── index.html         # HTML template
│   └── manifest.json      # PWA manifest
├── src/
│   ├── components/        # React components
│   │   ├── Dashboard.js   # Main dashboard component
│   │   ├── TwilioClient.js # Twilio client integration
│   │   └── CallLogs.js    # Call logs display
│   ├── App.js            # Root component
│   ├── App.css           # Main styles
│   ├── index.js          # Entry point
│   └── index.css         # Base styles
├── package.json          # Dependencies and scripts
└── .env                  # Environment variables
```

## Components

### App.js
- Root component that manages application state
- Handles backend connectivity
- Manages Twilio token generation
- Coordinates between Dashboard, TwilioClient, and CallLogs

### Dashboard.js
- Displays current call status
- Shows incoming call alerts with accept/reject buttons
- Provides setup instructions and status information

### TwilioClient.js
- Integrates Twilio Voice SDK
- Handles incoming and outgoing calls
- Manages call lifecycle (connect, disconnect, etc.)
- Provides call controls (call, hang up)

### CallLogs.js
- Fetches and displays call history
- Formats phone numbers and timestamps
- Shows call status badges
- Auto-refreshes every 10 seconds

## Available Scripts

### `npm start`
Runs the app in development mode at [http://localhost:3000](http://localhost:3000)

### `npm build`
Builds the app for production to the `build` folder

### `npm test`
Launches the test runner

## Twilio Integration

The frontend uses the Twilio Voice SDK to:
- Connect to Twilio services
- Make outgoing calls
- Receive incoming calls
- Handle call events (connect, disconnect, etc.)

### Token Generation

The frontend requests Twilio access tokens from the backend via:
```
POST http://localhost:8000/api/generate_token/
```

The token allows the browser to connect to Twilio services securely.

## Troubleshooting

### "Backend is offline" Error
- Ensure Django backend is running: `python manage.py runserver`
- Check that backend is running on port 8000
- Verify no firewall is blocking port 8000

### "Twilio is not configured" Warning
- Backend needs Twilio credentials in `.env` file
- See backend README for Twilio setup instructions

### Can't Connect to Twilio
- Click "Connect to Twilio" button
- Check browser console for error messages
- Verify backend is generating valid tokens
- Ensure Twilio credentials are correct in backend

### No Call Logs Showing
- Make a test call first
- Check backend database has call records
- Click "Refresh" button manually
- Verify backend API endpoint is accessible

### Audio Issues During Calls
- Grant microphone permissions in browser
- Check browser compatibility (Chrome/Firefox recommended)
- Ensure speakers/headphones are connected
- Test with different browsers

## Browser Compatibility

- **Chrome/Edge**: Full support ✓
- **Firefox**: Full support ✓
- **Safari**: Partial support (may have WebRTC limitations)
- **Mobile Browsers**: Support varies

## Development Tips

### Hot Reload
The development server supports hot reload. Changes to React components will automatically refresh the browser.

### Debugging
- Open browser DevTools (F12)
- Check Console tab for errors
- Network tab shows API requests
- Application tab shows local storage

### API Calls
All API calls to backend are proxied through `http://localhost:8000` as configured in `package.json`.

## Production Deployment

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

### Environment Variables for Production

Update `.env` file with production backend URL:
```
REACT_APP_API_URL=https://your-production-backend.com
```

### Hosting Options

- **Netlify**: Drag & drop the `build` folder
- **Vercel**: Connect GitHub repo for auto-deployment
- **AWS S3 + CloudFront**: Static website hosting
- **Firebase Hosting**: `firebase deploy`

## Security Notes

- Never commit `.env` file to version control
- Tokens expire after a set time (configurable in backend)
- Always use HTTPS in production
- Validate all user inputs

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Call recording playback
- [ ] Advanced call analytics
- [ ] Multi-party conferencing
- [ ] Screen sharing during calls
- [ ] Chat integration
- [ ] Contact management
- [ ] Call scheduling

## Support

For issues or questions:
1. Check backend logs: Django console output
2. Check frontend console: Browser DevTools
3. Review Twilio Console for call logs
4. Verify ngrok is exposing backend correctly

## License

MIT License - See LICENSE file for details
