from uuid import UUID, uuid4
from datetime import datetime, date
from typing import List, Optional

class ReleaseDraft:
    def __init__(self):
        self.id: UUID = uuid4()
        self.release_id: UUID = self.id
        self.status: str = "CREATED"
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
        self.artist_id: Optional[UUID] = None
        self.owner_user_id: Optional[str] = None
        self.artwork_id: Optional[UUID] = None
        self.track_ids: List[UUID] = []
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
            "warnings": [],
            "history": []
        }
        self.featuring_artists: Optional[List[str]] = None
        self.producer: Optional[str] = None
        self.composer: Optional[str] = None
        self.remixer: Optional[str] = None
        self.genre: Optional[str] = None
        self.subgenre: Optional[str] = None
        self.label_name: Optional[str] = None
        self.c_line: Optional[str] = None
        self.p_line: Optional[str] = None
        self.meta_language: Optional[str] = None
        self.product_version: Optional[str] = None
        self.product_code: Optional[str] = None
        self.sale_date: Optional[str] = None
        self.preorder_date: Optional[str] = None
        self.preorder_previewable: bool = False
        self.excluded_territories: Optional[List[str]] = None
        self.album_price: Optional[str] = None
        self.track_price: Optional[str] = None
        self.publishing: Optional[List[dict]] = None
        self.delivery = {
            "status": "not_delivered",  # not_delivered, uploading, uploaded, processing, accepted, rejected
            "connector_id": None,
            "delivered_at": None,
            "dsp_status": None,
            "dsp_issues": []
        }

    def to_dict(self):
        data = self.__dict__.copy()
        data["id"] = str(self.id)
        data["release_id"] = str(self.release_id)
        if self.artist_id:
            data["artist_id"] = str(self.artist_id)
        if self.owner_user_id:
            data["owner_user_id"] = self.owner_user_id
        if self.artwork_id:
            data["artwork_id"] = str(self.artwork_id)
        data["track_ids"] = [str(tid) for tid in self.track_ids]
        
        if hasattr(self.release_type, "value"):
            data["release_type"] = self.release_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict):
        instance = cls()
        for key, value in data.items():
            if key in ["id", "release_id", "artist_id", "artwork_id"]:
                if value:
                    setattr(instance, key, UUID(value))
            elif key == "track_ids":
                setattr(instance, key, [UUID(tid) for tid in value])
            elif key == "original_release_date" and value:
                if isinstance(value, str):
                    setattr(instance, key, date.fromisoformat(value))
                else:
                    setattr(instance, key, value)
            else:
                setattr(instance, key, value)
        return instance
