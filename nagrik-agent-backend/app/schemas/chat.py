"""
Request/response contracts for the /chat family of endpoints.
`language` and `attachments` are present from day one so we never need to
refactor state later when voice/image support is wired in.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Attachment(BaseModel):
    type: Literal["image", "document", "audio"]
    url: Optional[str] = None
    base64_data: Optional[str] = None
    mime_type: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    citizen_id: str

    message: Optional[str] = Field(
            default=None,
            description="Text message. Omit if only attachments are sent."
        )

    language: Optional[str] = Field(
            default=None,
            description="Optional language override. If omitted, language is detected automatically."
        )

    audio_base64: Optional[str] = Field(
            default=None,   
            description="Base64 encoded audio for voice chat."
        )
        
    attachments: list[Attachment] = Field(default_factory=list)

class NavigationAction(BaseModel):
    action: Literal[
        "open_scheme_page", "open_comparison", "open_application_form",
        "open_complaint_status", "open_profile", "none"
    ]
    target_id: Optional[str] = None
    params: dict = Field(default_factory=dict)


class ChatSource(BaseModel):
    scheme: Optional[str] = None
    ministry: Optional[str] = None
    department: Optional[str] = None
    source_file: Optional[str] = None
    source_url: Optional[str] = None
    page: Optional[int] = None
    snippet: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    reply_text: str
    reply_audio_base64: Optional[str] = None
    transcribed_text: Optional[str] = None
    language: str = "en"
    intent: Optional[str] = None
    navigation: Optional[NavigationAction] = None
    tool_calls_made: list[str] = Field(default_factory=list)
    sources: list[ChatSource] = Field(default_factory=list)
    extracted_fields: dict = Field(default_factory=dict)