# GenCall AI

**GenCall AI** is a full-stack AI-powered call management system built with Django (backend) and React (frontend), integrated with Twilio for voice capabilities.

## 🚀 Features

### Backend (Django)
- ✅ Twilio webhook integration for incoming calls
- ✅ Automatic call answering with AI text-to-speech
- ✅ Call logging and tracking
- ✅ RESTful API for frontend integration
- ✅ Admin panel for call management

### Frontend (React)
- ✅ Real-time call status monitoring
- ✅ Incoming call notifications
- ✅ Make outgoing test calls
- ✅ Call history and logs
- ✅ Responsive, modern UI

### Twilio Integration
- ✅ Voice SDK for browser-based calling
- ✅ Webhook handling for call events
- ✅ Text-to-speech AI greeting
- ✅ Call status tracking

## 📋 Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 14+** (for frontend)
- **Twilio Account** ([Sign up for free](https://www.twilio.com/try-twilio))
- **ngrok** ([Download](https://ngrok.com/download)) - for exposing local backend to Twilio

## 🛠️ Installation & Setup

### 1. Clone or Download the Project

Your project structure should look like:
```
Gencall ai/
├── backend/       # Django backend
└── frontend/      # React frontend
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Twilio credentials:
```env
DJANGO_SECRET_KEY=your-secret-key-here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
TWIML_APP_SID=your_twiml_app_sid
```

**Where to find Twilio credentials:**
- Go to [Twilio Console](https://console.twilio.com)
- **Account SID** and **Auth Token**: Dashboard page
- **Phone Number**: Phone Numbers → Manage → Active Numbers
- **TwiML App SID**: Voice → TwiML Apps → Create new (if needed)

#### Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

#### Start Django Server

```bash
python manage.py runserver
```

Backend will be running at: `http://127.0.0.1:8000/`

### 3. Expose Backend with ngrok

Twilio needs to access your local server via the internet.

```bash
# In a new terminal window
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abcd1234.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abcd1234.ngrok.io`)

### 4. Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to: **Phone Numbers → Manage → Active Numbers**
3. Click on your phone number
4. Under **Voice Configuration**:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-ngrok-url.ngrok.io/api/incoming_call/`
   - **HTTP Method**: POST
5. Under **Call Status Changes** (optional):
   - **URL**: `https://your-ngrok-url.ngrok.io/api/call_status/`
   - **HTTP Method**: POST
6. Click **Save**

### 5. Frontend Setup

#### Install Node.js Dependencies

```bash
cd frontend

# Install dependencies
npm install
```

#### Configure Environment (Optional)

Copy `.env.example` to `.env` if you want to customize:
```bash
cp .env.example .env
```

Default configuration works out of the box.

#### Start React Development Server

```bash
npm start
```

Frontend will open at: `http://localhost:3000/`

## 🎯 Testing the System

### Test 1: Incoming Call with AI Greeting

1. Ensure backend is running (`python manage.py runserver`)
2. Ensure ngrok is exposing backend
3. Call your Twilio phone number from any phone
4. You should hear: **"Hello! This is GenCall AI speaking..."**
5. Check Django console for webhook logs
6. Check frontend Call Logs for the call record

### Test 2: Frontend Dashboard

1. Open frontend at `http://localhost:3000/`
2. Check that "Backend: ✓ Ready" is showing
3. Click **"Connect to Twilio"** button
4. Wait for "Status: ✓ Ready" in Twilio Client section

### Test 3: Outgoing Call (Optional)

1. After connecting to Twilio in frontend
2. Enter your Twilio number in the input field
3. Click **"Call"** button
4. You should hear the AI greeting in your browser

### Test 4: View Call Logs

1. After making/receiving calls
2. Check the "Call Logs" section in frontend
3. Logs auto-refresh every 10 seconds
4. Click "Refresh" to manually update

## 📁 Project Structure

```
Gencall ai/
├── backend/
│   ├── gencall_backend/          # Django project settings
│   │   ├── settings.py           # Main configuration
│   │   ├── urls.py               # URL routing
│   │   └── ...
│   ├── calls/                    # Calls app
│   │   ├── models.py             # CallLog model
│   │   ├── views.py              # API views and webhooks
│   │   ├── urls.py               # App URLs
│   │   └── admin.py              # Admin configuration
│   ├── manage.py                 # Django CLI
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment template
│   └── README.md                 # Backend docs
│
└── frontend/
    ├── public/
    │   └── index.html            # HTML template
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.js      # Main dashboard
    │   │   ├── TwilioClient.js   # Twilio integration
    │   │   └── CallLogs.js       # Call history
    │   ├── App.js                # Root component
    │   ├── App.css               # Styles
    │   └── index.js              # Entry point
    ├── package.json              # Node dependencies
    ├── .env.example              # Environment template
    └── README.md                 # Frontend docs
```

## 🔧 API Endpoints

### Backend API

- `POST /api/incoming_call/` - Twilio webhook for incoming calls
- `POST /api/call_status/` - Twilio webhook for call status updates
- `GET /api/call_logs/` - Get recent call logs (JSON)
- `POST /api/generate_token/` - Generate Twilio access token
- `GET /api/test/` - Test backend status

### Testing Endpoints

```bash
# Test backend
curl http://localhost:8000/api/test/

# Get call logs
curl http://localhost:8000/api/call_logs/
```

## 🎨 Screenshots

### Dashboard
![Dashboard showing call status and controls]

### Call Logs
![Call history with timestamps and status]

### Incoming Call Alert
![Alert notification for incoming calls]

## 🐛 Troubleshooting

### Backend Issues

**"ModuleNotFoundError: No module named 'django'"**
- Solution: Activate virtual environment and run `pip install -r requirements.txt`

**"CSRF verification failed"**
- Solution: Ensure `@csrf_exempt` is on webhook views
- Check Twilio webhook URL is using HTTPS (ngrok)

**"Twilio webhook returns 404"**
- Solution: Verify ngrok URL is correct
- Ensure URL includes `/api/incoming_call/`
- Check Django server is running

### Frontend Issues

**"Backend is offline"**
- Solution: Start Django server: `python manage.py runserver`
- Check port 8000 is not blocked

**"Cannot connect to Twilio"**
- Solution: Check Twilio credentials in backend `.env`
- Click "Connect to Twilio" button
- Check browser console for errors

**"No audio during call"**
- Solution: Grant microphone permissions in browser
- Use Chrome or Firefox (better WebRTC support)
- Check speaker/headphone connection

### Twilio Issues

**"Call connects but no audio"**
- Solution: Check TwiML response is valid XML
- Verify Twilio account is active and funded
- Check Twilio Console logs

**"Webhook timeout"**
- Solution: Ensure ngrok is running
- Check backend responds within 15 seconds
- Verify no firewall blocks

## 📚 Learn More

### Twilio Documentation
- [Twilio Voice API](https://www.twilio.com/docs/voice)
- [TwiML for Voice](https://www.twilio.com/docs/voice/twiml)
- [Twilio Voice SDK](https://www.twilio.com/docs/voice/sdks/javascript)

### Django Resources
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)

### React Resources
- [React Documentation](https://react.dev/)
- [Create React App](https://create-react-app.dev/)

## 🚀 Next Steps

- [ ] Add speech recognition for interactive IVR
- [ ] Implement call recording
- [ ] Add SMS notifications
- [ ] Create analytics dashboard
- [ ] Add WebSocket for real-time updates
- [ ] Implement multi-party conferencing
- [ ] Add AI-powered call routing
- [ ] Create mobile app version

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 💬 Support

For issues or questions:
- Check individual README files in backend/ and frontend/
- Review Twilio Console for call/error logs
- Check Django console output
- Open browser DevTools console

## ⚙️ Configuration Summary

### Backend (.env)
```env
DJANGO_SECRET_KEY=your-secret-key
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWIML_APP_SID=APxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Twilio Number Configuration
- **Voice Webhook**: `https://your-ngrok-url.ngrok.io/api/incoming_call/`
- **Status Callback**: `https://your-ngrok-url.ngrok.io/api/call_status/`

### Ports
- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:3000`
- **ngrok**: Varies (shown in ngrok output)

---

**Built with ❤️ using Django, React, and Twilio**
