# ===== Data Models =====
from pydantic import BaseModel, Field


from datetime import datetime
from typing import Any, Dict, List, Optional


class DataHandle(BaseModel):
    """Lightweight handle for stored data"""

    data_handle: str = Field(description="Unique identifier for the data")
    session_id: str = Field(description="Session this data belongs to")
    data_type: str = Field(description="Type of data stored")
    location: Optional[str] = Field(
        default=None, description="Geographic location if applicable"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(description="When this handle expires")
    file_path: str = Field(description="Path to the JSON file storing the data")
    summary: Dict[str, Any] = Field(
        description="Summary statistics about the data"
    )
    schema: Dict[str, str] = Field(
        description="Schema of the stored data", alias="schema"
    )


class SessionInfo(BaseModel):
    """Session management information"""

    session_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime
    data_handles: List[str] = Field(default_factory=list)
    # --- NEW FIELDS FOR AUTH ---
    user_id: Optional[str] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None