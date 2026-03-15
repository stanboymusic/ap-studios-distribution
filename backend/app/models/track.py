from __future__ import annotations

from uuid import UUID, uuid4


class Track:
    def __init__(
        self,
        title: str,
        artist_id: UUID | None = None,
        isrc: str | None = None,
        id: UUID | None = None,
    ):
        self.id: UUID = id or uuid4()
        self.title = title
        self.artist_id = artist_id
        self.isrc = (isrc or "").strip().upper() or None

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "title": self.title,
            "artist_id": str(self.artist_id) if self.artist_id else None,
            "isrc": self.isrc,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Track":
        artist_id = data.get("artist_id")
        return cls(
            id=UUID(data["id"]),
            title=data["title"],
            artist_id=UUID(artist_id) if artist_id else None,
            isrc=data.get("isrc"),
        )
