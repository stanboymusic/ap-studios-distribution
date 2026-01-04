from pydantic import BaseModel
from datetime import datetime

class PartyInfo(BaseModel):
    party_id: str
    name: str

class MessageInfo(BaseModel):
    thread_id: str
    message_id: str
    created_at: datetime
    update_indicator: str = "OriginalMessage"

class ErnContext(BaseModel):
    version: str = "4.3"
    profile: str = "AudioAlbum"
    language: str = "en"
    message_id: str
    sender: PartyInfo
    recipient: PartyInfo
    graph_fingerprint: str