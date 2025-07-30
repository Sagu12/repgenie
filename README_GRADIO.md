# RepGenie - Gradio Web Application

A comprehensive AI-powered fitness trainer built with **Python Gradio** - fully responsive and feature-complete!

## 🌟 Features

### 🔐 **User Authentication**
- User registration and login
- Secure password hashing
- Session management
- SQLite database for user storage

### 💬 **AI Chat Interface**
- **💪 Workout Coach**: Personalized fitness and meal planning
- **🌐 News Search**: Latest fitness and nutrition news
- **📺 Video Search**: YouTube workout and fitness videos
- Real-time agent switching with visual feedback

### 📱 **Multi-Modal Input**
- **Text Chat**: Type questions and get AI responses
- **📸 Image Upload**: Body composition and meal analysis
- **🎤 Audio Recording**: Voice messages with transcription

### 🎨 **Modern UI/UX**
- Responsive design (mobile-friendly)
- Beautiful gradient themes
- Chat bubble interface
- Real-time status indicators
- Smooth animations and transitions

## 🚀 Quick Start

### Method 1: One-Click Launch
```bash
python start_gradio.py
```

### Method 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements_gradio.txt

# Start FastAPI backend (Terminal 1)
python fastapi_fitness_trainer.py

# Start Gradio frontend (Terminal 2)  
python gradio_app.py
```

## 🔧 Configuration

### 1. Create `.env` file:
```env
openai_api_key=your_openai_api_key_here
```

### 2. Access the Application:
- **Gradio UI**: `http://localhost:7860`
- **FastAPI Backend**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`

## 📖 How to Use

### 1. **Sign Up/Login**
- Create a new account or login with existing credentials
- Your email becomes your unique thread ID for conversations

### 2. **Choose Your AI Agent**
- **💪 Workout Coach**: Default mode for fitness planning and coaching
- **🌐 News Search**: Get latest fitness and nutrition news
- **📺 Video Search**: Find YouTube workout videos

### 3. **Interact with RepGenie**
- **Text**: Type your fitness questions
- **Images**: Upload body photos for analysis or meal photos for nutrition advice
- **Audio**: Record voice messages for hands-free interaction

### 4. **Get Personalized Responses**
- AI maintains conversation context
- Responses tailored to your selected agent
- Chat history preserved throughout session

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gradio UI     │────│   FastAPI        │────│   AI Models     │
│   (Frontend)    │    │   (Backend)      │    │   (OpenAI)      │
│   Port: 7860    │    │   Port: 8000     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
   ┌─────────┐              ┌──────────┐            ┌──────────┐
   │ SQLite  │              │ SQLite   │            │ OpenAI   │
   │ Users   │              │ Convos   │            │ API      │
   └─────────┘              └──────────┘            └──────────┘
```

## 🔄 Data Flow

1. **User Authentication**: Gradio ↔ SQLite (users)
2. **Chat Messages**: Gradio → FastAPI → OpenAI → SQLite (conversations)
3. **File Uploads**: Gradio → FastAPI → OpenAI (Vision/Whisper)
4. **Agent Selection**: Gradio updates → FastAPI agent routing

## 📱 Responsive Design

- **Desktop**: Full layout with side-by-side components
- **Tablet**: Stacked layout with touch-friendly controls
- **Mobile**: Single-column layout, optimized for small screens

## 🎨 UI Components

### **Chat Interface**
- Bubble-style messages with timestamps
- Agent indicators with emojis
- Smooth scrolling and auto-focus
- Loading states and error handling

### **File Uploads**
- Drag-and-drop image upload
- Audio recording with visual feedback
- Progress indicators
- File type validation

### **Agent Selection**
- Visual button states (active/inactive)
- Real-time agent switching
- Status indicators
- Smooth transitions

## 🔧 Customization

### **Styling**
- Modify `custom_css` in `gradio_app.py`
- Update color schemes and gradients
- Adjust responsive breakpoints

### **Functionality**
- Add new AI agents in `switch_agent()` function
- Customize message formatting in `format_message()`
- Extend file upload types

## 🚀 Deployment

### **Local Development**
```bash
python start_gradio.py
```

### **Production Deployment**
```bash
# Option 1: Gradio sharing
gradio_app.py --share

# Option 2: Custom server
uvicorn gradio_app:app --host 0.0.0.0 --port 7860
```

## 📊 Comparison: Gradio vs React

| Feature | Gradio Version | React Version |
|---------|---------------|---------------|
| **Setup** | ✅ 1 command | ❌ Complex setup |
| **Deployment** | ✅ Easy sharing | ❌ Build process |
| **Responsive** | ✅ Built-in | ✅ Custom CSS |
| **Features** | ✅ Complete | ✅ Complete |
| **Performance** | ✅ Fast | ✅ Fast |
| **Customization** | ⚠️ Limited | ✅ Full control |

## 🐛 Troubleshooting

### **Common Issues**

1. **"Connection Error"**
   - Ensure FastAPI backend is running on port 8000
   - Check `.env` file has valid OpenAI API key

2. **"User Database Error"**
   - Check file permissions for SQLite database
   - Ensure `gradio_users.db` can be created

3. **"File Upload Failed"**
   - Check file size limits
   - Ensure FastAPI backend is accessible

### **Debug Mode**
```bash
python gradio_app.py --debug
```

## 🎉 Success!

Your RepGenie Gradio application is now ready! This provides the same functionality as the React version but with:

- ✅ **Easier deployment**
- ✅ **Better mobile experience** 
- ✅ **Simpler maintenance**
- ✅ **Built-in sharing capabilities**

Enjoy your AI fitness trainer! 🏋️‍♀️💪 