import re

from app.ern.builder.xml_utils import sub


class ERNBuildError(ValueError):
    pass


_UPC_RE = re.compile(r"^\d{12}$")
PLACEHOLDER_UPCS = {"1234567890123", "000000000000", "123456789012"}


def _get_release_field(release, key: str):
    if hasattr(release, key):
        return getattr(release, key)
    if isinstance(release, dict):
        return release.get(key)
    return None


def validate_upc_for_ern(upc: str | None, release_id: str | None = None) -> str:
    """
    Validate UPC for ERN serialization (12 digits, valid checksum).
    Returns cleaned UPC or raises ERNBuildError.
    """
    candidate = (upc or "").strip()
    if not candidate:
        raise ERNBuildError("UPC is required to build an ERN message")

    if candidate in PLACEHOLDER_UPCS:
        raise ERNBuildError(
            f"UPC '{candidate}' is a placeholder - assign a real UPC before delivery"
        )

    if not _UPC_RE.fullmatch(candidate):
        release_hint = f" for release {release_id}" if release_id else ""
        raise ERNBuildError(
            f"UPC '{candidate}'{release_hint} has invalid format "
            "(expected exactly 12 numeric digits)."
        )

    digits = [int(d) for d in candidate]
    total = sum(d * (3 if i % 2 == 1 else 1) for i, d in enumerate(digits[:11]))
    expected_check = (10 - (total % 10)) % 10
    if digits[11] != expected_check:
        release_hint = f" for release {release_id}" if release_id else ""
        raise ERNBuildError(
            f"UPC '{candidate}'{release_hint} has invalid checksum. "
            f"Expected check digit {expected_check}, got {digits[11]}."
        )

    return candidate

def build_release_list(parent, releases, registry, ns):
    rl = sub(parent, "ReleaseList", ns=ns)

    for r in releases.values():
        rel = sub(rl, "Release", ns=ns)
        ref = registry.release_ref(r.internal_id)

        sub(rel, "ReleaseReference", ref, ns=ns)
        
        rel_id = sub(rel, "ReleaseId", ns=ns)
        release_id = (
            _get_release_field(r, "id")
            or _get_release_field(r, "internal_id")
            or "unknown"
        )
        upc_raw = _get_release_field(r, "upc") or _get_release_field(r, "release_upc")
        if not upc_raw:
            raise ERNBuildError(
                f"Release {release_id} has no UPC assigned. ERN requires a valid ICPN."
            )
        upc = validate_upc_for_ern(str(upc_raw), str(release_id))
        sub(rel_id, "ICPN", upc, ns=ns)

        sub(rel, "ReleaseType", r.type, ns=ns)
        
        title = sub(rel, "Title", ns=ns)
        sub(title, "TitleText", r.title, ns=ns)

        sub(rel, "OriginalReleaseDate", r.original_release_date, ns=ns)

        # Add Rights Controllers if available
        if r.rights and "shares" in r.rights:
            for share in r.rights["shares"]:
                rc = sub(rel, "ReleaseRightsController", ns=ns)
                sub(rc, "PartyReference", registry.party_ref(share["party_id"]), ns=ns)
                sub(rc, "RightsControllerRole", share.get("role", "RightsOwner"), ns=ns)
                sub(rc, "RightSharePercentage", str(share["percentage"]), ns=ns)

        res_ref_list = sub(rel, "ReleaseResourceReferenceList", ns=ns)
        for res_id in r.resources:
            sub(res_ref_list, "ReleaseResourceReference",
                registry.resource_ref(res_id), ns=ns)
