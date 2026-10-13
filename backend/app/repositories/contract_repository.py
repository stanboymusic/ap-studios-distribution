"""
File-based contract repository.
Storage: backend/storage/contracts/{tenant_id}/contracts.json
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.paths import safe_tenant_id, storage_path
from app.core.filelock import atomic_write_json, file_lock, read_json
from app.models.contract import ContractAcceptance


def _contracts_file(tenant_id: str) -> Path:
    path = storage_path("contracts", safe_tenant_id(tenant_id))
    path.mkdir(parents=True, exist_ok=True)
    return path / "contracts.json"


def _load(tenant_id: str) -> list[dict]:
    return read_json(_contracts_file(tenant_id), list)


def _save(tenant_id: str, contracts: list[dict]) -> None:
    atomic_write_json(_contracts_file(tenant_id), contracts)


def get_by_user_id(
    user_id: str, tenant_id: str
) -> Optional[ContractAcceptance]:
    for c in _load(tenant_id):
        if c.get("user_id") == user_id:
            return ContractAcceptance.from_dict(c)
    return None


def get_all(tenant_id: str) -> list[ContractAcceptance]:
    return [ContractAcceptance.from_dict(c) for c in _load(tenant_id)]


def save(contract: ContractAcceptance) -> ContractAcceptance:
    with file_lock(_contracts_file(contract.tenant_id)):
        contracts = _load(contract.tenant_id)
        # Solo un contrato por usuario — reemplazar si ya existe
        contracts = [c for c in contracts if c.get("user_id") != contract.user_id]
        contracts.append(contract.to_dict())
        _save(contract.tenant_id, contracts)
    return contract


def has_accepted(user_id: str, tenant_id: str) -> bool:
    return get_by_user_id(user_id, tenant_id) is not None
