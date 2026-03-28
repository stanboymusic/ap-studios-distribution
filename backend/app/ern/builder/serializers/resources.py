from app.ern.builder.xml_utils import sub
from app.ern.builder.serializers.tracks import validate_isrc_for_ern

def build_resource_list(parent, resources, registry, ns):
    rl = sub(parent, "ResourceList", ns=ns)

    for r in resources.values():
        if r.type == "SoundRecording":
            sr = sub(rl, "SoundRecording", ns=ns)
            ref = registry.resource_ref(r.internal_id)

            sub(sr, "ResourceReference", ref, ns=ns)
            
            sr_id = sub(sr, "SoundRecordingId", ns=ns)
            validated_isrc = validate_isrc_for_ern(r.isrc, r.title)
            sub(sr_id, "ISRC", validated_isrc, ns=ns)

            sub(sr, "SoundRecordingType", "MusicalWorkSoundRecording", ns=ns)
            sub(sr, "Duration", f"PT{r.duration_seconds}S", ns=ns)

            title = sub(sr, "ReferenceTitle", ns=ns)
            sub(title, "TitleText", r.title, ns=ns)

            file_el = sub(sr, "File", ns=ns)
            sub(file_el, "FileName", f"resources/audio/{r.file}", ns=ns)

            # Add Rights Controllers if available
            if r.rights and "shares" in r.rights:
                for share in r.rights["shares"]:
                    rc = sub(sr, "SoundRecordingRightsController", ns=ns)
                    sub(rc, "PartyReference", registry.party_ref(share["party_id"]), ns=ns)
                    sub(rc, "RightsControllerRole", share.get("role", "RightsOwner"), ns=ns)
                    sub(rc, "RightSharePercentage", str(share["percentage"]), ns=ns)
            
        elif r.type == "Image":
            img = sub(rl, "Image", ns=ns)
            ref = registry.resource_ref(r.internal_id)
            
            sub(img, "ResourceReference", ref, ns=ns)
            
            img_id = sub(img, "ImageId", ns=ns)
            sub(img_id, "ProprietaryId", r.internal_id, Namespace="DPID:AP-STUDIOS", ns=ns)
            
            sub(img, "ImageType", "FrontCoverImage", ns=ns)
            
            file_el = sub(img, "File", ns=ns)
            sub(file_el, "FileName", f"resources/images/{r.file}", ns=ns)
