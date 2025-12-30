from uuid import UUID, uuid4

class Artist:
    def __init__(self, name: str, type: str):
        self.id: UUID = uuid4()
        self.name = name
        self.type = type