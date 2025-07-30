import base64
import uuid
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO
import mimetypes
import warnings
import hashlib
import secrets

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import Tool
from langchain_community.tools import YouTubeSearchTool
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from openai import OpenAI
from gnews import GNews
import os
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Fitness Trainer API", description="AI-powered fitness trainer with multiple agents", version="1.0.0")

# Add CORS middleware with mobile-friendly configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Cache-Control",
        "Pragma",
        "X-CSRFToken",
        "ngrok-skip-browser-warning"  # Special header for ngrok
    ],
    expose_headers=["*"],
    max_age=86400,  # Cache preflight for 24 hours
)

# Add middleware for mobile and ngrok compatibility
@app.middleware("http")
async def mobile_compatibility_middleware(request, call_next):
    """Middleware to handle mobile browser and ngrok compatibility issues"""
    
    # Add ngrok bypass header for mobile browsers
    if "ngrok" in str(request.url):
        response = await call_next(request)
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response
    
    response = await call_next(request)
    
    # Add mobile-friendly headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    
    # Add security headers for mobile
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    
    return response

# Environment variables
openai_api_key = os.getenv("openai_api_key")
if not openai_api_key:
    raise ValueError("OpenAI API key not found in environment variables")

# Initialize OpenAI models
llm = ChatOpenAI(temperature=0, api_key=openai_api_key, model="gpt-4o", max_tokens=1024)
client = OpenAI(api_key=openai_api_key)

# Database setup
def init_database():
    """Initialize the conversations and users database"""
    conn = sqlite3.connect('conversations.db')
    cursor = conn.cursor()
    
    # Create conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_type TEXT,
            used_agent BOOLEAN DEFAULT FALSE,
            human_message TEXT,
            ai_message TEXT,
            input_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create calendar entries table for logbook functionality
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            entry_date DATE NOT NULL,
            activity_type TEXT NOT NULL,
            custom_activity TEXT,
            duration INTEGER,
            intensity TEXT,
            additional_notes TEXT,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    
    # Create insights table for storing AI-generated insights
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            analysis_date DATE NOT NULL,
            workout_requested BOOLEAN DEFAULT FALSE,
            workout_type TEXT,
            meal_requested BOOLEAN DEFAULT FALSE,
            meal_type TEXT,
            video_requested BOOLEAN DEFAULT FALSE,
            video_type TEXT,
            news_requested BOOLEAN DEFAULT FALSE,
            news_type TEXT,
            image_analysis_done BOOLEAN DEFAULT FALSE,
            image_analysis_insights TEXT,
            conversation_summary TEXT NOT NULL,
            calendar_entries_logged BOOLEAN DEFAULT FALSE,
            entries_count INTEGER DEFAULT 0,
            calendar_entries_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_email, analysis_date),
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Password hashing functions
def generate_salt() -> str:
    """Generate a random salt for password hashing"""
    return secrets.token_hex(32)

def hash_password(password: str, salt: str) -> str:
    """Hash a password with salt using SHA-256"""
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password, salt) == password_hash

# User-specific memory storage
user_memories: Dict[str, ConversationBufferWindowMemory] = {}

def get_user_memory(thread_id: str) -> ConversationBufferWindowMemory:
    """Get or create user-specific memory"""
    if thread_id not in user_memories:
        user_memories[thread_id] = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=50,
            return_messages=True
        )
    return user_memories[thread_id]

def save_conversation(thread_id: str, agent_type: str, used_agent: bool, 
                     human_message: str, ai_message: str, input_type: str = "text"):
    """Save conversation to database"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (thread_id, agent_type, used_agent, human_message, ai_message, input_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (thread_id, agent_type, used_agent, human_message, ai_message, input_type))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving conversation: {e}")

# Pydantic models for authentication
class SignupRequest(BaseModel):
    email: str
    password: str
    confirm_password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: str

# Pydantic models for chat
class TextInput(BaseModel):
    thread_id: str
    query: str
    selected_agent: Optional[str] = "workout"

class AudioInput(BaseModel):
    thread_id: str
    selected_agent: Optional[str] = "workout"

class ImageInput(BaseModel):
    thread_id: str
    base64_image: str
    mime_type: Optional[str] = "image/png"

class AudioBase64Input(BaseModel):
    thread_id: str
    base64_audio: str
    selected_agent: Optional[str] = "workout"

# Pydantic models for calendar/logbook
class CalendarEntryCreate(BaseModel):
    user_email: str
    entry_date: str  # YYYY-MM-DD format
    activity_type: str  # workout, yoga, swimming, cycling, meditation, boxing, meal_planning, other
    custom_activity: Optional[str] = None  # For 'other' activity type
    duration: Optional[int] = None  # Duration in minutes (not applicable for meal planning)
    intensity: Optional[str] = None  # high, medium, low
    additional_notes: Optional[str] = None
    completed: bool = False

class CalendarEntryUpdate(BaseModel):
    activity_type: Optional[str] = None
    custom_activity: Optional[str] = None
    duration: Optional[int] = None
    intensity: Optional[str] = None
    additional_notes: Optional[str] = None
    completed: Optional[bool] = None

class CalendarEntryResponse(BaseModel):
    id: int
    user_email: str
    entry_date: str
    activity_type: str
    custom_activity: Optional[str] = None
    duration: Optional[int] = None
    intensity: Optional[str] = None
    additional_notes: Optional[str] = None
    completed: bool
    created_at: str
    updated_at: str

class ThreadResponse(BaseModel):
    thread_id: str
    message: str

# Pydantic models for insights
class InsightsRequest(BaseModel):
    user_email: str
    date: str  # YYYY-MM-DD format

class InsightsResponse(BaseModel):
    date: str
    user_email: str
    workout_requested: bool
    workout_type: Optional[str] = None
    meal_requested: bool
    meal_type: Optional[str] = None
    video_requested: bool
    video_type: Optional[str] = None
    news_requested: bool
    news_type: Optional[str] = None
    image_analysis_done: bool
    image_analysis_insights: Optional[str] = None
    conversation_summary: str
    calendar_entries_logged: bool
    entries_count: int
    calendar_entries_summary: Optional[str] = None

# Agent Tools and Functions
def create_news_agent(memory: ConversationBufferWindowMemory):
    """Create news agent with user-specific memory"""
    news_tool = Tool(
        name="news_agent",
        func=GNews(language='en', period='7d', max_results=5).get_news,
        description="Searches the latest fitness and meal news using the GNews tool."
    )
    
    news_template = """You are a fitness and meal news assistant named Repgenie. Your job is to search the latest news using the available tools.

