# RepGenie - AI Fitness Trainer

A modern React + FastAPI application that provides personalized fitness guidance using AI agents with secure user authentication.

## 🚀 Features

- **Secure Authentication**: Email/password signup and login with SQLite database storage
- **Multi-Agent AI System**: Workout planning, web search for fitness news, and YouTube video recommendations
- **Voice & Image Support**: Upload images for analysis or record voice messages
- **Real-time Chat**: Interactive conversation with your AI fitness trainer
- **Conversation History**: Persistent chat history per user
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **CAPTCHA Protection**: Prevents automated registration/login attempts

## 🛠️ Setup Instructions

### Prerequisites

- Node.js (v16 or later)
- Python 3.8+
- pip (Python package manager)

### Backend Setup (FastAPI)

1. **Install Python dependencies:**
   ```bash
   pip install fastapi uvicorn python-dotenv openai langchain langchain-openai langchain-community gnews requests
   ```

2. **Create a `.env` file** in the project root with your OpenAI API key:
   ```
   openai_api_key=your_openai_api_key_here
   ```

3. **Start the FastAPI backend:**
   ```bash
   python fastapi_fitness_trainer.py
   ```
   
   The backend will run on `http://localhost:8000` and automatically create the SQLite database

### Frontend Setup (React)

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   The frontend will run on `http://localhost:3000`

### Quick Start (Both Frontend & Backend)

Run both servers simultaneously:
```bash
npm run start:full
```

### Test the Authentication System

Run the test script to verify everything is working:
```bash
python test_auth.py
```

## 🎯 How to Use

### Authentication
1. **Sign Up**: Create a new account with email, password, and complete the CAPTCHA
2. **Login**: Sign in with your registered email and password

### Chat Features
1. **Chat**: Ask questions about workouts, nutrition, or fitness goals
2. **Switch Agents**: Use the settings button to toggle between:
   - 💪 **Workout**: Personalized fitness and meal planning
   - 🌐 **News**: Latest fitness and nutrition news
   - 📺 **YouTube**: Fitness video recommendations
   - 🚀 **All Agents**: Combined responses from all agents
3. **Upload Images**: Share photos of meals or physique for AI analysis
4. **Voice Messages**: Record voice messages for hands-free interaction

## 🔧 Configuration

### Environment Variables

- `VITE_API_URL`: Backend API URL (defaults to `http://localhost:8000`)

### Backend Configuration

The FastAPI backend requires:
- OpenAI API key in `.env` file
- SQLite database (automatically created as `conversations.db`)

## 📡 API Endpoints

### Authentication Endpoints
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login

### Chat Endpoints
- `POST /chat/text` - Send text messages
- `POST /chat/image_upload` - Upload and analyze images  
- `POST /chat/audio` - Upload and process audio

### Utility Endpoints
- `POST /generate_thread_id` - Generate user thread ID
- `GET /conversation_history/{thread_id}` - Get chat history
- `DELETE /clear_memory/{thread_id}` - Clear user memory
- `GET /health` - Health check

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Conversations Table
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_type TEXT,
    used_agent BOOLEAN DEFAULT FALSE,
    human_message TEXT,
    ai_message TEXT,
    input_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔒 Security Features

- **Password Hashing**: Passwords are hashed with SHA-256 and unique salts
- **Input Validation**: Client and server-side validation for all inputs
- **CAPTCHA Protection**: Prevents automated attacks
- **SQL Injection Protection**: Parameterized queries prevent SQL injection
- **Error Handling**: Secure error messages don't expose sensitive information

## 🏗️ Architecture

### Frontend (React + TypeScript)
- **Authentication**: Secure login/signup with form validation
- **Components**: Modular React components with TypeScript
- **State Management**: React hooks for local state
- **Styling**: Tailwind CSS for modern UI
- **API Layer**: Centralized API service with error handling

### Backend (FastAPI + Python)
- **Authentication**: Secure user registration and login
- **AI Agents**: LangChain-powered agents for different functionalities
- **Database**: SQLite for users and conversation storage
- **Memory**: User-specific conversation memory
- **File Processing**: Image and audio analysis with OpenAI

## 🐛 Troubleshooting

### Common Issues

1. **"Error sending message"**: Ensure FastAPI backend is running on port 8000
2. **Authentication errors**: Check database permissions and table creation
3. **CORS errors**: Backend includes CORS middleware for all origins
4. **OpenAI errors**: Check your API key in the `.env` file
5. **Audio not working**: Check browser microphone permissions
6. **Database errors**: Ensure SQLite permissions and disk space

### Development Tips

- Check browser console for detailed error logs
- Monitor FastAPI logs for backend issues
- Use the health check endpoint: `http://localhost:8000/health`
- Run the test script: `python test_auth.py`

## 📝 Notes

- **Authentication**: Users must create accounts with email/password
- **Password Requirements**: Minimum 8 characters with uppercase, lowercase, and numbers
- **Database**: SQLite database stores user credentials and conversation history
- **Thread IDs**: User emails serve as unique thread identifiers for conversations
- **Image and audio processing**: Requires OpenAI API credits
- **CAPTCHA**: Required for both signup and login for security

## 🚀 Deployment

For production deployment:
1. Build the frontend: `npm run build`
2. Configure environment variables for production
3. Deploy FastAPI with a proper ASGI server like Gunicorn
4. Set up proper database for production use (consider PostgreSQL)
5. Configure HTTPS and proper CORS origins
6. Set up proper backup for SQLite database

## 🧪 Testing

Run the authentication test suite:
```bash
python test_auth.py
```

This will test:
- Database table creation
- Backend health
- User registration
- User login

All tests should pass before deploying to production. 

## 🔧 Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key

### Installation
1. **Clone the repository**
2. **Install backend dependencies:**
   ```bash
   pip install -r requirements_gradio.txt
   ```
3. **Install frontend dependencies:**
   ```bash
   cd project
   npm install
   ```

### 📱 Mobile Access via ngrok

For testing on mobile devices, follow these steps:

1. **Install ngrok**: https://ngrok.com/
2. **Start your backend** (keep running):
   ```bash
   python fastapi_fitness_trainer.py
   ```
3. **In a new terminal, expose the backend**:
   ```bash
   ngrok http 8000
   ```
4. **Copy the ngrok HTTPS URL** (e.g., `https://abc123.ngrok.io`)
5. **Update frontend environment** - create a `.env` file in the `project` folder:
   ```
   VITE_API_URL=https://your-ngrok-url.ngrok.io
   ```
6. **Start the frontend**:
   ```bash
   npm run dev
   ```
7. **Expose the frontend** (new terminal):
   ```bash
   ngrok http 3000
   ```
8. **Access on mobile**: Use the frontend ngrok HTTPS URL

### 🐛 Mobile Debugging
- Open browser console on mobile (or use desktop dev tools)
- Look for `📱 Mobile Debug` logs
- Check network connectivity
- Ensure both URLs use HTTPS (required for mobile)

### Run Instructions 