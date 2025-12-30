from uuid import UUID, uuid4

class Release:
    def __init__(self, title: str, artist_id: UUID):
        self.id: UUID = uuid4()
        self.title = title
        self.artist_id = artist_id
        self.type = "SINGLE"
        self.status = "DRAFT"
        self.upc = None
        self.original_release_date = None