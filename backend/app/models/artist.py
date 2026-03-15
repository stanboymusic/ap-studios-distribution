from uuid import UUID, uuid4

class Artist:
    def __init__(self, name: str, type: str, id: UUID = None, grid: str | None = None):
        self.id: UUID = id or uuid4()
        self.name = name
        self.type = type
        self.grid = (grid or "").strip() or None

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type,
            "grid": self.grid,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            type=data["type"],
            grid=data.get("grid"),
        )
