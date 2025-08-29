from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os, logging, json, base64, uuid, asyncio
import requests
from datetime import datetime, timedelta
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Enhanced Voice AI Assistant", version="2.0.0")

# CORS middleware for better security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Global storage with API key management
chat_histories = {}
session_personas = {}
session_metadata = {}
session_api_keys = {}  # NEW: Store API keys per session

# Default API keys (fallback)
DEFAULT_API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY", "your key"),
    "openweather": os.getenv("OPENWEATHER_API_KEY", "your key"),
    "tavily": os.getenv("TAVILY_API_KEY", "your key")
}

# ---- ENHANCED SKILL FUNCTIONS WITH DYNAMIC API KEYS ----

def get_session_api_keys(session_id: str) -> dict:
    """Get API keys for a session, with fallback to defaults"""
    session_keys = session_api_keys.get(session_id, {})
    return {
        "gemini": session_keys.get("gemini") or DEFAULT_API_KEYS["gemini"],
        "openweather": session_keys.get("openweather") or DEFAULT_API_KEYS["openweather"],
        "tavily": session_keys.get("tavily") or DEFAULT_API_KEYS["tavily"]
    }

def get_current_weather_enhanced(location: str, session_id: str, units: str = "metric") -> dict:
    """Enhanced weather function with session-specific API keys"""
    try:
        api_keys = get_session_api_keys(session_id)
        openweather_key = api_keys["openweather"]
        
        if openweather_key and openweather_key != "your openweather api key here":
            # Add country codes for better accuracy
            location_mapping = {
                "tokyo": "Tokyo,JP", "london": "London,GB", "paris": "Paris,FR",
                "new york": "New York,US", "mumbai": "Mumbai,IN", "delhi": "Delhi,IN"
            }
            
            if "," not in location:
                location = location_mapping.get(location.lower(), location)
            
            # Current weather API call
            current_url = "http://api.openweathermap.org/data/2.5/weather"
            current_params = {
                'q': location,
                'appid': openweather_key,
                'units': units
            }
            
            logging.info(f"Weather API call for {location} with session key")
            response = requests.get(current_url, params=current_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Generate weather alerts and recommendations
                alerts = generate_weather_alerts(data)
                recommendations = generate_weather_recommendations(data)
                
                return {
                    "status": "success",
                    "source": "OpenWeatherMap API (User Key)",
                    "current": {
                        "location": f"{data['name']}, {data['sys']['country']}",
                        "temperature": f"{data['main']['temp']:.1f}°{'C' if units == 'metric' else 'F'}",
                        "feels_like": f"{data['main']['feels_like']:.1f}°{'C' if units == 'metric' else 'F'}",
                        "condition": data['weather'][0]['description'].title(),
                        "humidity": f"{data['main']['humidity']}%",
                        "pressure": f"{data['main']['pressure']} hPa",
                        "wind_speed": f"{data['wind']['speed']} {'m/s' if units == 'metric' else 'mph'}",
                        "wind_direction": get_wind_direction(data['wind'].get('deg', 0)),
                        "visibility": f"{data.get('visibility', 10000)/1000:.1f} km",
                        "sunrise": datetime.fromtimestamp(data['sys']['sunrise']).strftime("%H:%M"),
                        "sunset": datetime.fromtimestamp(data['sys']['sunset']).strftime("%H:%M")
                    },
                    "alerts": alerts,
                    "recommendations": recommendations,
                    "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            elif response.status_code == 401:
                return {"error": "Invalid OpenWeather API key. Please check your API key in settings."}
            elif response.status_code == 404:
                return {"error": f"City '{location}' not found. Try including country code (e.g., 'Tokyo,JP')"}
            else:
                return {"error": f"Weather service error: {response.status_code}"}
        
        # Fallback to enhanced mock data
        return create_enhanced_mock_weather(location)
        
    except Exception as e:
        logging.error(f"Weather API error: {e}")
        return create_enhanced_mock_weather(location, error=True)

def get_wind_direction(degrees):
    """Convert wind degrees to compass direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(degrees / 22.5) % 16
    return directions[idx]

def generate_weather_alerts(weather_data):
    """Generate weather alerts based on current conditions"""
    alerts = []
    temp = weather_data['main']['temp']
    wind_speed = weather_data['wind']['speed']
    condition = weather_data['weather'][0]['main'].lower()
    
    if temp > 35:
        alerts.append("🌡️ High temperature alert: Stay hydrated and avoid prolonged outdoor exposure")
    elif temp < 0:
        alerts.append("❄️ Freezing temperature alert: Dress warmly and watch for icy conditions")
    
    if wind_speed > 10:
        alerts.append("💨 High wind alert: Secure loose objects and be cautious while driving")
    
    if condition in ['rain', 'thunderstorm']:
        alerts.append("☔ Precipitation alert: Carry an umbrella and drive carefully")
    
    return alerts

def generate_weather_recommendations(weather_data):
    """Generate personalized recommendations based on weather"""
    recommendations = []
    temp = weather_data['main']['temp']
    condition = weather_data['weather'][0]['description'].lower()
    
    # Clothing recommendations
    if temp > 25:
        recommendations.append("👕 Wear light, breathable clothing")
    elif temp > 15:
        recommendations.append("👔 Light jacket or sweater recommended")
    elif temp > 5:
        recommendations.append("🧥 Warm jacket needed")
    else:
        recommendations.append("🧤 Heavy winter clothing, gloves, and hat recommended")
    
    # Activity recommendations
    if 'rain' in condition or 'storm' in condition:
        recommendations.append("🏠 Good day for indoor activities")
    elif 'clear' in condition or 'sunny' in condition:
        recommendations.append("☀️ Perfect weather for outdoor activities")
    elif 'cloud' in condition:
        recommendations.append("⛅ Great for walks and outdoor exercise")
        
    return recommendations

def create_enhanced_mock_weather(location: str, error: bool = False) -> dict:
    """Create enhanced mock weather data when API is not available"""
    if error:
        return {
            "status": "demo",
            "source": "Mock Data (API Error)",
            "error": "Weather service temporarily unavailable - showing demo data"
        }
    
    import random
    
    # Simulate realistic weather based on location
    mock_temps = {
        "london": (8, 15, "Partly cloudy"),
        "new york": (12, 22, "Clear sky"),
        "tokyo": (18, 25, "Light rain"),
        "mumbai": (26, 32, "Humid and cloudy"),
        "delhi": (20, 28, "Hazy"),
        "default": (15, 22, "Clear sky")
    }
    
    location_key = location.lower()
    temp_range = None
    for key in mock_temps:
        if key in location_key:
            temp_range = mock_temps[key]
            break
    
    if not temp_range:
        temp_range = mock_temps["default"]
    
    min_temp, max_temp, condition = temp_range
    current_temp = random.randint(min_temp, max_temp)
    
    return {
        "status": "demo",
        "source": "Mock Data (Demo Mode - Configure API Key)",
        "current": {
            "location": f"{location.title()}",
            "temperature": f"{current_temp}°C",
            "feels_like": f"{current_temp + random.randint(-2, 3)}°C",
            "condition": condition,
            "humidity": f"{random.randint(40, 80)}%",
            "pressure": f"{random.randint(1008, 1025)} hPa",
            "wind_speed": f"{random.randint(3, 12)} m/s",
            "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            "visibility": f"{random.randint(8, 15)} km",
            "sunrise": "06:30",
            "sunset": "18:45"
        },
        "alerts": ["📋 Demo mode: Configure your OpenWeather API key for real alerts"],
        "recommendations": ["🔑 Demo mode: Add your API key in settings for personalized recommendations"],
        "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def search_web_with_fallback(query: str, session_id: str, max_results: int = 3) -> dict:
    """Search web with session-specific Tavily API key"""
    try:
        api_keys = get_session_api_keys(session_id)
        tavily_key = api_keys["tavily"]
        
        if tavily_key and tavily_key != "your tavily api key here":
            url = "https://api.tavily.com/search"
            headers = {"Content-Type": "application/json"}
            data = {
                "api_key": tavily_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": max_results
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                search_results = []
                
                for item in result.get('results', []):
                    search_results.append({
                        "title": item.get('title', ''),
                        "snippet": item.get('content', '')[:200] + '...',
                        "url": item.get('url', '')
                    })
                
                return {
                    "query": query,
                    "answer": result.get('answer', 'Information found from web search'),
                    "results": search_results,
                    "source": "Tavily API (User Key)",
                    "search_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        
        return create_mock_search_results(query)
        
    except Exception as e:
        logging.warning(f"Search failed: {e}, using mock results")
        return create_mock_search_results(query)

def create_mock_search_results(query: str) -> dict:
    """Create helpful mock search results when API is not available"""
    mock_results = {
        "ai": [
            {"title": "Latest AI Developments 2025", "snippet": "Artificial Intelligence continues to advance with new breakthroughs in machine learning...", "url": "https://example.com/ai-news"}
        ],
        "technology": [
            {"title": "Tech News Today", "snippet": "Latest technology developments including semiconductors, cloud computing...", "url": "https://example.com/tech-news"}
        ]
    }
    
    query_lower = query.lower()
    results = mock_results.get("technology", [{"title": f"Information about {query}", "snippet": f"Demo results for {query}...", "url": "https://example.com/search"}])
    
    return {
        "query": query,
        "answer": f"Demo results for {query}. Configure Tavily API key for real web search.",
        "results": results[:3],
        "source": "Mock Data (Demo Mode - Configure API Key)",
        "search_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_news_with_fallback(topic: str, session_id: str, max_results: int = 3) -> dict:
    """Get news with session-specific Tavily API key"""
    try:
        api_keys = get_session_api_keys(session_id)
        tavily_key = api_keys["tavily"]
        
        if tavily_key and tavily_key != "your tavily api key here":
            query = f"latest news {topic} today" if topic != "general" else "latest news today"
            
            url = "https://api.tavily.com/search"
            headers = {"Content-Type": "application/json"}
            data = {
                "api_key": tavily_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "max_results": max_results
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                news_articles = []
                
                for item in result.get('results', []):
                    news_articles.append({
                        "headline": item.get('title', ''),
                        "summary": item.get('content', '')[:300] + '...',
                        "url": item.get('url', ''),
                        "published": "Recent"
                    })
                
                return {
                    "topic": topic,
                    "articles": news_articles,
                    "source": "Tavily API (User Key)",
                    "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        
        return create_mock_news(topic)
        
    except Exception as e:
        logging.warning(f"News failed: {e}, using mock news")
        return create_mock_news(topic)

def create_mock_news(topic: str) -> dict:
    """Create relevant mock news when API is not available"""
    mock_news = {
        "general": [
            {"headline": "Global Economic Indicators Show Growth", "summary": "Demo news: Configure Tavily API key for real news...", "published": "Demo"}
        ]
    }
    
    articles = mock_news.get(topic.lower(), mock_news["general"])
    
    return {
        "topic": topic,
        "articles": articles,
        "source": "Mock Data (Demo Mode - Configure API Key)",
        "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_current_time() -> dict:
    """Get current time and date - No API required"""
    now = datetime.now()
    return {
        "current_time": now.strftime("%H:%M:%S"),
        "current_date": now.strftime("%Y-%m-%d"),
        "day_of_week": now.strftime("%A"),
        "timezone": "Local Time"
    }

def get_system_info() -> dict:
    """Get basic system information - No API required"""
    import platform
    try:
        import psutil
        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "memory_usage": f"{psutil.virtual_memory().percent}%",
            "disk_usage": f"{psutil.disk_usage('/').percent}%" if os.name != 'nt' else f"{psutil.disk_usage('C:\\').percent}%"
        }
    except ImportError:
        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "message": "Basic system info available"
        }

# ---- API ENDPOINTS ----

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/session")
async def create_session():
    session_id = str(uuid.uuid4())
    chat_histories[session_id] = []
    session_personas[session_id] = "default"
    session_api_keys[session_id] = {}  # Empty API keys initially
    session_metadata[session_id] = {
        "created_at": datetime.now().isoformat(),
        "total_messages": 0,
        "personas_used": ["default"],
        "api_keys_configured": []
    }
    logging.info(f"Created session {session_id}")
    return JSONResponse({"session_id": session_id})

@app.post("/session/{session_id}/api-keys")
async def update_api_keys(session_id: str, api_keys: dict):
    """Update API keys for a session"""
    if session_id in session_api_keys:
        # Validate and store API keys
        valid_keys = {}
        for key, value in api_keys.items():
            if key in ['gemini', 'openweather', 'tavily'] and value and value.strip():
                valid_keys[key] = value.strip()
        
        session_api_keys[session_id] = valid_keys
        
        # Update metadata
        if session_id in session_metadata:
            session_metadata[session_id]["api_keys_configured"] = list(valid_keys.keys())
        
        logging.info(f"Updated API keys for session {session_id}: {list(valid_keys.keys())}")
        return JSONResponse({
            "status": "success", 
            "configured_keys": list(valid_keys.keys()),
            "message": f"Configured {len(valid_keys)} API key(s)"
        })
    
    return JSONResponse({"status": "error", "message": "Invalid session"}, status_code=400)

@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session status including configured API keys"""
    if session_id in session_metadata:
        api_keys = get_session_api_keys(session_id)
        configured_keys = session_api_keys.get(session_id, {})
        
        return JSONResponse({
            "session_id": session_id,
            "metadata": session_metadata[session_id],
            "configured_api_keys": list(configured_keys.keys()),
            "available_features": {
                "weather": bool(api_keys["openweather"]),
                "web_search": bool(api_keys["tavily"]),
                "news": bool(api_keys["tavily"]),
                "ai_chat": bool(api_keys["gemini"]),
                "time_date": True,
                "system_info": True
            }
        })
    
    return JSONResponse({"status": "error", "message": "Session not found"}, status_code=404)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logging.info(f"WebSocket connected: {session_id}")

    # Define available functions
    available_functions = {
        "get_current_time": get_current_time,
        "get_system_info": get_system_info,
        "get_current_weather_enhanced": lambda location: get_current_weather_enhanced(location, session_id),
        "search_web_with_fallback": lambda query, max_results=3: search_web_with_fallback(query, session_id, max_results),
        "get_news_with_fallback": lambda topic="general", max_results=3: get_news_with_fallback(topic, session_id, max_results)
    }

    async def run_complete_pipeline(user_transcript: str):
        """Complete pipeline with session-specific API keys"""
        try:
            history = chat_histories.get(session_id, [])
            persona = session_personas.get(session_id, "default")
            metadata = session_metadata.get(session_id, {})
            api_keys = get_session_api_keys(session_id)

            # Enhanced persona prompts
            persona_prompts = {
                "friendly_teacher": """You are Sarah, a warm and patient teacher with access to real-time information including weather, news, web search, time/date, and system data. Use these tools to provide accurate, educational responses.""",
                "tech_support": """You are Alex, a professional tech support specialist with access to system information, web search, weather data, and news to provide comprehensive technical assistance.""",
                "storyteller": """You are Morgan, an imaginative storyteller who can incorporate real-world data from weather, news, and search to create engaging, contextual narratives.""",
                "default": """You are Jamie, a helpful AI assistant with access to comprehensive real-time information including weather forecasts, news updates, web search, system monitoring, and time/date services."""
            }

            # Initialize conversation
            if not history:
                system_prompt = persona_prompts.get(persona, persona_prompts["default"])
                history.append({"role": "user", "parts": [{"text": system_prompt}]})
                
                # Check configured API keys for personalized greeting
                configured_keys = list(session_api_keys.get(session_id, {}).keys())
                if configured_keys:
                    features_text = ", ".join(configured_keys).replace("_", " ").title()
                    greeting = f"Hello! I'm your {persona.replace('_', ' ')} assistant with {features_text} capabilities configured. What can I help you with?"
                else:
                    greeting = f"Hello! I'm your {persona.replace('_', ' ')} assistant. I can help with time/date and system info. Configure API keys in settings for weather, news, and web search!"
                
                history.append({"role": "model", "parts": [{"text": greeting}]})

            # Add user message
            history.append({"role": "user", "parts": [{"text": user_transcript}]})

            # Enhanced function calling logic
            try:
                # Configure Gemini with session API key
                gemini_key = api_keys["gemini"]
                if gemini_key:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel("gemini-1.5-flash-latest")
                else:
                    model = None
                
                user_lower = user_transcript.lower()
                function_result = None
                
                logging.info(f"Processing user input: '{user_transcript}' with keys: {list(session_api_keys.get(session_id, {}).keys())}")
                
                # WEATHER CHECK - PRIORITY 1
                if any(word in user_lower for word in ["weather", "temperature", "rain", "snow", "sunny", "cloudy", "forecast"]):
                    logging.info("Detected WEATHER request")
                    location = extract_location_from_text(user_transcript)
                    function_result = get_current_weather_enhanced(location, session_id)
                    
                    if function_result.get("status") in ["success", "demo"]:
                        current = function_result['current']
                        llm_response_text = f"Current weather in {current['location']}:\n\n"
                        llm_response_text += f"🌡️ **Temperature:** {current['temperature']} (feels like {current['feels_like']})\n"
                        llm_response_text += f"☀️ **Condition:** {current['condition']}\n"
                        llm_response_text += f"💧 **Humidity:** {current['humidity']}\n"
                        llm_response_text += f"🌪️ **Wind:** {current['wind_speed']} {current.get('wind_direction', '')}\n"
                        llm_response_text += f"👁️ **Visibility:** {current.get('visibility', 'N/A')}\n"
                        llm_response_text += f"🌅 **Sunrise:** {current.get('sunrise', 'N/A')} | 🌅 **Sunset:** {current.get('sunset', 'N/A')}\n\n"
                        
                        if function_result.get('alerts'):
                            llm_response_text += "**⚠️ Weather Alerts:**\n"
                            for alert in function_result['alerts']:
                                llm_response_text += f"• {alert}\n"
                            llm_response_text += "\n"
                        
                        if function_result.get('recommendations'):
                            llm_response_text += "**💡 Recommendations:**\n"
                            for rec in function_result['recommendations']:
                                llm_response_text += f"• {rec}\n"
                            llm_response_text += "\n"
                        
                        llm_response_text += f"*Source: {function_result['source']} | Updated: {function_result['retrieved_at']}*"
                    else:
                        llm_response_text = f"I'm sorry, I couldn't retrieve weather data. {function_result.get('error', 'Please check your API key configuration.')}"
                
                # NEWS CHECK - PRIORITY 2
                elif any(word in user_lower for word in ["news", "headlines", "current events"]):
                    logging.info("Detected NEWS request")
                    topic = "general"
                    if "technology" in user_lower or "tech" in user_lower:
                        topic = "technology"
                    elif "sports" in user_lower:
                        topic = "sports"
                    
                    function_result = get_news_with_fallback(topic, session_id)
                    llm_response_text = f"Here are the latest {function_result['topic']} news headlines:\n\n"
                    
                    for i, article in enumerate(function_result['articles'][:3], 1):
                        llm_response_text += f"{i}. **{article['headline']}**\n   {article['summary']}\n   Published: {article['published']}\n\n"
                    
                    llm_response_text += f"Source: {function_result['source']} | Retrieved: {function_result['retrieved_at']}"
                
                # SEARCH CHECK - PRIORITY 3
                elif any(word in user_lower for word in ["search", "find", "look up", "information about"]):
                    logging.info("Detected SEARCH request")
                    search_query = user_transcript
                    if "search for" in user_lower:
                        search_query = user_transcript.split("search for", 1)[1].strip()
                    elif "find" in user_lower and "about" in user_lower:
                        search_query = user_transcript.split("about", 1)[1].strip()
                    
                    function_result = search_web_with_fallback(search_query, session_id)
                    llm_response_text = f"I searched for '{function_result['query']}' and found:\n\n{function_result['answer']}\n\nRelevant results:\n"
                    
                    for i, result in enumerate(function_result['results'][:3], 1):
                        llm_response_text += f"{i}. **{result['title']}**\n   {result['snippet']}\n\n"
                    
                    llm_response_text += f"Source: {function_result['source']}"
                
                # SYSTEM CHECK - PRIORITY 4
                elif any(word in user_lower for word in ["system", "computer", "memory", "disk", "performance"]):
                    logging.info("Detected SYSTEM request")
                    function_result = get_system_info()
                    llm_response_text = f"Here's your system information:\n\n"
                    llm_response_text += f"🖥️ **System:** {function_result.get('system', 'Unknown')}\n"
                    llm_response_text += f"💾 **Platform:** {function_result.get('platform', 'Unknown')}\n"
                    llm_response_text += f"🧠 **Memory Usage:** {function_result.get('memory_usage', 'N/A')}\n"
                    llm_response_text += f"💽 **Disk Usage:** {function_result.get('disk_usage', 'N/A')}\n\n"
                    llm_response_text += "Need more detailed system monitoring?"
                
                # TIME CHECK - PRIORITY 5
                elif any(word in user_lower for word in ["time", "clock", "date", "today", "day"]):
                    logging.info("Detected TIME request")
                    function_result = get_current_time()
                    llm_response_text = f"🕐 Current time: **{function_result['current_time']}**\n"
                    llm_response_text += f"📅 Date: **{function_result['current_date']}** ({function_result['day_of_week']})\n"
                    llm_response_text += f"🌍 Timezone: {function_result['timezone']}"
                
                else:
                    logging.info("Detected GENERAL CHAT request")
                    if model and gemini_key:
                        response = model.generate_content(
                            history,
                            generation_config={
                                "temperature": 0.7,
                                "top_p": 0.8,
                                "max_output_tokens": 2048,
                            }
                        )
                        llm_response_text = response.text or "I'm here to help! You can ask me about weather, news, web search, time, or system info."
                    else:
                        llm_response_text = "I'm here to help! Configure your Gemini API key in settings for enhanced conversational abilities, or ask me about time, system info, weather, news, or search."

                # Add final response to history
                history.append({"role": "model", "parts": [{"text": llm_response_text}]})
                
                # Update session data
                chat_histories[session_id] = history
                metadata["total_messages"] += 1
                session_metadata[session_id] = metadata

                # Send response to client
                await websocket.send_text(json.dumps({
                    "type": "llm_response",
                    "text": llm_response_text,
                    "persona": persona,
                    "message_count": metadata["total_messages"],
                    "has_functions": function_result is not None,
                    "function_used": function_result is not None,
                    "api_keys_status": {
                        "gemini": bool(api_keys["gemini"]),
                        "openweather": bool(api_keys["openweather"]),
                        "tavily": bool(api_keys["tavily"])
                    }
                }))
                
                logging.info(f"Enhanced response sent for {session_id} - Function used: {function_result is not None}")

            except Exception as llm_error:
                logging.error(f"LLM generation error: {llm_error}")
                error_response = "I'm experiencing some technical difficulties. Please check your API key configuration in settings."
                await websocket.send_text(json.dumps({
                    "type": "llm_response",
                    "text": error_response,
                    "persona": persona,
                    "error": True
                }))

            # TTS handling with browser fallback
            try:
                await websocket.send_text(json.dumps({
                    "type": "audio_end",
                    "source": "browser_tts_fallback",
                    "message": "Using browser voice"
                }))
            except Exception as tts_error:
                logging.warning(f"TTS indication failed: {tts_error}")

        except Exception as pipeline_error:
            logging.error(f"Pipeline error: {pipeline_error}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "System error occurred. Please try again.",
                "error_details": str(pipeline_error)
            }))

    def extract_location_from_text(text: str) -> str:
        """Extract location from user input, defaulting to a common location"""
        text_lower = text.lower()
        
        city_indicators = ["in ", "for ", "at ", "weather in ", "weather for ", "temperature in "]
        
        for indicator in city_indicators:
            if indicator in text_lower:
                location_part = text.split(indicator, 1)[1].strip()
                location = location_part.split()[0] if location_part.split() else "London"
                return location.title()
        
        return "London"

    # WebSocket message handling
    try:
        while True:
            raw_message = await websocket.receive_text()
            data = json.loads(raw_message)

            if data.get("type") == "persona":
                new_persona = data.get("persona", "default")
                session_personas[session_id] = new_persona
                logging.info(f"Persona updated: {new_persona}")
                
                await websocket.send_text(json.dumps({
                    "type": "persona_updated",
                    "new_persona": new_persona
                }))

            elif data.get("type") == "user_transcript":
                transcript = (data.get("text") or "").strip()
                logging.info(f"[{session_id}] Enhanced transcript: '{transcript}'")
                
                if not transcript or len(transcript) < 2:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "I didn't catch that. Please speak more clearly."
                    }))
                    continue
                
                await websocket.send_text(json.dumps({"type": "ack_transcript"}))
                await websocket.send_text(json.dumps({"type": "final", "text": transcript}))
                
                await run_complete_pipeline(transcript)

    except WebSocketDisconnect:
        logging.info(f"WebSocket disconnected: {session_id}")
    except Exception as ws_error:
        logging.error(f"WebSocket error: {ws_error}")
    finally:
        # Cleanup
        if session_id in chat_histories:
            del chat_histories[session_id]
        if session_id in session_personas:
            del session_personas[session_id]
        if session_id in session_metadata:
            del session_metadata[session_id]
        if session_id in session_api_keys:
            del session_api_keys[session_id]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "version": "2.0.0",
        "features": ["weather", "news", "search", "time", "system", "chat"],
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
