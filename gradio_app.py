import gradio as gr
import requests
import json
import os
from datetime import datetime
import base64
import hashlib
import sqlite3
from typing import Optional, Dict, Any, Tuple
import tempfile
import io

# Configuration
API_BASE_URL = 'http://localhost:8000'
DB_FILE = 'gradio_users.db'

# Initialize user database
def init_user_db():
    """Initialize user database for authentication"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256((password + "repgenie_salt").encode()).hexdigest()

def register_user(email: str, password: str) -> Tuple[bool, str]:
    """Register a new user"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "Email already exists"
        
        # Insert new user
        password_hash = hash_password(password)
        cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", 
                      (email, password_hash))
        conn.commit()
        conn.close()
        return True, "Registration successful"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def login_user(email: str, password: str) -> Tuple[bool, str]:
    """Login user"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, "User not found"
        
        if result[0] == hash_password(password):
            return True, "Login successful"
        else:
            return False, "Invalid password"
    except Exception as e:
        return False, f"Login failed: {str(e)}"

# API Integration Functions
def send_text_message(thread_id: str, query: str, selected_agent: str = "workout") -> Dict:
    """Send text message to FastAPI backend"""
    try:
        response = requests.post(f"{API_BASE_URL}/chat/text", 
                               json={
                                   "thread_id": thread_id,
                                   "query": query,
                                   "selected_agent": selected_agent
                               }, 
                               timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"response": f"Error: {response.status_code}", "agent_used": "error"}
    except Exception as e:
        return {"response": f"Connection error: {str(e)}", "agent_used": "error"}

def upload_image_to_api(thread_id: str, image_path: str) -> Dict:
    """Upload image to FastAPI backend"""
    try:
        with open(image_path, 'rb') as f:
            files = {'image_file': f}
            data = {'thread_id': thread_id}
            response = requests.post(f"{API_BASE_URL}/chat/image_upload", 
                                   files=files, data=data, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"response": f"Error: {response.status_code}", "agent_used": "error"}
    except Exception as e:
        return {"response": f"Connection error: {str(e)}", "agent_used": "error"}

def upload_audio_to_api(thread_id: str, audio_path: str, selected_agent: str = "workout") -> Dict:
    """Upload audio to FastAPI backend"""
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio_file': f}
            data = {'thread_id': thread_id, 'selected_agent': selected_agent}
            response = requests.post(f"{API_BASE_URL}/chat/audio", 
                                   files=files, data=data, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            return {"response": f"Error: {response.status_code}", "agent_used": "error"}
    except Exception as e:
        return {"response": f"Connection error: {str(e)}", "agent_used": "error"}

# Chat Interface Functions
def get_agent_emoji(agent: str) -> str:
    """Get emoji for agent type"""
    agent_emojis = {
        "workout": "💪",
        "news": "🌐", 
        "youtube": "📺",
        "image_analysis": "📸",
        "error": "❌"
    }
    return agent_emojis.get(agent, "🤖")

def format_message(sender: str, message: str, agent: str = "", timestamp: str = "") -> str:
    """Format message for chat display"""
    if not timestamp:
        timestamp = datetime.now().strftime("%H:%M")
    
    if sender == "user":
        return f"""
<div style='text-align: right; margin: 10px 0;'>
    <div style='display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 12px 16px; border-radius: 18px 18px 4px 18px; 
                max-width: 70%; word-wrap: break-word; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
        {message}
        <div style='font-size: 11px; opacity: 0.8; margin-top: 4px;'>{timestamp}</div>
    </div>
</div>
"""
    else:
        agent_emoji = get_agent_emoji(agent)
        return f"""
<div style='text-align: left; margin: 10px 0;'>
    <div style='display: inline-block; background: white; border: 1px solid #e0e0e0; 
                color: #333; padding: 12px 16px; border-radius: 18px 18px 18px 4px; 
                max-width: 70%; word-wrap: break-word; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
        {f'<div style="font-size: 11px; color: #666; margin-bottom: 4px;">{agent_emoji} {agent.title()}</div>' if agent else ''}
        {message}
        <div style='font-size: 11px; color: #888; margin-top: 4px;'>{timestamp}</div>
    </div>