You **must** follow this exact step-by-step format:

Question: the input question you must answer  
Thought: think about what to do next (e.g., "I should search news about bodybuilding")  
Action: the tool to use, choose from [{tool_names}]  
Action Input: the exact input to give the tool (e.g., "bodybuilding news")  
Observation: the result returned by the tool  
... (repeat Thought -> Action -> Action Input -> Observation as needed)  
Thought: I now know the final answer  
Final Answer: Format your final answer using markdown for better readability:
- Use **bold** for headlines and important points
- Use ## for section headings
- Use - for bullet points with news items
- Use [link text](URL) for clickable links
- Use > for quotes from articles
- Include emojis for visual appeal (📰 for news, 🏋️ for fitness, 🥗 for nutrition)

Only use tools listed below. Never answer directly without using a tool.

TOOLS:
{tools}

Begin!

History: {chat_history}  
Question: {input}  
{agent_scratchpad}"""

    news_prompt = PromptTemplate.from_template(news_template)
    news_agent = create_react_agent(llm, [news_tool], news_prompt)
    return AgentExecutor(agent=news_agent, tools=[news_tool], verbose=True, memory=memory)

def create_youtube_agent(memory: ConversationBufferWindowMemory):
    """Create YouTube agent with user-specific memory"""
    def youtube_search(query: str):
        tool = YouTubeSearchTool()
        return str(tool.run(query))
    
    youtube_tool = Tool(
        name="youtube_agent",
        func=youtube_search,
        description="Searches YouTube for fitness and meal related videos."
    )
    
    youtube_template = """You are a fitness and meal video assistant named Repgenie. Your job is to search for relevant YouTube videos using the available tools.

You **must** follow this exact step-by-step format:

Question: the input question you must answer
Thought: think about what to do next (e.g., "I should search for workout videos")
Action: the tool to use, choose from [{tool_names}]
Action Input: the exact input to give the tool (e.g., "workout videos")
Observation: the result returned by the tool
... (repeat Thought -> Action -> Action Input -> Observation as needed)
Thought: I now know the final answer
Final Answer: Format your final answer using markdown for better readability:
- Use **bold** for video titles and important points
- Use ## for section headings like "## Recommended Videos"
- Use - for bullet points with video descriptions
- Use [video title](YouTube URL) for clickable video links
- Include emojis for visual appeal (📺 for videos, 💪 for workouts, 🥗 for nutrition)
- Add brief descriptions of what each video covers

Only use tools listed below. Never answer directly without using a tool.

TOOLS:
{tools}

Begin!

