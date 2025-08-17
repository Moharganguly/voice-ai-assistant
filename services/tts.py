import os
import requests
import base64
import logging

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_google_gemini_api_key")

if GEMINI_API_KEY == "your_google_gemini_api_key":
    logging.warning("Gemini API key is not set. Please set the GEMINI_API_KEY environment variable.")

def generate_audio(text: str, output_path: str):
    """
    Generates audio for a given text using Google's Gemini TTS
    and saves it to the specified output path.
    """
    google_tts_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
    
    google_payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}}
        },
        "model": "gemini-2.5-flash-preview-tts"
    }
    
    google_res = requests.post(google_tts_url, json=google_payload)

    if google_res.status_code != 200:
        raise Exception(f"Google TTS API request failed: {google_res.text}")

    response_json = google_res.json()
    
    # Safely extract the audio data
    try:
        audio_data_base64 = response_json['candidates'][0]['content']['parts'][0]['inlineData']['data']
        audio_bytes = base64.b64decode(audio_data_base64)
        
        with open(output_path, "wb") as audio_file:
            audio_file.write(audio_bytes)
        logging.info(f"Audio content successfully saved to {output_path}")
            
    except (KeyError, IndexError) as e:
        logging.error(f"Error parsing Google TTS response: {response_json} - {e}")
        raise Exception("Could not parse audio data from the Google TTS API response.")
