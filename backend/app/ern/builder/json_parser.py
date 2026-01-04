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
        ern_data = payload["ern"].copy()
        ern_data["graph_fingerprint"] = graph_fingerprint
        
        # Filter to only allowed fields for ErnContext model
        allowed_context_fields = {'version', 'profile', 'language', 'message_id', 'sender', 'recipient', 'graph_fingerprint'}
        filtered_ern_data = {key: value for key, value in ern_data.items() if key in allowed_context_fields}
        context = ErnContext(**filtered_ern_data)

        parties = {}
        for k, v in payload.get("parties", {}).items():
            party_data = v.copy()
            party_data['name'] = party_data.pop('display_name', '')
            if 'role' in party_data:
                party_data['roles'] = [party_data.pop('role')]
            
            # Filter to only allowed fields for Party model
            allowed_party_fields = {'name', 'party_id', 'roles'}
            filtered_party_data = {key: value for key, value in party_data.items() if key in allowed_party_fields}
            parties[k] = Party(internal_id=k, **filtered_party_data)

        resources = {}
        for k, v in payload.get("resources", {}).items():
            res_data = v.copy()
            # Handle duration_seconds being float from frontend
            if 'duration_seconds' in res_data and res_data['duration_seconds'] is not None:
                res_data['duration_seconds'] = int(float(res_data['duration_seconds']))
            
            # Filter to only allowed fields for Resource model
            allowed_res_fields = {'type', 'title', 'duration_seconds', 'isrc', 'file', 'artists', 'territories'}
            filtered_res_data = {key: value for key, value in res_data.items() if key in allowed_res_fields}
            resources[k] = Resource(internal_id=k, **filtered_res_data)

        releases = {}
        for k, v in payload.get("releases", {}).items():
            release_data = v.copy()
            release_data['type'] = release_data.pop('release_type', '')
            release_data['original_release_date'] = release_data.pop('release_date', '')
            release_data['display_artists'] = [release_data.pop('artist', '')]
            release_data['resources'] = release_data.pop('tracks', [])
            release_data['label'] = 'AP Studios'  # Default label
            # Filter to only allowed fields
            allowed_fields = {'type', 'title', 'original_release_date', 'resources', 'display_artists', 'label'}
            release_data = {key: value for key, value in release_data.items() if key in allowed_fields}
            releases[k] = Release(internal_id=k, **release_data)

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