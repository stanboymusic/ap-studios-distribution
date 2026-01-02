from app.ern.builder.xml_utils import sub

def build_deal_list(parent, deals, registry):
    dl = sub(parent, "DealList")

    for d in deals.values():
        deal = sub(dl, "Deal")
        sub(deal, "DealReference", registry.deal_ref(d.internal_id))

        sub(deal, "ReleaseReference",
            registry.release_ref(d.release))

        for t in d.territories:
            sub(deal, "TerritoryCode", t)

        sub(deal, "StartDate", d.start_date)

        for cm in d.commercial_models:
            cm_el = sub(deal, "CommercialModelType")
            sub(cm_el, "CommercialModelType", cm.model)
            sub(cm_el, "UseType", cm.use_type)