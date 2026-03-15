from app.ern.builder.xml_utils import sub

def build_party_list(parent, parties, registry, ns):
    pl = sub(parent, "PartyList", ns=ns)

    for party in parties.values():
        p = sub(pl, "Party", ns=ns)
        ref = registry.party_ref(party.internal_id)

        sub(p, "PartyReference", ref, ns=ns)
        sub(p, "PartyName", party.name, ns=ns)

        # PIE-Ready Identifiers
        if hasattr(party, 'identifiers') and party.identifiers:
            for ident in party.identifiers:
                pid = sub(p, "PartyId", ns=ns)
                sub(pid, "ProprietaryId", ident.value, Namespace=ident.namespace, ns=ns)
        elif getattr(party, 'party_id', None):
            pid = sub(p, "PartyId", ns=ns)
            sub(pid, "ProprietaryId", party.party_id, ns=ns)