History: {chat_history}
Question: {input}
{agent_scratchpad}"""

    youtube_prompt = PromptTemplate.from_template(youtube_template)
    youtube_agent = create_react_agent(llm, [youtube_tool], youtube_prompt)
    return AgentExecutor(agent=youtube_agent, tools=[youtube_tool], verbose=True, memory=memory)

def create_workout_meal_planner(memory: ConversationBufferWindowMemory):
    """Create workout and meal planner with user-specific memory"""
    prompt = PromptTemplate.from_template(
        """You are a Workout and Meal Planner Expert named RepGenie.
    You will generate the plan based on the user's activity level and other follow-up questions.
    Do NOT give a straight workout or meal plan immediately.
    Instead, ask step-by-step personalized questions to gather the user's preferences, lifestyle, and goals.

    IMPORTANT: Format your responses using markdown for better readability:
    - Use **bold** for emphasis
    - Use # for main headings, ## for subheadings  
    - Use bullet points with - for lists
    - Use numbered lists with 1. 2. 3. when appropriate
    - Use > for quotes or important notes
    - Use `code formatting` for specific exercises or measurements

    Use the conversation history to maintain continuity.

    History:
    {chat_history}

    User: {input}
    RepGenie:"""
    )
    
    return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=True)

def analyze_image_with_openai(base64_image: str, memory: ConversationBufferWindowMemory, mime_type: str = "image/png") -> tuple[str, str]:
    """Analyze image using GPT-4o with user-specific memory"""
    
    # Get conversation history for context
    chat_history = ""
    if memory.chat_memory.messages:
        for message in memory.chat_memory.messages[-10:]:  # Last 10 messages for context
            if isinstance(message, HumanMessage):
                chat_history += f"Human: {message.content}\n"
            elif isinstance(message, AIMessage):
                chat_history += f"Assistant: {message.content}\n"
    
    user_prompt = (
        "You are a world-class fitness and nutrition coach with expertise in image analysis named RepGenie. "
        "From the provided image, perform a detailed evaluation of any visible physique and/or food items.\n\n"
        
        "🧍‍♂️ If a human physique is visible:\n"
        "- Describe visible muscular definition and overall body composition\n"
        "- Estimate body fat percentage range based on visual cues\n"
        "- Assess muscle symmetry and proportions (e.g., chest to waist ratio, shoulder width)\n"
        "- Comment on conditioning and posture\n\n"
        
        "🍽️ If a meal or food is visible:\n"
        "- Identify key food items (e.g., protein source, carbs, vegetables)\n"
        "- Estimate macronutrient distribution (protein, carbs, fats)\n"
        "- Assess portion sizes and nutritional quality\n"
        "- Comment on whether it appears suitable for pre- or post-workout nutrition\n\n"
        
        "IMPORTANT: Format your response using markdown for better readability:\n"
        "- Use **bold** for emphasis and key points\n"
        "- Use ## for section headings like '## Physique Analysis' or '## Nutritional Breakdown'\n"
        "- Use - for bullet points with specific observations\n"
        "- Use > for important recommendations or quotes\n"
        "- Include relevant emojis for visual appeal (💪 for muscle, 🍎 for nutrition, ⚖️ for balance)\n"
        "- Use `specific measurements` or `exercise names` in code formatting when applicable\n\n"
        
        "Use the conversation history to provide personalized and contextual advice based on the user's goals and previous discussions.\n\n"
        
        f"Previous conversation context:\n{chat_history}\n\n" if chat_history else ""
        
        "Provide a holistic summary and any helpful suggestions for improvement if possible."
        "If the image is not showing any fitness or meal related content then just simply say that you cannot analyze because you cannot see any fitness/meal related content."
    )
    
    try:
        data_uri = f"data:{mime_type};base64,{base64_image}"
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    ]
                }
            ],
            max_tokens=512
        )
        
        reply = response.choices[0].message.content
        
        # Create a more descriptive human message for memory
        # Extract key info from the AI response to create context for other agents
        human_message = "I shared an image for fitness analysis. "
        if "physique" in reply.lower() or "body" in reply.lower() or "muscle" in reply.lower():
            human_message += "It appears to be a physique/body composition photo. "
        elif "food" in reply.lower() or "meal" in reply.lower() or "nutrition" in reply.lower():
            human_message += "It appears to be a food/meal photo. "
        else:
            human_message += "Please analyze this fitness-related image. "
        
        human_message += "Please consider this analysis in our future conversations about my fitness goals."
        
        # Store in user-specific memory with meaningful context
        memory.chat_memory.add_message(HumanMessage(content=human_message))
        memory.chat_memory.add_message(AIMessage(content=reply))
        
        return reply, human_message
    
    except Exception as e:
        error_message = f"Error analyzing image:  Please make sure your image has of one the following formats: ['png', 'jpeg', 'gif', 'webp']"
        return error_message, "I tried to share an image for analysis but there was an error."

def transcribe_audio_with_openai(audio_bytes: bytes) -> str:
    """Transcribe audio using OpenAI Whisper"""
    try:
        print(f"🎵 Processing audio file: {len(audio_bytes)} bytes")
        
        if len(audio_bytes) == 0:
            return "Error transcribing audio: Audio file is empty"
        
        # Detect audio format based on file signatures
        format_signatures = {
            b"RIFF": ".wav",
            b"ID3": ".mp3",
            b"\xff\xfb": ".mp3",  # MP3 with no ID3 tag
            b"\xff\xf3": ".mp3",  # MP3 alternative
            b"\xff\xf2": ".mp3",  # MP3 alternative  
            b"fLaC": ".flac",
            b"OggS": ".ogg",
            b"\x1a\x45\xdf\xa3": ".webm",  # WebM/Matroska signature
        }
        
        # Default to mp3 if no signature matches
        detected_ext = ".mp3"
        for signature, extension in format_signatures.items():
            if audio_bytes.startswith(signature):
                detected_ext = extension
                print(f"🎵 Detected audio format: {extension}")
                break
        
        # For WebM files, check if it's actually audio
        if detected_ext == ".webm":
            # WebM files can contain audio or video, we'll try as audio first
            detected_ext = ".webm"
        
        print(f"🎵 Using extension: {detected_ext}")
        
        # Create BytesIO stream for OpenAI
        audio_stream = BytesIO(audio_bytes)
        audio_stream.name = f"recording{detected_ext}"
        
        # Try transcription with detected format
        try:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_stream,
                response_format="text"
            )
            
            result = transcript.strip()
            print(f"🎯 Transcription successful: '{result}' ({len(result)} chars)")
            
            if not result:
                return "Error transcribing audio: No speech detected in audio"
            
            return result
            
        except Exception as transcription_error:
            print(f"❌ Transcription failed with {detected_ext}: {transcription_error}")
            
            # If WebM failed, try converting to a different format in memory
            if detected_ext == ".webm":
                print("🔄 Retrying WebM as MP3...")
                audio_stream = BytesIO(audio_bytes)
                audio_stream.name = "recording.mp3"
                
                try:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_stream,
                        response_format="text"
                    )
                    result = transcript.strip()
                    print(f"🎯 WebM->MP3 transcription successful: '{result}'")
                    return result if result else "Error transcribing audio: No speech detected in audio"
                except Exception as retry_error:
                    print(f"❌ WebM->MP3 retry also failed: {retry_error}")
            
            # If all else fails, return the original error
            raise transcription_error
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Audio transcription error: {error_msg}")
        
        # Provide more helpful error messages
        if "format" in error_msg.lower() or "codec" in error_msg.lower():
            return "Error transcribing audio: Unsupported audio format. Please try recording again."
        elif "too short" in error_msg.lower() or "duration" in error_msg.lower():
            return "Error transcribing audio: Audio too short. Please record for at least 1-2 seconds."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            return "Error transcribing audio: Network error. Please check your connection."
        else:
            return f"Error transcribing audio: {error_msg}"

# Fetch conversations directly from database
def get_conversations_from_db(user_email: str, date: str) -> list:
    """Get conversations directly from database for a specific user and date"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, agent_type, used_agent, human_message, ai_message, input_type, created_at
            FROM conversations 
            WHERE thread_id = ? AND DATE(date) = ?
            ORDER BY date ASC
        ''', (user_email, date))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                "date": row[0],
                "agent_type": row[1],
                "used_agent": row[2],
                "human_message": row[3],
                "ai_message": row[4],
                "input_type": row[5],
                "created_at": row[6]
            })
        
        conn.close()
        print(f"📊 Retrieved {len(conversations)} conversations from database for {user_email} on {date}")
        return conversations
        
    except Exception as e:
        print(f"❌ Error retrieving conversations from database: {e}")
        return []

def get_calendar_entries_from_db(user_email: str, date: str) -> list:
    """Get calendar entries directly from database for a specific user and date"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_email, entry_date, activity_type, custom_activity, 
                   duration, intensity, additional_notes, completed, created_at, updated_at
            FROM calendar_entries 
            WHERE user_email = ? AND entry_date = ?
            ORDER BY created_at ASC
        ''', (user_email, date))
        
        calendar_entries = []
        for row in cursor.fetchall():
            calendar_entries.append({
                "id": row[0],
                "user_email": row[1],
                "entry_date": row[2],
                "activity_type": row[3],
                "custom_activity": row[4],
                "duration": row[5],
                "intensity": row[6],
                "additional_notes": row[7],
                "completed": bool(row[8]),
                "created_at": row[9],
                "updated_at": row[10]
            })
        
        conn.close()
        print(f"📅 Retrieved {len(calendar_entries)} calendar entries from database for {user_email} on {date}")
        return calendar_entries
        
    except Exception as e:
        print(f"❌ Error retrieving calendar entries from database: {e}")
        return []

