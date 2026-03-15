from fastapi import APIRouter, HTTPException
from app.schemas.rights import RightsConfigurationCreate
from app.models.rights import RightsConfiguration, RightsShare
from app.services.rights_engine import validate_rights_configuration, RightsValidationError
from app.services.rights_store import RightsStore
from fastapi import Request

router = APIRouter(prefix="/rights", tags=["Rights"])

def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or "default"

@router.get("/configurations")
def list_rights_configurations(request: Request):
    tenant_id = _tenant_id(request)
    return [c.model_dump() for c in RightsStore.list_configurations(tenant_id)]

@router.post("/configurations")
def create_rights_configuration(payload: RightsConfigurationCreate, request: Request):
    tenant_id = _tenant_id(request)
    config = RightsConfiguration(
        scope=payload.scope,
        release_id=payload.release_id,
        track_id=payload.track_id
    )

    for s in payload.shares:
        config.shares.append(
            RightsShare(
                party_reference=s.party_reference,
                rights_type=s.rights_type,
                usage_types=s.usage_types,
                territories=s.territories,
                share_percentage=s.share_percentage,
                valid_from=s.valid_from,
                valid_to=s.valid_to
            )
        )

    try:
        validate_rights_configuration(config)
    except RightsValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    RightsStore.save_configuration(config, tenant_id=tenant_id)

    return {
        "id": config.id,
        "status": "VALID",
        "shares": len(config.shares)
    }
