from app.ern.builder.xml_utils import sub

def build_release_list(parent, releases, registry, ns):
    rl = sub(parent, "ReleaseList", ns=ns)

    for r in releases.values():
        rel = sub(rl, "Release", ns=ns)
        ref = registry.release_ref(r.internal_id)

        sub(rel, "ReleaseReference", ref, ns=ns)
        
        rel_id = sub(rel, "ReleaseId", ns=ns)
        sub(rel_id, "ICPN", "1234567890123", ns=ns) # TODO: use real UPC

        sub(rel, "ReleaseType", r.type, ns=ns)
        
        title = sub(rel, "Title", ns=ns)
        sub(title, "TitleText", r.title, ns=ns)

        sub(rel, "OriginalReleaseDate", r.original_release_date, ns=ns)

        res_ref_list = sub(rel, "ReleaseResourceReferenceList", ns=ns)
        for res_id in r.resources:
            sub(res_ref_list, "ReleaseResourceReference",
                registry.resource_ref(res_id), ns=ns)