def analyze_user_insights_with_openai(conversations: list, calendar_entries: list, user_email: str, date: str) -> InsightsResponse:
    """Analyze user conversations and calendar entries using OpenAI to generate detailed insights"""
    
    print(f"🔍 Analyzing {len(conversations)} conversations and {len(calendar_entries)} calendar entries")
    
    # Prepare detailed conversation data for analysis
    conversation_text = ""
    workout_conversations = []
    meal_conversations = []
    video_conversations = []
    news_conversations = []
    image_conversations = []
    
    for conv in conversations:
        conversation_text += f"Agent: {conv['agent_type']}, Input: {conv['input_type']}, Time: {conv['date']}\n"
        conversation_text += f"Human: {conv['human_message']}\n"
        conversation_text += f"AI: {conv['ai_message']}\n\n"
        
        # Categorize conversations for detailed analysis
        if conv['agent_type'] == 'workout':
            workout_conversations.append(conv)
        if 'meal' in conv['human_message'].lower() or 'nutrition' in conv['human_message'].lower() or 'food' in conv['human_message'].lower():
            meal_conversations.append(conv)
        if conv['agent_type'] == 'youtube' or 'video' in conv['human_message'].lower():
            video_conversations.append(conv)
        if conv['agent_type'] == 'news':
            news_conversations.append(conv)
        if conv['input_type'] == 'image':
            image_conversations.append(conv)
    
    print(f"📝 Conversation categories: workout={len(workout_conversations)}, meal={len(meal_conversations)}, video={len(video_conversations)}, news={len(news_conversations)}, image={len(image_conversations)}")
    
    # Prepare detailed calendar entries data
    calendar_text = ""
    completed_activities = []
    pending_activities = []
    total_duration = 0
    
    for entry in calendar_entries:
        calendar_text += f"Activity: {entry['activity_type']}"
        if entry['custom_activity']:
            calendar_text += f" ({entry['custom_activity']})"
        if entry['duration']:
            calendar_text += f", Duration: {entry['duration']} minutes"
            total_duration += entry['duration']
        if entry['intensity']:
            calendar_text += f", Intensity: {entry['intensity']}"
        if entry['additional_notes']:
            calendar_text += f", Notes: {entry['additional_notes']}"
        calendar_text += f", Completed: {'Yes' if entry['completed'] else 'No'}, Created: {entry['created_at']}\n"
        
        if entry['completed']:
            completed_activities.append(entry)
        else:
            pending_activities.append(entry)
    
    print(f"📅 Calendar analysis: total_duration={total_duration} min, completed={len(completed_activities)}, pending={len(pending_activities)}")
    
    analysis_prompt = f"""
You are an AI fitness data analyst. Analyze the following comprehensive user data for {user_email} on {date} and provide detailed insights in JSON format.

DETAILED CONVERSATION ANALYSIS:
Total Conversations: {len(conversations)}
- Workout-related conversations: {len(workout_conversations)}
- Meal/Nutrition conversations: {len(meal_conversations)}
- Video/Tutorial requests: {len(video_conversations)}
- News requests: {len(news_conversations)}
- Image analysis sessions: {len(image_conversations)}

CONVERSATION DATA:
{conversation_text if conversation_text else "No conversations found for this date."}

DETAILED CALENDAR ANALYSIS:
Total Entries: {len(calendar_entries)}
- Completed activities: {len(completed_activities)}
- Pending activities: {len(pending_activities)}
- Total planned duration: {total_duration} minutes

CALENDAR ENTRIES:
{calendar_text if calendar_text else "No calendar entries found for this date."}

Provide a comprehensive analysis with detailed insights. Look for specific patterns:

1. WORKOUT ANALYSIS: Look for workout requests, types, goals, preferences
2. MEAL ANALYSIS: Look for nutrition questions, diet preferences, meal planning
3. VIDEO ANALYSIS: Look for tutorial requests, exercise demos, educational content
4. NEWS ANALYSIS: Look for fitness news, trends, research interests
5. IMAGE ANALYSIS: Check for physique photos, food photos, form checks

Return a JSON response (NO markdown code blocks, just pure JSON):
{{
    "workout_requested": boolean,
    "workout_type": "detailed workout type and goals mentioned",
    "meal_requested": boolean,
    "meal_type": "detailed meal preferences and nutrition goals",
    "video_requested": boolean,
    "video_type": "specific video content requested",
    "news_requested": boolean,
    "news_type": "specific news topics of interest",
    "image_analysis_done": boolean,
    "image_analysis_insights": "detailed summary of all image analysis performed",
    "conversation_summary": "comprehensive summary of all user interactions and goals (200-300 chars)",
    "calendar_entries_summary": "detailed breakdown of all planned and completed activities (150-200 chars)"
}}

Be very detailed in your analysis. Focus on the user's specific goals, preferences, and patterns.
"""

    try:
        print("🤖 Calling OpenAI for detailed analysis...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            max_tokens=1200,
            temperature=0.1
        )
        
        # Parse the JSON response - handle markdown code blocks
        import json
        response_content = response.choices[0].message.content.strip()
        print(f"🤖 OpenAI response: {response_content[:200]}...")
        
        # Remove markdown code blocks if present
        if response_content.startswith('```json'):
            response_content = response_content[7:]  # Remove ```json
        if response_content.startswith('```'):
            response_content = response_content[3:]   # Remove ```
        if response_content.endswith('```'):
            response_content = response_content[:-3]  # Remove ending ```
        
        response_content = response_content.strip()
        
        insights_json = json.loads(response_content)
        
        # Create detailed InsightsResponse object
        result = InsightsResponse(
            date=date,
            user_email=user_email,
            workout_requested=insights_json.get("workout_requested", False),
            workout_type=insights_json.get("workout_type"),
            meal_requested=insights_json.get("meal_requested", False),
            meal_type=insights_json.get("meal_type"),
            video_requested=insights_json.get("video_requested", False),
            video_type=insights_json.get("video_type"),
            news_requested=insights_json.get("news_requested", False),
            news_type=insights_json.get("news_type"),
            image_analysis_done=insights_json.get("image_analysis_done", False),
            image_analysis_insights=insights_json.get("image_analysis_insights"),
            conversation_summary=insights_json.get("conversation_summary", "No conversation summary available"),
            calendar_entries_logged=len(calendar_entries) > 0,
            entries_count=len(calendar_entries),
            calendar_entries_summary=insights_json.get("calendar_entries_summary")
        )
        
        print(f"✅ Detailed analysis complete: workout={result.workout_requested}, meal={result.meal_requested}, video={result.video_requested}, news={result.news_requested}")
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"❌ Cleaned response content: {response_content}")
        # Return detailed fallback insights
        return create_detailed_fallback_insights(conversations, calendar_entries, user_email, date)
        
    except Exception as e:
        print(f"❌ Error analyzing insights: {e}")
        # Return detailed fallback insights
        return create_detailed_fallback_insights(conversations, calendar_entries, user_email, date)

