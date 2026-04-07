# GenCall AI Backend

Django backend for handling Twilio calls with AI capabilities.

## Features

- **Incoming Call Handler**: Automatically answers calls and responds with text-to-speech
- **Call Logging**: Stores all call information in database
- **RESTful API**: Provides endpoints for frontend integration
- **Twilio Integration**: Full Twilio SDK integration for voice operations

## Setup Instructions

### 1. Install Python Dependencies

First, create a virtual environment and install dependencies:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the `.env.example` file to `.env` and fill in your Twilio credentials:

```bash
cp .env.example .env
```

Edit `.env` file with your Twilio credentials:
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number (format: +1234567890)
- `TWIML_APP_SID`: Your TwiML App SID (create in Twilio Console)

Add speech-to-text settings:
- `STT_PROVIDER`: `groq` or `openai` (default: `groq`)
- `GROQ_API_KEY`: Your Groq API key
- `GROQ_STT_MODEL`: Transcription model (default: `whisper-large-v3-turbo`)
- `OPENAI_API_KEY`: Optional if using OpenAI provider
- `OPENAI_STT_MODEL`: Optional if using OpenAI provider (default: `whisper-1`)

### 3. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run the Development Server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

### 6. Expose Server with ngrok (Required for Twilio)

Twilio needs to access your local server via the internet. Use ngrok:

```bash
# Install ngrok from https://ngrok.com/download
# Then run:
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abcd1234.ngrok.io`)

### 7. Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Click on your phone number
4. Under "Voice & Fax", set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://your-ngrok-url.ngrok.io/api/incoming_call/`
   - **HTTP Method**: POST
5. Under "Call Status Changes":
   - **URL**: `https://your-ngrok-url.ngrok.io/api/call_status/`
   - **HTTP Method**: POST
6. Click "Save"

## API Endpoints

- `POST /api/incoming_call/` - Twilio webhook for incoming calls
- `POST /api/call_status/` - Twilio webhook for call status updates
- `GET /api/call_logs/` - Get recent call logs
- `POST /api/generate_token/` - Generate Twilio access token for frontend
- `POST /api/speech_to_text/` - Transcribe uploaded audio (supports Urdu via `language=ur`)
- `GET /api/test/` - Test endpoint to verify API is running

### Speech-to-Text Example

```bash
curl -X POST http://127.0.0.1:8000/api/speech_to_text/ \
   -F "file=@sample.wav" \
   -F "language=ur"
```

## Testing

1. Call your Twilio phone number
2. You should hear: "Hello! This is GenCall AI speaking..."
3. Check call logs in admin panel: `http://127.0.0.1:8000/admin/`

## Project Structure

```
backend/
├── gencall_backend/       # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py            # URL routing
│   └── wsgi.py           # WSGI configuration
├── calls/                 # Calls app
│   ├── models.py         # CallLog model
│   ├── views.py          # View functions and API endpoints
│   ├── urls.py           # App URL configuration
│   └── admin.py          # Admin interface configuration
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables (create from .env.example)
```

## Troubleshooting

### Twilio Can't Reach Server
- Ensure ngrok is running
- Check that ngrok URL is correctly set in Twilio Console
- Verify the URL includes `/api/incoming_call/` at the end

### No Audio on Call
- Check Twilio account status
- Verify TwiML response is being generated correctly
- Check server logs for errors

### CSRF Token Errors
- Twilio webhooks are CSRF-exempt
- Ensure `@csrf_exempt` decorator is present on webhook views

## Development Notes

- The server uses SQLite database by default
- CORS is enabled for `http://localhost:3000` (React frontend)
- All hosts are allowed in development (change for production)
- Call logs are stored with timestamps for analysis

## Next Steps

- Implement call recording
- Add speech recognition for interactive responses
- Create more sophisticated AI responses
- Add WebSocket support for real-time updates
