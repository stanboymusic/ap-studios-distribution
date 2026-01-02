from app.ern.builder.xml_utils import sub

def build_release_list(parent, releases, registry):
    rl = sub(parent, "ReleaseList")

    for r in releases.values():
        rel = sub(rl, "Release")
        ref = registry.release_ref(r.internal_id)

        sub(rel, "ReleaseReference", ref)

        sub(rel, "ReleaseType", "Album")
        title = sub(rel, "ReferenceTitle")
        sub(title, "TitleText", r.title)

        sub(rel, "OriginalReleaseDate", r.original_release_date)

        for res_id in r.resources:
            sub(rel, "ReleaseResourceReference",
                registry.resource_ref(res_id))