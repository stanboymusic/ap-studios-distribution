from lxml import etree
from datetime import date

def build_deal_list(root):
    deal_list = etree.SubElement(root, "DealList")

    release_deal = etree.SubElement(deal_list, "ReleaseDeal", DealReference="D-001")

    deal_release_ref = etree.SubElement(release_deal, "DealReleaseReference")
    etree.SubElement(deal_release_ref, "ReleaseReference").text = "R-001"

    deal_terms = etree.SubElement(release_deal, "DealTerms")
    etree.SubElement(deal_terms, "TerritoryCode").text = "Worldwide"

    validity_period = etree.SubElement(deal_terms, "ValidityPeriod")
    etree.SubElement(validity_period, "StartDate").text = date.today().isoformat()

    etree.SubElement(deal_terms, "CommercialModelType").text = "SubscriptionModel"
    etree.SubElement(deal_terms, "UseType").text = "OnDemandStream"

    return deal_list