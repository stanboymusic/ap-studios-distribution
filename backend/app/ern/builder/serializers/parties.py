from app.ern.builder.xml_utils import sub

def build_party_list(parent, parties, registry):
    pl = sub(parent, "PartyList")

    for party in parties.values():
        p = sub(pl, "Party")
        ref = registry.party_ref(party.internal_id)

        sub(p, "PartyReference", ref)
        sub(p, "PartyName", party.name)

        if party.party_id:
            pid = sub(p, "PartyId")
            sub(pid, "ProprietaryId", party.party_id)