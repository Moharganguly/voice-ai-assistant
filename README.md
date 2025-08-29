<<<<<<< HEAD
🎙️ Conversational AI Voice Agent
This project is a fully functional, voice-powered conversational agent built as part of the "30 Days of Voice Agents" challenge. It listens to user voice input, understands the context of the conversation, generates an intelligent response using a Large Language Model (LLM), and speaks the answer back in a natural-sounding voice.

✨ Features
Voice-in, Voice-out Interaction: A seamless conversational loop where the user speaks and the agent speaks back.

Real-time Transcription: Uses AssemblyAI for fast and accurate Speech-to-Text (STT).

Intelligent Responses: Powered by Google's Gemini LLM to provide context-aware and intelligent answers.

Chat History: The agent remembers previous turns in the conversation, allowing for natural, follow-up questions.

Natural Voice Output: Uses Google's Gemini Text-to-Speech (TTS) to generate a high-quality, natural-sounding voice for the agent.

Robust Error Handling: The application can gracefully handle API failures and provides fallback responses.

Modern Web Interface: A sleek, responsive UI with a single smart button and an animated chat log.

🛠️ Tech Stack & Architecture
This project uses a modern Python backend with a vanilla JavaScript frontend.

Backend: Python 3 with FastAPI

Frontend: HTML, CSS, Vanilla JavaScript

Speech-to-Text (STT): AssemblyAI API

Large Language Model (LLM): Google Gemini API

Text-to-Speech (TTS): Google Gemini API

Audio Conversion: FFMPEG

🏛️ Architecture Flow
Frontend (JS): The browser records the user's voice and sends the audio data to the backend.

Backend (FastAPI):
a. Receives the audio file.
b. Converts the audio to a compatible WAV format using FFMPEG.
c. Sends the WAV file to AssemblyAI for transcription.
d. Retrieves the chat history for the current session from an in-memory store.
e. Sends the full conversation history plus the new user transcript to the Gemini LLM.
f. Receives the text response from the LLM and updates the chat history.
g. Sends the LLM's text response to the Gemini TTS API to generate the voice output.
h. Returns a JSON object to the frontend containing the final audio URL and the transcripts.

Frontend (JS):
a. Receives the JSON response.
b. Updates the chat log with the user's and agent's messages.
c. Plays the agent's audio response, triggering the next conversational turn.

🚀 Getting Started
Follow these instructions to get a copy of the project up and running on your local machine.

Prerequisites
Python 3.8+

FFMPEG: You must have FFMPEG installed and accessible from your system's command line. You can download it from ffmpeg.org.

Installation & Setup
Clone the repository:

git clone <your-repo-url>
cd <your-repo-folder>

Install Python dependencies:

pip install -r requirements.txt

Configure Environment Variables:
You need to get API keys from the following services:

AssemblyAI

Google AI Studio (for Gemini)

Open the main.py file and replace the placeholder values with your actual keys:

ASSEMBLYAI_API_KEY = "your_assemblyai_api_key"
GEMINI_API_KEY = "your_google_gemini_api_key" 

Also, ensure the path to your FFMPEG executable is correct for your system:

FFMPEG_PATH = "C:\\ffmpeg\\bin\\ffmpeg.exe" 

Running the Application
Navigate to the project's root directory in your terminal.

Run the FastAPI server using Uvicorn:

python -m uvicorn main:app --reload

Open your web browser and go to http://127.0.0.1:8000.

You should now see the voice agent's interface, ready for a conversation!
=======
# voice-ai-assistant
Enhanced Voice AI Assistant v2.0 - Professional voice interface with real-world capabilities
>>>>>>> c3485741795d0ef61d99858486ad87542156677b
