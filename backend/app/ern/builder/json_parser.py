import hashlib
import json
from uuid import UUID
from app.ern.models.context import ErnContext
from app.ern.models.party import Party
from app.ern.models.resource import Resource
from app.ern.models.release import Release
from app.ern.models.deal import Deal
from app.models.rights import RightsConfiguration, RightsShare
from app.services.deal_engine import resolve_deals

class ErnJsonParser:

    def parse(self, payload: dict):
        # Calculate graph fingerprint
        graph_fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        ern_data = payload.get("ern", {}).copy()
        ern_data["graph_fingerprint"] = graph_fingerprint
        
        # Filter to only allowed fields for ErnContext model
        allowed_context_fields = {'version', 'profile', 'language', 'message_id', 'sender', 'recipient', 'graph_fingerprint'}
        filtered_ern_data = {key: value for key, value in ern_data.items() if key in allowed_context_fields}
        context = ErnContext(**filtered_ern_data)

        parties = {}
        for k, v in payload.get("parties", {}).items():
            party_data = v.copy()
            allowed_party_fields = {'name', 'display_name', 'party_id', 'roles', 'identifiers', 'type'}
            filtered_party_data = {key: value for key, value in party_data.items() if key in allowed_party_fields}
            parties[k] = Party(**filtered_party_data)

        resources = {}
        resource_track_id_map = {}
        for k, v in payload.get("resources", {}).items():
            res_data = v.copy()
            if 'duration_seconds' in res_data and res_data['duration_seconds'] is not None:
                res_data['duration_seconds'] = int(float(res_data['duration_seconds']))
            
            allowed_res_fields = {'type', 'title', 'duration_seconds', 'isrc', 'file', 'artists', 'territories', 'rights'}
            filtered_res_data = {key: value for key, value in res_data.items() if key in allowed_res_fields}
            resources[k] = Resource(internal_id=k, **filtered_res_data)
            
            if res_data.get("track_id"):
                resource_track_id_map[UUID(res_data["track_id"])] = k

        releases = {}
        for k, v in payload.get("releases", {}).items():
            release_data = v.copy()
            # Map alternate key if frontend uses release_upc instead of upc.
            if "release_upc" in release_data and "upc" not in release_data:
                release_data["upc"] = release_data["release_upc"]
            release_data['type'] = release_data.pop('release_type', '')
            release_data['original_release_date'] = release_data.pop('release_date', '')
            release_data['display_artists'] = [release_data.pop('artist', '')]
            release_data['resources'] = release_data.pop('tracks', [])
            release_data['label'] = 'AP Studios'
            allowed_fields = {
                'type',
                'title',
                'upc',
                'original_release_date',
                'resources',
                'display_artists',
                'label',
                'rights',
            }
            release_data = {key: value for key, value in release_data.items() if key in allowed_fields}
            releases[k] = Release(internal_id=k, **release_data)

        # Resolve deals from rights
        rights_configs = []
        rights_payload = payload.get("rights")
        if rights_payload:
            release_id = (payload.get("release_id") or "").strip()
            if release_id:
                rc = RightsConfiguration(
                    scope=rights_payload.get("scope", "release"),
                    release_id=UUID(release_id),
                    track_id=UUID(rights_payload["track_id"]) if rights_payload.get("track_id") else None
                )
                for s in rights_payload.get("shares", []):
                    # Robust mapping from frontend CamelCase or snake_case
                    share_data = {
                        "party_reference": s.get("party_reference") or s.get("partyReference"),
                        "rights_type": s.get("rights_type") or s.get("rightsType"),
                        "usage_types": s.get("usage_types") or s.get("usageTypes"),
                        "territories": s.get("territories"),
                        "share_percentage": s.get("share_percentage") or s.get("sharePercentage"),
                        "valid_from": s.get("valid_from") or s.get("validFrom"),
                        "valid_to": s.get("valid_to") or s.get("validTo")
                    }
                    rc.shares.append(RightsShare(**share_data))
                rights_configs.append(rc)

        release_ref = list(releases.keys())[0] if releases else "R1"
        deals_list = resolve_deals(rights_configs, release_ref, resource_track_id_map)
        deals = {d.deal_reference: d for d in deals_list}

        return {
            "context": context,
            "parties": parties,
            "resources": resources,
            "releases": releases,
            "deals": deals
        }
