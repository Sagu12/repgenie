# RepGenie Development Startup Script for Windows (PowerShell)

Write-Host "🚀 Starting RepGenie Development Environment..." -ForegroundColor Green
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host "Please create a .env file with your OpenAI API key:" -ForegroundColor Yellow
    Write-Host "openai_api_key=your_openai_api_key_here" -ForegroundColor Yellow
    Write-Host ""
}

# Start FastAPI backend in background
Write-Host "🐍 Starting FastAPI backend on http://localhost:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-Command", "python fastapi_fitness_trainer.py" -WindowStyle Minimized

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Check if backend is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Backend is running!" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend failed to start. Check for errors above." -ForegroundColor Red
    Write-Host "Make sure all Python dependencies are installed:" -ForegroundColor Yellow
    Write-Host "pip install fastapi uvicorn python-dotenv openai langchain langchain-openai langchain-community gnews" -ForegroundColor Yellow
    exit 1
}

# Start React frontend
Write-Host "⚛️  Starting React frontend on http://localhost:3000..." -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Usage Instructions:" -ForegroundColor Green
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Enter your email to start your fitness journey" -ForegroundColor White
Write-Host "3. Chat with RepGenie using text, voice, or images!" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop both servers, use Ctrl+C" -ForegroundColor Yellow
Write-Host ""

npm run dev 