from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.config.ddex import ERNVersion, ERNProfile

class ERNParty(BaseModel):
    party_id: str
    name: str

class ERNMessage(BaseModel):
    version: ERNVersion = Field(default=ERNVersion.v43)
    profile: ERNProfile = Field(default=ERNProfile.AUDIO_ALBUM)
    message_id: str
    sender: ERNParty
    recipient: ERNParty

class ERNPayload(BaseModel):
    ern: ERNMessage
    parties: Optional[Dict[str, Any]] = {}
    resources: Optional[Dict[str, Any]] = {}
    releases: Optional[Dict[str, Any]] = {}
    deals: Optional[Dict[str, Any]] = {}