</div>
"""

# Main Application Functions
def process_text_message(message: str, chat_history: str, current_user: str, current_agent: str) -> Tuple[str, str]:
    """Process text message and update chat"""
    if not current_user:
        return chat_history, ""
    
    if not message.strip():
        return chat_history, message
    
    # Add user message to chat
    user_msg = format_message("user", message)
    chat_history += user_msg
    
    # Send to API
    response = send_text_message(current_user, message, current_agent)
    
    # Add bot response to chat
    bot_msg = format_message("bot", response["response"], response.get("agent_used", current_agent))
    chat_history += bot_msg
    
    return chat_history, ""

def process_image_upload(image, chat_history: str, current_user: str) -> str:
    """Process image upload"""
    if not current_user or not image:
        return chat_history
    
    # Add user message
    user_msg = format_message("user", "📸 Image uploaded for analysis")
    chat_history += user_msg
    
    # Send to API
    response = upload_image_to_api(current_user, image)
    
    # Add bot response
    bot_msg = format_message("bot", response["response"], response.get("agent_used", "image_analysis"))
    chat_history += bot_msg
    
    return chat_history

def process_audio_upload(audio, chat_history: str, current_user: str, current_agent: str) -> str:
    """Process audio upload"""
    if not current_user or not audio:
        return chat_history
    
    # Add user message
    user_msg = format_message("user", "🎤 Audio recorded for processing")
    chat_history += user_msg
    
    # Send to API
    response = upload_audio_to_api(current_user, audio, current_agent)
    
    # Add transcription message
    if "transcribed_text" in response:
        transcription_msg = format_message("user", f"🎯 Transcribed: \"{response['transcribed_text']}\"")
        chat_history += transcription_msg
    
    # Add bot response
    bot_msg = format_message("bot", response["response"], response.get("agent_used", current_agent))
    chat_history += bot_msg
    
    return chat_history

def handle_login(email: str, password: str) -> Tuple[str, str, str]:
    """Handle user login"""
    if not email or not password:
        return "", "Please enter both email and password", ""
    
    success, message = login_user(email, password)
    if success:
        welcome_msg = format_message("bot", f"Welcome back! I'm RepGenie, your AI fitness trainer. How can I help you today?", "workout")
        return email, "", welcome_msg
    else:
        return "", message, ""

def handle_register(email: str, password: str, confirm_password: str) -> Tuple[str, str, str]:
    """Handle user registration"""
    if not email or not password or not confirm_password:
        return "", "Please fill all fields", ""
    
    if password != confirm_password:
        return "", "Passwords don't match", ""
    
    success, message = register_user(email, password)
    if success:
        welcome_msg = format_message("bot", f"Welcome to RepGenie! I'm your AI fitness trainer. Let's start your fitness journey!", "workout")
        return email, "", welcome_msg
    else:
        return "", message, ""

def handle_logout() -> Tuple[str, str, str, str]:
    """Handle user logout"""
    return "", "", "", ""

def switch_agent(agent: str, chat_history: str, current_user: str) -> Tuple[str, str]:
    """Switch to different agent"""
    if not current_user:
        return chat_history, agent
    
    agent_messages = {
        "workout": "💪 Workout mode activated - I'm ready to help with your fitness and meal planning!",
        "news": "🌐 Web Search activated - I can now search for the latest fitness and nutrition news!",
        "youtube": "📺 Video Search activated - I can now search for fitness and workout videos on YouTube!"
    }
    
    if agent in agent_messages:
        bot_msg = format_message("bot", agent_messages[agent], agent)
        chat_history += bot_msg
    
    return chat_history, agent

# Custom CSS
custom_css = """
/* Main App Styling */
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

