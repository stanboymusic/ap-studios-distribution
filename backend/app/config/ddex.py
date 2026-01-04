from enum import Enum

class ERNVersion(str, Enum):
    v42 = "4.2"
    v43 = "4.3"

class ERNProfile(str, Enum):
    AUDIO_ALBUM = "AudioAlbum"
    AUDIO_SINGLE = "AudioSingle"

ERN_CONFIG = {
    ("4.3", "AudioAlbum"): {
        "namespace": "http://ddex.net/xml/ern/43",
        "schema": "http://service.ddex.net/xml/ern/43/release-notification.xsd"
    },
    ("4.2", "AudioAlbum"): {
        "namespace": "http://ddex.net/xml/ern/42",
        "schema": "http://service.ddex.net/xml/ern/42/release-notification.xsd"
    },
    ("4.3", "AudioSingle"): {
        "namespace": "http://ddex.net/xml/ern/43",
        "schema": "http://service.ddex.net/xml/ern/43/release-notification.xsd"
    },
    ("4.2", "AudioSingle"): {
        "namespace": "http://ddex.net/xml/ern/42",
        "schema": "http://service.ddex.net/xml/ern/42/release-notification.xsd"
    }
}

AP_STUDIOS_PARTY = {
    "party_id": "PA-DPIDA-202402050E-4",
    "name": "AP Studios",
    "role": "RightsController"
}