from pydantic import BaseModel, model_validator, Field
from typing import Optional, List
from datetime import datetime

class Campaign(BaseModel):
    """
    Domain Model for a Campaign.
    Enforces rules: Name length, Description optional.
    """
    id: Optional[str] = None
    user_email: str
    name: str
    description: Optional[str] = ""
    created_at: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_name_length(self):
        if self.name and len(self.name) < 3:
            raise ValueError("Campaign name must be at least 3 characters.")
        return self

class CampaignCreate(BaseModel):
    """DTO for creating a campaign."""
    user_email: str
    name: str
    description: str = ""