/* Chat Container */
.chat-container {
    background: #f8f9fa !important;
    border-radius: 20px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
    border: none !important;
}

/* Input Styling */
.input-container {
    background: white !important;
    border-radius: 25px !important;
    border: 2px solid #e0e0e0 !important;
    padding: 8px 16px !important;
}

/* Button Styling */
.primary-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 25px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    transition: transform 0.2s ease !important;
}

.primary-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4) !important;
}

.agent-btn {
    border-radius: 20px !important;
    border: 2px solid #e0e0e0 !important;
    background: white !important;
    padding: 10px 20px !important;
    margin: 5px !important;
    transition: all 0.3s ease !important;
}

.agent-btn.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border-color: transparent !important;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .gradio-container {
        padding: 10px !important;
    }
    
    .chat-container {
        margin: 5px !important;
        border-radius: 15px !important;
    }
}

/* Header Styling */
.app-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 20px 20px 0 0;
    text-align: center;
    margin-bottom: 0;
}

.app-title {
    font-size: 28px;
    font-weight: bold;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.app-subtitle {
    font-size: 14px;
    opacity: 0.9;
    margin: 5px 0 0 0;
}

/* Status Indicator */
.status-indicator {
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    margin: 10px 0;
}

.status-online {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.status-offline {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}
"""

# Initialize database
init_user_db()

# Create Gradio Interface
def create_app():
    with gr.Blocks(css=custom_css, title="RepGenie - AI Fitness Trainer", theme=gr.themes.Soft()) as app:
        
        # State variables
        current_user = gr.State("")
        current_agent = gr.State("workout")
        
        # Header
        gr.HTML("""
        <div class="app-header">
            <h1 class="app-title">🏋️ RepGenie</h1>
            <p class="app-subtitle">Your AI-Powered Fitness Trainer</p>
        </div>
        """)
        
        # Authentication Interface
        with gr.Column(visible=True) as auth_interface:
            gr.Markdown("## Welcome to RepGenie")
            
            with gr.Tab("Login"):
                with gr.Row():
                    with gr.Column(scale=1):
                        login_email = gr.Textbox(label="Email", placeholder="Enter your email")
                        login_password = gr.Textbox(label="Password", type="password", placeholder="Enter your password")
                        login_btn = gr.Button("Login", variant="primary", elem_classes="primary-btn")
                        login_message = gr.Markdown("")
            
            with gr.Tab("Sign Up"):
                with gr.Row():
                    with gr.Column(scale=1):
                        signup_email = gr.Textbox(label="Email", placeholder="Enter your email")
                        signup_password = gr.Textbox(label="Password", type="password", placeholder="Create a password")
                        signup_confirm = gr.Textbox(label="Confirm Password", type="password", placeholder="Confirm your password")
                        signup_btn = gr.Button("Sign Up", variant="primary", elem_classes="primary-btn")
                        signup_message = gr.Markdown("")
        
        # Main Chat Interface
        with gr.Column(visible=False) as chat_interface:
            
            # User Info & Controls
            with gr.Row():
                with gr.Column(scale=3):
                    user_info = gr.Markdown("")
                with gr.Column(scale=1):
                    logout_btn = gr.Button("Logout", variant="secondary")
            
            # Agent Selection
            with gr.Row():
                gr.Markdown("### Choose Your AI Agent:")
                with gr.Row():
                    workout_btn = gr.Button("💪 Workout Coach", elem_classes="agent-btn active")
                    news_btn = gr.Button("🌐 News Search", elem_classes="agent-btn")
                    youtube_btn = gr.Button("📺 Video Search", elem_classes="agent-btn")
            
            # Current Agent Display
            agent_status = gr.Markdown("**Current Agent:** 💪 Workout Coach")
            
            # Chat Area
            with gr.Row():
                with gr.Column(scale=1):
                    chat_history = gr.HTML(
                        value="",
                        elem_classes="chat-container",
                        label="Chat"
                    )
            
            # Input Area
            with gr.Row():
                with gr.Column(scale=4):
                    message_input = gr.Textbox(
                        placeholder="Type your fitness question here...",
                        label="",
                        elem_classes="input-container"
                    )
                with gr.Column(scale=1):
                    send_btn = gr.Button("Send", variant="primary", elem_classes="primary-btn")
            
            # File Uploads
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Upload Files")
                    with gr.Row():
                        with gr.Column():
                            image_upload = gr.Image(
                                label="📸 Upload Image (Body/Food Analysis)",
                                type="filepath",
                                height=200
                            )
                        with gr.Column():
                            audio_upload = gr.Audio(
                                label="🎤 Record/Upload Audio",
                                type="filepath"
                            )
        
        # Event Handlers
        
        # Authentication
        def show_chat_interface(user_email):
            if user_email:
                return {
                    auth_interface: gr.update(visible=False),
                    chat_interface: gr.update(visible=True),
                    user_info: f"**Logged in as:** {user_email}"
                }
            return {
                auth_interface: gr.update(visible=True),
                chat_interface: gr.update(visible=False)
            }
        
        def hide_chat_interface():
            return {
                auth_interface: gr.update(visible=True),
                chat_interface: gr.update(visible=False),
                chat_history: "",
                message_input: "",
                user_info: ""
            }
        
        # Login handlers
        login_btn.click(
            fn=handle_login,
            inputs=[login_email, login_password],
            outputs=[current_user, login_message, chat_history]
        ).then(
            fn=show_chat_interface,
            inputs=[current_user],
            outputs=[auth_interface, chat_interface, user_info]
        )
        
        signup_btn.click(
            fn=handle_register,
            inputs=[signup_email, signup_password, signup_confirm],
            outputs=[current_user, signup_message, chat_history]
        ).then(
            fn=show_chat_interface,
            inputs=[current_user],
            outputs=[auth_interface, chat_interface, user_info]
        )
        
        logout_btn.click(
            fn=handle_logout,
            outputs=[current_user, login_message, signup_message, chat_history]
        ).then(
            fn=hide_chat_interface,
            outputs=[auth_interface, chat_interface, chat_history, message_input, user_info]
        )
        
        # Chat handlers
        send_btn.click(
            fn=process_text_message,
            inputs=[message_input, chat_history, current_user, current_agent],
            outputs=[chat_history, message_input]
        )
        
        message_input.submit(
            fn=process_text_message,
            inputs=[message_input, chat_history, current_user, current_agent],
            outputs=[chat_history, message_input]
        )
        
        # Agent switching
        workout_btn.click(
            fn=lambda ch, cu: switch_agent("workout", ch, cu),
            inputs=[chat_history, current_user],
            outputs=[chat_history, current_agent]
        ).then(
            fn=lambda: ("**Current Agent:** 💪 Workout Coach"),
            outputs=[agent_status]
        )
        
        news_btn.click(
            fn=lambda ch, cu: switch_agent("news", ch, cu),
            inputs=[chat_history, current_user],
            outputs=[chat_history, current_agent]
        ).then(
            fn=lambda: ("**Current Agent:** 🌐 News Search"),
            outputs=[agent_status]
        )
        
        youtube_btn.click(
            fn=lambda ch, cu: switch_agent("youtube", ch, cu),
            inputs=[chat_history, current_user],
            outputs=[chat_history, current_agent]
        ).then(
            fn=lambda: ("**Current Agent:** 📺 Video Search"),
            outputs=[agent_status]
        )
        
        # File upload handlers
        image_upload.change(
            fn=process_image_upload,
            inputs=[image_upload, chat_history, current_user],
            outputs=[chat_history]
        )
        
        audio_upload.change(
            fn=process_audio_upload,
            inputs=[audio_upload, chat_history, current_user, current_agent],
            outputs=[chat_history]
        )
    
    return app

if __name__ == "__main__":
    # Create and launch the app
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True,
        show_error=True
    ) 