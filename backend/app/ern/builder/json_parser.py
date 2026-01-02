import hashlib
import json
from app.ern.models.context import ErnContext
from app.ern.models.party import Party
from app.ern.models.resource import Resource
from app.ern.models.release import Release
from app.ern.models.deal import Deal, CommercialModel

class ErnJsonParser:

    def parse(self, payload: dict):
        # Calculate graph fingerprint
        graph_fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        context_data = payload["context"].copy()
        context_data["graph_fingerprint"] = graph_fingerprint
        context = ErnContext(**context_data)

        parties = {}
        for k, v in payload.get("parties", {}).items():
            party_data = v.copy()
            party_data['name'] = party_data.pop('display_name', '')
            if 'role' in party_data:
                party_data['roles'] = [party_data.pop('role')]
            parties[k] = Party(internal_id=k, **party_data)

        resources = {
            k: Resource(internal_id=k, **v)
            for k, v in payload.get("resources", {}).items()
        }

        releases = {
            k: Release(internal_id=k, **v)
            for k, v in payload.get("releases", {}).items()
        }

        deals = {
            k: Deal(
                internal_id=k,
                release=v["release"],
                territories=v["territories"],
                start_date=v["startDate"],
                commercial_models=[
                    CommercialModel(**cm) for cm in v["commercialModels"]
                ]
            )
            for k, v in payload.get("deals", {}).items()
        }

        return {
            "context": context,
            "parties": parties,
            "resources": resources,
            "releases": releases,
            "deals": deals
        }