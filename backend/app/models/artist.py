from uuid import UUID, uuid4


class Artist:
    def __init__(
        self,
        name: str,
        type: str,
        id: UUID = None,
        grid: str | None = None,
        owner_user_id: str | None = None,
    ):
        self.id: UUID = id or uuid4()
        self.name = name
        self.type = type
        self.grid = (grid or "").strip() or None
        # Usuario (artista) que creó este perfil. None = dato anterior a esta versión.
        self.owner_user_id = (owner_user_id or "").strip() or None

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type,
            "grid": self.grid,
            "owner_user_id": self.owner_user_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            type=data["type"],
            grid=data.get("grid"),
            owner_user_id=data.get("owner_user_id"),
        )
