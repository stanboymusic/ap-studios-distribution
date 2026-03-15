from decimal import Decimal
from typing import List, Dict
from collections import defaultdict
from app.models.dsr import SaleEvent, RevenueLineItem, Statement
from app.models.rights import RightsConfiguration, RightsShare

def calculate_payouts(
    sale: SaleEvent,
    shares: List[RightsShare]
) -> List[RevenueLineItem]:
    """
    Calculates the revenue allocation for each share in the configuration.
    """
    line_items = []
    
    # Validation: Sum of shares for the specific context must be 100%
    # This is normally done at the configuration level, but we check here for safety.
    total_percentage = sum(s.share_percentage for s in shares)
    if not (Decimal("99.9") <= Decimal(str(total_percentage)) <= Decimal("100.1")):
        # In a real system, this would go to a suspense account
        raise ValueError(f"Incomplete splits: total is {total_percentage}%")

    for share in shares:
        # amount = (gross * percentage) / 100
        amount = (sale.gross_amount * Decimal(str(share.share_percentage))) / Decimal("100")
        
        line_items.append(
            RevenueLineItem(
                sale_event_id=sale.id,
                party_reference=share.party_reference,
                role=share.rights_type,
                amount=amount.quantize(Decimal("0.000001")),
                currency=sale.currency,
                dsp=sale.dsp,
                usage_type=sale.usage_type,
                territory=sale.territory,
                period_start=sale.period_start,
                period_end=sale.period_end
            )
        )
        
    return line_items

def build_statement(
    party_reference: str,
    line_items: List[RevenueLineItem]
) -> Statement:
    """
    Aggregates line items into a financial statement for a specific party.
    """
    if not line_items:
        raise ValueError("No line items to build statement")
        
    total_amount = sum(li.amount for li in line_items)
    
    breakdown_by_dsp = defaultdict(Decimal)
    breakdown_by_usage = defaultdict(Decimal)
    
    for li in line_items:
        breakdown_by_dsp[li.dsp] += li.amount
        breakdown_by_usage[li.usage_type] += li.amount
        
    return Statement(
        party_reference=party_reference,
        period_start=min(li.period_start for li in line_items),
        period_end=max(li.period_end for li in line_items),
        total_amount=total_amount,
        currency=line_items[0].currency,
        breakdown_by_dsp=dict(breakdown_by_dsp),
        breakdown_by_usage=dict(breakdown_by_usage),
        lines=line_items
    )
