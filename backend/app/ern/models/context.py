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
    ern_version: str = "4.3"
    profile: str
    language: str
    sender: PartyInfo
    recipient: PartyInfo
    message: MessageInfo
    graph_fingerprint: str