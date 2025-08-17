import os
import requests
import time
import logging

# --- Configuration ---
# It's good practice to load secrets from environment variables,
# but for this challenge, we'll define them here.
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "your_assemblyai_api_key")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "C:\\ffmpeg\\bin\\ffmpeg.exe")

if ASSEMBLYAI_API_KEY == "your_assemblyai_api_key":
    logging.warning("AssemblyAI API key is not set. Please set the ASSEMBLYAI_API_KEY environment variable.")

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes the audio file at the given path using the AssemblyAI API.
    """
    headers = {"authorization": ASSEMBLYAI_API_KEY}
    
    # 1. Upload the audio file
    with open(audio_path, 'rb') as audio_file:
        upload_response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=audio_file)
    
    if upload_response.status_code != 200:
        raise Exception(f"AssemblyAI Upload Error: {upload_response.text}")
    
    upload_url = upload_response.json()["upload_url"]
    logging.info("Audio file uploaded to AssemblyAI.")

    # 2. Request transcription
    transcript_req_data = {"audio_url": upload_url}
    transcript_req = requests.post("https://api.assemblyai.com/v2/transcript", json=transcript_req_data, headers=headers)
    
    if transcript_req.status_code != 200:
        raise Exception(f"AssemblyAI Transcription Request Error: {transcript_req.text}")
    
    transcript_id = transcript_req.json()["id"]
    logging.info(f"Transcription requested with ID: {transcript_id}")

    # 3. Poll for the result
    while True:
        status_check_res = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
        
        if status_check_res.status_code != 200:
            raise Exception(f"AssemblyAI Status Check Error: {status_check_res.text}")
        
        status_check = status_check_res.json()
        if status_check["status"] == "completed":
            return status_check["text"]
        elif status_check["status"] == "error":
            raise Exception(f"AssemblyAI Transcription Error: {status_check.get('error')}")
        
        logging.info("Transcription in progress...")
        time.sleep(2)
