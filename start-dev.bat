@echo off
echo Starting RepGenie Development Environment...
echo.

echo 🔧 Checking Python dependencies...
pip install fastapi uvicorn python-dotenv openai langchain langchain-openai langchain-community gnews

echo.
echo 🚀 Starting FastAPI Backend on http://localhost:8000
start "FastAPI Backend" cmd /k "python fastapi_fitness_trainer.py"

echo.
echo 🚀 Starting React Frontend on http://localhost:5173
start "React Frontend" cmd /k "npm run dev"

echo.
echo ✅ Both servers are starting...
echo 📱 Frontend: http://localhost:5173
echo 🔗 Backend API: http://localhost:8000
echo 📖 API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause > nul 