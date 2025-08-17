from pydantic import BaseModel
from typing import Optional

# Pydantic models define the data structures for your API.
# This helps with validation, documentation, and editor support.

class ChatResponse(BaseModel):
    is_error: bool
    user_transcript: str
    llm_response: str
    audio_url: str

class ErrorResponse(BaseModel):
    is_error: bool
    error_message: str
    audio_url: Optional[str] = None
