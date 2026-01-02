class ReferenceRegistry:
    def __init__(self):
        self.parties = {}
        self.resources = {}
        self.releases = {}
        self.deals = {}

    def party_ref(self, internal_id):
        return self.parties.setdefault(internal_id, f"P-{len(self.parties)+1}")

    def resource_ref(self, internal_id):
        return self.resources.setdefault(internal_id, f"SR-{len(self.resources)+1}")

    def release_ref(self, internal_id):
        return self.releases.setdefault(internal_id, f"R-{len(self.releases)+1}")

    def deal_ref(self, internal_id):
        return self.deals.setdefault(internal_id, f"D-{len(self.deals)+1}")