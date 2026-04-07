# GenCall AI - Start Script
# This script helps you start both backend and frontend servers

Write-Host "================================" -ForegroundColor Cyan
Write-Host "   GenCall AI - Startup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-Not (Test-Path "backend") -or -Not (Test-Path "frontend")) {
    Write-Host "Error: Please run this script from the 'Gencall ai' root directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Write-Host "What would you like to do?" -ForegroundColor Green
Write-Host ""
Write-Host "1. Start Backend (Django)" -ForegroundColor White
Write-Host "2. Start Frontend (React)" -ForegroundColor White
Write-Host "3. Run Database Migrations" -ForegroundColor White
Write-Host "4. Create Admin User" -ForegroundColor White
Write-Host "5. Check Backend Status" -ForegroundColor White
Write-Host "6. View Setup Instructions" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`nStarting Django Backend..." -ForegroundColor Green
        Write-Host "Server will run at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow
        Set-Location backend
        & .\venv\Scripts\python.exe manage.py runserver
    }
    "2" {
        Write-Host "`nStarting React Frontend..." -ForegroundColor Green
        Write-Host "App will open at: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow
        Set-Location frontend
        npm start
    }
    "3" {
        Write-Host "`nRunning Database Migrations..." -ForegroundColor Green
        Set-Location backend
        & .\venv\Scripts\python.exe manage.py makemigrations
        & .\venv\Scripts\python.exe manage.py migrate
        Write-Host "`nMigrations completed!" -ForegroundColor Green
    }
    "4" {
        Write-Host "`nCreating Admin User..." -ForegroundColor Green
        Set-Location backend
        & .\venv\Scripts\python.exe manage.py createsuperuser
    }
    "5" {
        Write-Host "`nChecking Backend Status..." -ForegroundColor Green
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/test/" -UseBasicParsing
            $data = $response.Content | ConvertFrom-Json
            Write-Host "`n✓ Backend is running!" -ForegroundColor Green
            Write-Host "Status: $($data.status)" -ForegroundColor Cyan
            Write-Host "Twilio Configured: $($data.twilio_configured)" -ForegroundColor Cyan
        } catch {
            Write-Host "`n✗ Backend is not running" -ForegroundColor Red
            Write-Host "Please start the backend with option 1" -ForegroundColor Yellow
        }
    }
    "6" {
        Write-Host "`n📖 Opening Quick Start Guide..." -ForegroundColor Green
        Write-Host ""
        Write-Host "=== QUICK SETUP ===" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "1. Configure Twilio:" -ForegroundColor White
        Write-Host "   - Edit backend\.env with your Twilio credentials" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Start Backend (Terminal 1):" -ForegroundColor White
        Write-Host "   cd backend" -ForegroundColor Gray
        Write-Host "   .\venv\Scripts\python.exe manage.py runserver" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Start ngrok (Terminal 2):" -ForegroundColor White
        Write-Host "   ngrok http 8000" -ForegroundColor Gray
        Write-Host "   Copy the HTTPS URL" -ForegroundColor Gray
        Write-Host ""
        Write-Host "4. Configure Twilio Webhook:" -ForegroundColor White
        Write-Host "   - Go to Twilio Console > Phone Numbers" -ForegroundColor Gray
        Write-Host "   - Set webhook to: https://your-ngrok-url/api/incoming_call/" -ForegroundColor Gray
        Write-Host ""
        Write-Host "5. Start Frontend (Terminal 3):" -ForegroundColor White
        Write-Host "   cd frontend" -ForegroundColor Gray
        Write-Host "   npm start" -ForegroundColor Gray
        Write-Host ""
        Write-Host "📄 See QUICKSTART.md for detailed instructions" -ForegroundColor Cyan
    }
    default {
        Write-Host "`nInvalid choice. Please run the script again." -ForegroundColor Red
    }
}

Write-Host ""
