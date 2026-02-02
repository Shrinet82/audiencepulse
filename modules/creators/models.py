from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class Creator(BaseModel):
    """
    Persistent Identity for a Creator.
    """
    id: Optional[str] = None
    platform: str = "youtube"
    channel_id: str
    handle: Optional[str] = None
    name: str
    avatar_url: Optional[str] = None
    subscriber_count: Optional[int] = 0
    created_at: Optional[str] = None

class AnalysisRun(BaseModel):
    """
    A specific audit job run for a creator.
    """
    id: Optional[str] = None
    creator_id: str
    campaign_id: Optional[str] = None
    status: str = "pending"
    fit_score: Optional[int] = 0
    report_json: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

class CreatorCreate(BaseModel):
    """DTO for creating a new creator."""
    channel_id: str
    name: str
    handle: Optional[str] = None
    avatar_url: Optional[str] = None
    subscriber_count: Optional[int] = 0
