from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import subprocess
import logging

# Import the new services and schemas
from services import stt, llm, tts
from schemas import ChatResponse, ErrorResponse

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FastAPI App Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Directory and Path Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# --- In-Memory Datastore for Chat History ---
chat_histories = {}


# --- HTML Frontend Endpoint ---
@app.get("/", response_class=FileResponse)
async def read_index():
    """Serves the index.html file as the main page."""
    return "index.html"


# --- Conversational Agent Endpoint (from previous days) ---
# This endpoint will not be used today, but we'll keep it for later.
@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str, file: UploadFile = File(...)):
    # ... (existing logic from Day 14) ...
    pass


# ==============================================================================
# --- 🚀 Day 16: Streaming WebSocket Endpoint 🚀 ---
# ==============================================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    This WebSocket endpoint handles streaming audio data from the client.
    It receives audio chunks and saves them to a single file.
    """
    await websocket.accept()
    logging.info("WebSocket connection established for audio streaming.")
    
    # Generate a unique filename for this streaming session
    file_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}.webm")
    
    try:
        # Open the file in append-binary mode
        with open(save_path, "ab") as f:
            while True:
                # Receive binary audio data from the client
                data = await websocket.receive_bytes()
                # Write the received audio chunk to the file
                f.write(data)
                
    except WebSocketDisconnect:
        logging.info(f"WebSocket connection closed. Audio saved to {save_path}")
    except Exception as e:
        logging.error(f"An error occurred in the WebSocket: {e}")
