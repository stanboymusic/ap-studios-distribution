from app.ern.builder.xml_utils import sub

def build_deal_list(parent, deals, registry, ns):
    dl = sub(parent, "DealList", ns=ns)

    for d in deals.values():
        deal = sub(dl, "Deal", ns=ns)
        
        sub(deal, "DealReleaseReference",
            registry.release_ref(d.release), ns=ns)

        deal_terms = sub(deal, "DealTerms", ns=ns)

        for t in d.territories:
            sub(deal_terms, "TerritoryCode", t, ns=ns)

        val_period = sub(deal_terms, "ValidityPeriod", ns=ns)
        sub(val_period, "StartDate", d.start_date, ns=ns)

        for cm in d.commercial_models:
            sub(deal_terms, "CommercialModelType", cm.model, ns=ns)
            sub(deal_terms, "UsageType", cm.use_type, ns=ns)