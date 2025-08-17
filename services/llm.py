import os
import requests
import logging
from typing import List, Dict

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_google_gemini_api_key")

if GEMINI_API_KEY == "your_google_gemini_api_key":
    logging.warning("Gemini API key is not set. Please set the GEMINI_API_KEY environment variable.")

def get_llm_response(history: List[Dict]) -> str:
    """
    Gets a response from the Gemini LLM, considering the chat history.
    """
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    # The history now correctly contains the user's latest prompt.
    payload = {"contents": history}
    headers = {"Content-Type": "application/json"}

    response = requests.post(gemini_url, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Gemini LLM Error: {response.text}")

    response_data = response.json()
    
    # Safely extract the text
    try:
        return response_data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError) as e:
        logging.error(f"Error parsing Gemini response: {response_data} - {e}")
        raise Exception("Could not parse the response from the Gemini API.")