def create_detailed_fallback_insights(conversations: list, calendar_entries: list, user_email: str, date: str) -> InsightsResponse:
    """Create detailed fallback insights when AI analysis fails"""
    print("🔧 Creating detailed fallback insights due to AI analysis failure")
    
    # Detailed keyword-based analysis
    workout_requested = False
    meal_requested = False
    video_requested = False
    news_requested = False
    image_analysis_done = False
    
    workout_details = []
    meal_details = []
    video_details = []
    news_details = []
    image_details = []
    
    conversation_summary = "Analysis unavailable due to processing error"
    
    if conversations:
        all_text = " ".join([conv['human_message'].lower() for conv in conversations])
        
        # Detailed workout analysis
        workout_keywords = ['workout', 'exercise', 'training', 'muscle', 'strength', 'fitness', 'gym', 'bodybuilding', 'split', 'routine']
        if any(keyword in all_text for keyword in workout_keywords):
            workout_requested = True
            for conv in conversations:
                if any(keyword in conv['human_message'].lower() for keyword in workout_keywords):
                    workout_details.append(conv['human_message'][:50] + "...")
        
        # Detailed meal analysis
        meal_keywords = ['meal', 'nutrition', 'protein', 'diet', 'food', 'eating', 'calories', 'macro']
        if any(keyword in all_text for keyword in meal_keywords):
            meal_requested = True
            for conv in conversations:
                if any(keyword in conv['human_message'].lower() for keyword in meal_keywords):
                    meal_details.append(conv['human_message'][:50] + "...")
        
        # Detailed video analysis
        video_keywords = ['video', 'youtube', 'tutorial', 'show me', 'watch', 'demo']
        if any(keyword in all_text for keyword in video_keywords):
            video_requested = True
            for conv in conversations:
                if any(keyword in conv['human_message'].lower() for keyword in video_keywords):
                    video_details.append(conv['human_message'][:50] + "...")
        
        # Detailed news analysis
        news_keywords = ['news', 'latest', 'trending', 'updates', 'research']
        if any(keyword in all_text for keyword in news_keywords):
            news_requested = True
            for conv in conversations:
                if any(keyword in conv['human_message'].lower() for keyword in news_keywords):
                    news_details.append(conv['human_message'][:50] + "...")
        
        # Image analysis detection
        image_conversations = [conv for conv in conversations if conv['input_type'] == 'image']
        if image_conversations:
            image_analysis_done = True
            image_details = [f"Image analysis performed on {len(image_conversations)} photos"]
        
        conversation_summary = f"User engaged in {len(conversations)} fitness-related conversations covering workout planning, nutrition advice, and educational content."
    
    # Detailed calendar analysis
    calendar_summary = "No activities logged"
    if calendar_entries:
        completed = len([e for e in calendar_entries if e['completed']])
        pending = len(calendar_entries) - completed
        total_duration = sum([e['duration'] or 0 for e in calendar_entries])
        activities = list(set([e['activity_type'] for e in calendar_entries]))
        
        calendar_summary = f"Logged {len(calendar_entries)} activities ({', '.join(activities)}): {completed} completed, {pending} pending, {total_duration} min total"
    
    return InsightsResponse(
        date=date,
        user_email=user_email,
        workout_requested=workout_requested,
        workout_type="; ".join(workout_details[:3]) if workout_details else None,
        meal_requested=meal_requested,
        meal_type="; ".join(meal_details[:3]) if meal_details else None,
        video_requested=video_requested,
        video_type="; ".join(video_details[:3]) if video_details else None,
        news_requested=news_requested,
        news_type="; ".join(news_details[:3]) if news_details else None,
        image_analysis_done=image_analysis_done,
        image_analysis_insights="; ".join(image_details) if image_details else None,
        conversation_summary=conversation_summary,
        calendar_entries_logged=len(calendar_entries) > 0,
        entries_count=len(calendar_entries),
        calendar_entries_summary=calendar_summary
    )

