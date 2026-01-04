from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Optional

class ReleaseDraft:
    def __init__(self):
        self.id: UUID = uuid4()
        self.release_id: UUID = self.id
        self.status: str = "draft"
        self.created_at: str = datetime.utcnow().isoformat()
        self.updated_at: str = datetime.utcnow().isoformat()
        self.owner_party = {
            "party_name": "AP Studios",
            "dpid": "PA-DPIDA-202402050E-4"
        }
        self.ddex = {
            "standard": "ERN",
            "message_version": "4.3.1",
            "release_profile": "SimpleAudioSingle",
            "message_type": "NewReleaseMessage"
        }
        self.artist = None
        self.release = None
        self.tracks: List = []
        self.artwork = None
        self.deals = None
        self.title = None
        self.release_type = None
        self.original_release_date = None
        self.language = "es"
        self.territories = ["Worldwide"]
        self.upc = None
        self.track_file = None
        self.isrc = None
        self.duration = None
        self.validation = {
            "last_validated_at": None,
            "ddex_status": "not_validated",
            "errors": [],
            "warnings": []
        }
        self.delivery = {
            "status": "not_delivered",  # not_delivered, uploading, uploaded, processing, accepted, rejected
            "connector_id": None,
            "delivered_at": None,
            "dsp_status": None,
            "dsp_issues": []
        }