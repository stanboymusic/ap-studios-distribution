from app.ern.builder.xml_utils import sub

def build_deal_list(parent, deals, registry, ns):
    if not deals:
        return
        
    dl = sub(parent, "DealList", ns=ns)

    for d in deals.values():
        deal = sub(dl, "Deal", ns=ns)
        
        # Reference to the Deal (D-1, etc)
        sub(deal, "DealReference", d.deal_reference, ns=ns)

        deal_terms = sub(deal, "DealTerms", ns=ns)

        # Commercial Model (SubscriptionModel, etc)
        sub(deal_terms, "CommercialModelType", d.commercial_model, ns=ns)

        # Usages (OnDemandStream, etc)
        for use in d.use_types:
            usage = sub(deal_terms, "Usage", ns=ns)
            sub(usage, "UseType", use, ns=ns)

        # Territories
        for t in d.territory_codes:
            sub(deal_terms, "TerritoryCode", t, ns=ns)

        # Validity
        val_period = sub(deal_terms, "ValidityPeriod", ns=ns)
        sub(val_period, "StartDate", d.valid_from, ns=ns)
        if d.valid_to:
            sub(val_period, "EndDate", d.valid_to, ns=ns)

        # Critical: DealPartyReference
        sub(deal, "DealPartyReference", d.party_reference, ns=ns)

        # Link to Release
        rlist = sub(deal, "ReleaseDealReferenceList", ns=ns)
        sub(rlist, "ReleaseDealReference", d.release_reference, ns=ns)

        # Link to Tracks if any
        if d.track_references:
            tlist = sub(deal, "TrackDealReferenceList", ns=ns)
            for tref in d.track_references:
                sub(tlist, "TrackDealReference", tref, ns=ns)
