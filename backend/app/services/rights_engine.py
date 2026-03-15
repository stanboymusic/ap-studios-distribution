from collections import defaultdict
from datetime import date
from typing import List
from ..models.rights import RightsConfiguration, RightsShare

class RightsValidationError(Exception):
    pass


def validate_rights_configuration(config: RightsConfiguration):
    buckets = defaultdict(float)

    for share in config.shares:
        for usage in share.usage_types:
            for territory in share.territories:
                key = (
                    share.rights_type,
                    usage,
                    territory,
                    share.valid_from,
                    share.valid_to
                )
                buckets[key] += share.share_percentage

    for key, total in buckets.items():
        if round(total, 2) != 100.00:
            rights_type, usage, territory, v_from, v_to = key
            msg = (
                f"Shares must sum to 100% for {rights_type} ({usage}) in {territory}. "
                f"Current total: {total}%. "
                f"Check that all collaborators cover the same territories and usage types."
            )
            raise RightsValidationError(msg)

    # Validación de solapamiento temporal
    for i, a in enumerate(config.shares):
        for b in config.shares[i + 1:]:
            if (
                a.party_reference == b.party_reference
                and a.rights_type == b.rights_type
                and set(a.usage_types) & set(b.usage_types)
                and set(a.territories) & set(b.territories)
            ):
                if dates_overlap(a.valid_from, a.valid_to, b.valid_from, b.valid_to):
                    raise RightsValidationError(
                        "Overlapping date ranges detected"
                    )


def dates_overlap(a_start, a_end, b_start, b_end):
    a_end = a_end or date.max
    b_end = b_end or date.max
    return a_start <= b_end and b_start <= a_end
