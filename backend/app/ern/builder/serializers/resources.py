from app.ern.builder.xml_utils import sub

def build_resource_list(parent, resources, registry):
    rl = sub(parent, "ResourceList")

    for r in resources.values():
        sr = sub(rl, "SoundRecording")
        ref = registry.resource_ref(r.internal_id)

        sub(sr, "ResourceReference", ref)
        sub(sr, "Isrc", r.isrc)
        sub(sr, "Duration", f"PT{r.duration_seconds}S")

        title = sub(sr, "ReferenceTitle")
        sub(title, "TitleText", r.title)