from typing import List, Dict
from uuid import UUID
from datetime import date
from app.models.rights import RightsConfiguration
from app.ern.models.deal import Deal

USAGE_MAP = {
    "Streaming": "OnDemandStream",
    "Download": "PermanentDownload",
    "Preview": "Preview"
}

def map_usage_types(usages: List[str]) -> List[str]:
    return [USAGE_MAP.get(u, u) for u in usages]

def map_territories(territories: List[str]) -> List[str]:
    if "WORLD" in territories or "Worldwide" in territories:
        return ["Worldwide"]
    return territories

def resolve_deals(
    rights_configs: List[RightsConfiguration],
    release_ref: str,
    track_ref_map: Dict[UUID, str]
) -> List[Deal]:
    deals: List[Deal] = []
    
    # In ERN, we create a Deal for each distinct rights holder/territory/usage combo
    # But for now, we follow the user's simplified approach: 1 config -> 1 Deal
    for idx, rc in enumerate(rights_configs, start=1):
        # The frontend current sends a list of shares in one configuration
        # For ERN, each share with its own usage/territory should be a Deal
        for s_idx, share in enumerate(rc.shares, start=1):
            deal = Deal(
                deal_reference=f"D-{idx}-{s_idx}",
                party_reference=share.party_reference,
                commercial_model="SubscriptionModel", # Default for now
                use_types=map_usage_types(share.usage_types),
                territory_codes=map_territories(share.territories),
                valid_from=share.valid_from.isoformat() if isinstance(share.valid_from, date) else str(share.valid_from),
                valid_to=share.valid_to.isoformat() if share.valid_to and isinstance(share.valid_to, date) else (str(share.valid_to) if share.valid_to else None),
                release_reference=release_ref,
                track_references=[]
            )
            
            if rc.scope == "track" and rc.track_id:
                ref = track_ref_map.get(rc.track_id)
                if ref:
                    deal.track_references.append(ref)
            
            deals.append(deal)
            
    return deals
