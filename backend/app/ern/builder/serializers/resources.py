from app.ern.builder.xml_utils import sub

def build_resource_list(parent, resources, registry, ns):
    rl = sub(parent, "ResourceList", ns=ns)

    for r in resources.values():
        if r.type == "SoundRecording":
            sr = sub(rl, "SoundRecording", ns=ns)
            ref = registry.resource_ref(r.internal_id)

            sub(sr, "ResourceReference", ref, ns=ns)
            
            sr_id = sub(sr, "SoundRecordingId", ns=ns)
            sub(sr_id, "ISRC", r.isrc, ns=ns)

            sub(sr, "SoundRecordingType", "MusicalWorkSoundRecording", ns=ns)
            sub(sr, "Duration", f"PT{r.duration_seconds}S", ns=ns)

            title = sub(sr, "ReferenceTitle", ns=ns)
            sub(title, "TitleText", r.title, ns=ns)

            file_el = sub(sr, "File", ns=ns)
            sub(file_el, "FileName", f"resources/audio/{r.file}", ns=ns)
            
        elif r.type == "Image":
            img = sub(rl, "Image", ns=ns)
            ref = registry.resource_ref(r.internal_id)
            
            sub(img, "ResourceReference", ref, ns=ns)
            
            img_id = sub(img, "ImageId", ns=ns)
            sub(img_id, "ProprietaryId", r.internal_id, Namespace="DPID:AP-STUDIOS", ns=ns)
            
            sub(img, "ImageType", "FrontCoverImage", ns=ns)
            
            file_el = sub(img, "File", ns=ns)
            sub(file_el, "FileName", f"resources/images/{r.file}", ns=ns)