def save_insights_to_database(insights: InsightsResponse) -> bool:
    """Save generated insights to database"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        # Use INSERT OR REPLACE to handle updates
        cursor.execute('''
            INSERT OR REPLACE INTO insights (
                user_email, analysis_date, workout_requested, workout_type,
                meal_requested, meal_type, video_requested, video_type,
                news_requested, news_type, image_analysis_done, image_analysis_insights,
                conversation_summary, calendar_entries_logged, entries_count,
                calendar_entries_summary, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            insights.user_email, insights.date, insights.workout_requested, insights.workout_type,
            insights.meal_requested, insights.meal_type, insights.video_requested, insights.video_type,
            insights.news_requested, insights.news_type, insights.image_analysis_done, insights.image_analysis_insights,
            insights.conversation_summary, insights.calendar_entries_logged, insights.entries_count,
            insights.calendar_entries_summary, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ Insights saved to database for {insights.user_email} on {insights.date}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving insights to database: {e}")
        return False

def get_insights_from_database(user_email: str, date: str) -> InsightsResponse | None:
    """Retrieve insights from database if they exist"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_email, analysis_date, workout_requested, workout_type,
                   meal_requested, meal_type, video_requested, video_type,
                   news_requested, news_type, image_analysis_done, image_analysis_insights,
                   conversation_summary, calendar_entries_logged, entries_count,
                   calendar_entries_summary, created_at, updated_at
            FROM insights 
            WHERE user_email = ? AND analysis_date = ?
        ''', (user_email, date))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            print(f"📊 Found existing insights for {user_email} on {date}")
            return InsightsResponse(
                user_email=row[0],
                date=row[1],
                workout_requested=bool(row[2]),
                workout_type=row[3],
                meal_requested=bool(row[4]),
                meal_type=row[5],
                video_requested=bool(row[6]),
                video_type=row[7],
                news_requested=bool(row[8]),
                news_type=row[9],
                image_analysis_done=bool(row[10]),
                image_analysis_insights=row[11],
                conversation_summary=row[12],
                calendar_entries_logged=bool(row[13]),
                entries_count=row[14],
                calendar_entries_summary=row[15]
            )
        else:
            print(f"🔍 No existing insights found for {user_email} on {date}")
            return None
            
    except Exception as e:
        print(f"❌ Error retrieving insights from database: {e}")
        return None

# API Endpoints
@app.post("/generate_thread_id")
async def generate_thread_id(email: str):
    """Generate a new thread ID for a user"""
    # unique_id = str(uuid.uuid4())
    thread_id = f"{email}"
    return {"thread_id": thread_id}

@app.post("/auth/signup", response_model=UserResponse)
async def signup(request: SignupRequest):
    """User registration endpoint"""
    try:
        # Validate input
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        if request.password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        if len(request.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        
        # Check if user already exists
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE email = ?', (request.email.lower(),))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        salt = generate_salt()
        password_hash = hash_password(request.password, salt)
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, salt)
            VALUES (?, ?, ?)
        ''', (request.email.lower(), password_hash, salt))
        
        user_id = cursor.lastrowid
        
        # Get the created user
        cursor.execute('SELECT id, email, created_at FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        return UserResponse(
            id=user_data[0],
            email=user_data[1],
            created_at=user_data[2]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.post("/auth/login", response_model=UserResponse)
async def login(request: LoginRequest):
    """User login endpoint"""
    try:
        if not request.email or not request.password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute('''
            SELECT id, email, password_hash, salt, created_at 
            FROM users WHERE email = ?
        ''', (request.email.lower(),))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user_id, email, stored_hash, salt, created_at = user_data
        
        # Verify password
        if not verify_password(request.password, salt, stored_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return UserResponse(
            id=user_id,
            email=email,
            created_at=created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@app.post("/chat/text")
async def chat_text(input_data: TextInput):
    """Handle text input"""
    try:
        memory = get_user_memory(input_data.thread_id)
        
        if input_data.selected_agent == "workout":
            planner = create_workout_meal_planner(memory)
            response = planner.invoke({"input": input_data.query})['text']
            agent_type = "workout"
            used_agent = True
            
        elif input_data.selected_agent == "news":
            news_executor = create_news_agent(memory)
            response = news_executor.invoke({"input": input_data.query}, handle_parsing_errors=True)['output']
            agent_type = "news"
            used_agent = True
            
        elif input_data.selected_agent == "youtube":
            youtube_executor = create_youtube_agent(memory)
            response = youtube_executor.invoke({"input": input_data.query}, handle_parsing_errors=True)['output']
            agent_type = "youtube" 
            used_agent = True
            
        else:
            # All agents
            responses = []
            
            planner = create_workout_meal_planner(memory)
            workout_response = planner.invoke({"input": input_data.query})['text']
            responses.append("🧠 **Workout/Meal Plan**:\n" + workout_response)
            
            news_executor = create_news_agent(memory)
            news_response = news_executor.invoke({"input": input_data.query}, handle_parsing_errors=True)['output']
            responses.append("📰 **News**:\n" + news_response)
            
            youtube_executor = create_youtube_agent(memory)
            youtube_response = youtube_executor.invoke({"input": input_data.query}, handle_parsing_errors=True)['output']
            responses.append("📺 **YouTube**:\n" + youtube_response)
            
            response = "\n\n".join(responses)
            agent_type = "all"
            used_agent = True
        
        # Save conversation
        save_conversation(
            input_data.thread_id, agent_type, used_agent, 
            input_data.query, response, "text"
        )
        
        return {"response": response, "agent_used": agent_type}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text input: {str(e)}")

@app.post("/chat/image")
async def chat_image(input_data: ImageInput):
    """Handle base64 image input"""
    try:
        memory = get_user_memory(input_data.thread_id)
        response, human_message = analyze_image_with_openai(input_data.base64_image, memory, input_data.mime_type)
        
        # Save conversation with descriptive message
        save_conversation(
            input_data.thread_id, "image_analysis", True,
            human_message, response, "image"
        )
        
        return {"response": response, "agent_used": "image_analysis"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/chat/image_upload")
async def chat_image_upload(
    thread_id: str = Form(...),
    image_file: UploadFile = File(...)
):
    """Handle image file upload"""
    try:
        # Read image file
        image_bytes = await image_file.read()
        
        # Convert to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Detect MIME type from file
        mime_type = image_file.content_type
        if not mime_type or not mime_type.startswith('image/'):
            # Fallback: try to detect from file extension
            if image_file.filename:
                ext = image_file.filename.lower().split('.')[-1]
                mime_map = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg', 
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'webp': 'image/webp',
                    'bmp': 'image/bmp'
                }
                mime_type = mime_map.get(ext, 'image/png')
            else:
                mime_type = 'image/png'  # Default fallback
        
        memory = get_user_memory(thread_id)
        response, human_message = analyze_image_with_openai(base64_image, memory, mime_type)
        
        # Enhance human message with filename context
        enhanced_human_message = human_message.replace("I shared an image", f"I uploaded an image file '{image_file.filename}'")
        
        # Save conversation with descriptive message
        save_conversation(
            thread_id, "image_analysis", True,
            enhanced_human_message, response, "image"
        )
        
        return {
            "response": response, 
            "agent_used": "image_analysis",
            "detected_mime_type": mime_type,
            "filename": image_file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing uploaded image: {str(e)}")

@app.post("/chat/audio")
async def chat_audio(
    thread_id: str = Form(...),
    selected_agent: str = Form("workout"),
    audio_file: UploadFile = File(...)
):
    """Handle audio input"""
    try:
        # Read audio file
        audio_bytes = await audio_file.read()
        
        # Transcribe audio
        transcribed_text = transcribe_audio_with_openai(audio_bytes)
        
        if "Error" in transcribed_text:
            raise HTTPException(status_code=400, detail=transcribed_text)
        
        memory = get_user_memory(thread_id)
        
        # Process transcribed text with selected agent
        if selected_agent == "workout":
            planner = create_workout_meal_planner(memory)
            response = "🧠 **Workout/Meal Plan**:\n" + planner.invoke({"input": transcribed_text})['text']
            
        elif selected_agent == "news":
            news_executor = create_news_agent(memory)
            response = "📰 **News**:\n" + news_executor.invoke({"input": transcribed_text}, handle_parsing_errors=True)['output']
            
        elif selected_agent == "youtube":
            youtube_executor = create_youtube_agent(memory)
            response = "📺 **YouTube**:\n" + youtube_executor.invoke({"input": transcribed_text}, handle_parsing_errors=True)['output']
            
        else:
            response = f"Unsupported agent: {selected_agent}"
        
        # Save conversation
        save_conversation(
            thread_id, selected_agent, True,
            f"[Audio] {transcribed_text}", response, "audio"
        )
        
        return {
            "transcribed_text": transcribed_text,
            "response": response,
            "agent_used": selected_agent
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@app.post("/chat/audio_base64")
async def chat_audio_base64(input_data: AudioBase64Input):
    """Handle base64 encoded audio input"""
    try:
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(input_data.base64_audio)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {str(e)}")
        
        # Transcribe audio
        transcribed_text = transcribe_audio_with_openai(audio_bytes)
        
        if "Error" in transcribed_text:
            raise HTTPException(status_code=400, detail=transcribed_text)
        
        memory = get_user_memory(input_data.thread_id)
        
        # Process transcribed text with selected agent
        if input_data.selected_agent == "workout":
            planner = create_workout_meal_planner(memory)
            response = "🧠 **Workout/Meal Plan**:\n" + planner.invoke({"input": transcribed_text})['text']
            
        elif input_data.selected_agent == "news":
            news_executor = create_news_agent(memory)
            response = "📰 **News**:\n" + news_executor.invoke({"input": transcribed_text}, handle_parsing_errors=True)['output']
            
        elif input_data.selected_agent == "youtube":
            youtube_executor = create_youtube_agent(memory)
            response = "📺 **YouTube**:\n" + youtube_executor.invoke({"input": transcribed_text}, handle_parsing_errors=True)['output']
            
        else:
            response = f"Unsupported agent: {input_data.selected_agent}"
        
        # Save conversation
        save_conversation(
            input_data.thread_id, input_data.selected_agent, True,
            f"[Audio Base64] {transcribed_text}", response, "audio"
        )
        
        return {
            "transcribed_text": transcribed_text,
            "response": response,
            "agent_used": input_data.selected_agent
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing base64 audio: {str(e)}")

@app.get("/conversation_history/{thread_id}")
async def get_conversation_history(thread_id: str, limit: Optional[int] = 50):
    """Get conversation history for a thread"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, agent_type, used_agent, human_message, ai_message, input_type
            FROM conversations 
            WHERE thread_id = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (thread_id, limit))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                "date": row[0],
                "agent_type": row[1],
                "used_agent": row[2],
                "human_message": row[3],
                "ai_message": row[4],
                "input_type": row[5]
            })
        
        conn.close()
        return {"conversations": conversations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation history: {str(e)}")

@app.delete("/clear_memory/{thread_id}")
async def clear_user_memory(thread_id: str):
    """Clear memory for a specific user thread"""
    try:
        if thread_id in user_memories:
            del user_memories[thread_id]
        return {"message": f"Memory cleared for thread {thread_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing memory: {str(e)}")

# Calendar/Logbook API Endpoints
@app.post("/calendar/entries", response_model=CalendarEntryResponse)
async def create_calendar_entry(entry: CalendarEntryCreate):
    """Create a new calendar entry"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        # Validate activity type
        valid_activities = ['workout', 'yoga', 'swimming', 'cycling', 'meditation', 'boxing', 'meal_planning', 'other']
        if entry.activity_type not in valid_activities:
            raise HTTPException(status_code=400, detail=f"Invalid activity type. Must be one of: {valid_activities}")
        
        # Validate intensity if provided
        if entry.intensity and entry.intensity not in ['high', 'medium', 'low']:
            raise HTTPException(status_code=400, detail="Intensity must be 'high', 'medium', or 'low'")
        
        # For 'other' activity type, custom_activity is required
        if entry.activity_type == 'other' and not entry.custom_activity:
            raise HTTPException(status_code=400, detail="Custom activity name is required when activity type is 'other'")
        
        # Insert the entry
        cursor.execute('''
            INSERT INTO calendar_entries (
                user_email, entry_date, activity_type, custom_activity, 
                duration, intensity, additional_notes, completed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.user_email, entry.entry_date, entry.activity_type, entry.custom_activity,
            entry.duration, entry.intensity, entry.additional_notes, entry.completed
        ))
        
        entry_id = cursor.lastrowid
        
        # Get the created entry
        cursor.execute('''
            SELECT id, user_email, entry_date, activity_type, custom_activity, 
                   duration, intensity, additional_notes, completed, created_at, updated_at
            FROM calendar_entries WHERE id = ?
        ''', (entry_id,))
        
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        
        return CalendarEntryResponse(
            id=row[0],
            user_email=row[1],
            entry_date=row[2],
            activity_type=row[3],
            custom_activity=row[4],
            duration=row[5],
            intensity=row[6],
            additional_notes=row[7],
            completed=bool(row[8]),
            created_at=row[9],
            updated_at=row[10]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating calendar entry: {str(e)}")

@app.get("/calendar/entries/{user_email}")
async def get_calendar_entries(user_email: str, date: Optional[str] = None):
    """Get calendar entries for a user, optionally filtered by date"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        if date:
            # Get entries for specific date
            cursor.execute('''
                SELECT id, user_email, entry_date, activity_type, custom_activity, 
                       duration, intensity, additional_notes, completed, created_at, updated_at
                FROM calendar_entries 
                WHERE user_email = ? AND entry_date = ?
                ORDER BY created_at DESC
            ''', (user_email, date))
        else:
            # Get all entries for user
            cursor.execute('''
                SELECT id, user_email, entry_date, activity_type, custom_activity, 
                       duration, intensity, additional_notes, completed, created_at, updated_at
                FROM calendar_entries 
                WHERE user_email = ?
                ORDER BY entry_date DESC, created_at DESC
            ''', (user_email,))
        
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            entries.append(CalendarEntryResponse(
                id=row[0],
                user_email=row[1],
                entry_date=row[2],
                activity_type=row[3],
                custom_activity=row[4],
                duration=row[5],
                intensity=row[6],
                additional_notes=row[7],
                completed=bool(row[8]),
                created_at=row[9],
                updated_at=row[10]
            ))
        
        return {"entries": entries}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving calendar entries: {str(e)}")

@app.put("/calendar/entries/{entry_id}")
async def update_calendar_entry(entry_id: int, update_data: CalendarEntryUpdate):
    """Update a calendar entry"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        # Check if entry exists
        cursor.execute('SELECT id FROM calendar_entries WHERE id = ?', (entry_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Calendar entry not found")
        
        # Build update query dynamically
        update_fields = []
        update_values = []
        
        if update_data.activity_type is not None:
            valid_activities = ['workout', 'yoga', 'swimming', 'cycling', 'meditation', 'boxing', 'meal_planning', 'other']
            if update_data.activity_type not in valid_activities:
                raise HTTPException(status_code=400, detail=f"Invalid activity type. Must be one of: {valid_activities}")
            update_fields.append('activity_type = ?')
            update_values.append(update_data.activity_type)
        
        if update_data.custom_activity is not None:
            update_fields.append('custom_activity = ?')
            update_values.append(update_data.custom_activity)
        
        if update_data.duration is not None:
            update_fields.append('duration = ?')
            update_values.append(update_data.duration)
        
        if update_data.intensity is not None:
            if update_data.intensity not in ['high', 'medium', 'low']:
                raise HTTPException(status_code=400, detail="Intensity must be 'high', 'medium', or 'low'")
            update_fields.append('intensity = ?')
            update_values.append(update_data.intensity)
        
        if update_data.additional_notes is not None:
            update_fields.append('additional_notes = ?')
            update_values.append(update_data.additional_notes)
        
        if update_data.completed is not None:
            update_fields.append('completed = ?')
            update_values.append(update_data.completed)
        
        if not update_fields:
            conn.close()
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated_at
        update_fields.append('updated_at = ?')
        update_values.append(datetime.now().isoformat())
        
        # Add entry_id for WHERE clause
        update_values.append(entry_id)
        
        query = f"UPDATE calendar_entries SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
        
        conn.commit()
        conn.close()
        
        return {"message": "Calendar entry updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating calendar entry: {str(e)}")

@app.delete("/calendar/entries/{entry_id}")
async def delete_calendar_entry(entry_id: int):
    """Delete a calendar entry"""
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        # Check if entry exists
        cursor.execute('SELECT id FROM calendar_entries WHERE id = ?', (entry_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Calendar entry not found")
        
        # Delete the entry
        cursor.execute('DELETE FROM calendar_entries WHERE id = ?', (entry_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": "Calendar entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting calendar entry: {str(e)}")

@app.get("/insights/{user_email}", response_model=InsightsResponse)
async def get_user_insights(user_email: str, date: str, regenerate: bool = False):
    """Get AI-powered insights for a user on a specific date"""
    try:
        # First, check if insights already exist in database (unless regeneration is forced)
        if not regenerate:
            existing_insights = get_insights_from_database(user_email, date)
            if existing_insights:
                print(f"📊 Returning cached insights for {user_email} on {date}")
                return existing_insights
        
        print(f"🧠 Generating new insights for {user_email} on {date}")
        
        # Fetch conversations and calendar entries directly from database
        conversations = get_conversations_from_db(user_email, date)
        calendar_entries = get_calendar_entries_from_db(user_email, date)
        
        # Analyze the data using OpenAI
        insights = analyze_user_insights_with_openai(conversations, calendar_entries, user_email, date)
        
        # Save the generated insights to database
        save_success = save_insights_to_database(insights)
        if save_success:
            print(f"💾 Insights cached for future requests")
        else:
            print(f"⚠️ Insights generated but not cached")
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@app.post("/insights/{user_email}/regenerate", response_model=InsightsResponse)
async def regenerate_user_insights(user_email: str, date: str):
    """Force regeneration of insights for a user on a specific date"""
    try:
        return await get_user_insights(user_email, date, regenerate=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating insights: {str(e)}")

@app.options("/{path:path}")
async def handle_options(path: str):
    """Handle preflight OPTIONS requests for all paths"""
    return {"message": "OK"}

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint for mobile debugging"""
    return {
        "status": "healthy", 
        "message": "Fitness Trainer API is running",
        "timestamp": datetime.now().isoformat(),
        "mobile_compatible": True,
        "cors_enabled": True,
        "ngrok_compatible": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 