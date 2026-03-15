from __future__ import annotations

from typing import Any, Dict

from app.repositories.release_repository import update_release_status
from app.services.sftp_connector import SFTPConnector
from app.services.transport_ddex import upload_with_retry


def deliver_to_dsp(xml_path: str, dsp_config: Dict[str, Any], tenant_id: str = "default") -> Dict[str, Any]:
    connector = SFTPConnector(
        host=dsp_config["host"],
        port=int(dsp_config.get("port", 22)),
        username=dsp_config["username"],
        password=dsp_config["password"],
    )
    manifest = upload_with_retry(
        connector=connector,
        local_path=xml_path,
        remote_path=dsp_config["path"],
        retries=int(dsp_config.get("retries", 3)),
        connect_timeout_seconds=float(dsp_config.get("timeout_seconds", 3.0)),
        retry_backoff_seconds=float(dsp_config.get("retry_backoff_seconds", 1.5)),
    )

    release_id = str(dsp_config.get("release_id") or "").strip()
    if release_id:
        update_release_status(release_id, "DELIVERED", tenant_id=tenant_id)

    return manifest
