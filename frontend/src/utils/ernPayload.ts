import { ReleaseDraft } from "../types";

export function buildErnPayload(state: ReleaseDraft) {
  const payload: any = {
    ern: {
      version: state.ern?.version || "4.3",
      profile: state.ern?.profile || "AudioAlbum",
      message_id: `msg-${Date.now()}`,
      sender: {
        party_id: state.owner_party.dpid,
        name: state.owner_party.party_name
      },
      recipient: {
        party_id: "DPID-RECIPIENT", // TODO
        name: "Recipient DSP"
      }
    },
    parties: {
      "party-artist": {
        display_name: state.artist?.display_name || "Unknown Artist",
        country: state.artist?.country || "US",
        primary_language: state.artist?.primary_language || "en",
        is_rights_holder: state.artist?.is_rights_holder || true
      },
      "party-sender": {
        display_name: state.owner_party.party_name,
        party_id: state.owner_party.dpid,
        role: "RightsController"
      }
    },
    resources: {},
    releases: {
      "release-main": {
        title: state.release?.title.text || "Untitled",
        release_type: state.ddex.release_profile,
        artist: "party-artist",
        parental_advisory: state.release?.parental_advisory || "None",
        genres: state.release?.genres || { primary: "Pop" },
        release_date: state.release?.original_release_date || "2026-01-01",
        upc: "1234567890123" // TODO
      }
    },
    deals: {
      "deal-main": {
        release: "release-main",
        territories: ["Worldwide"],
        startDate: "2026-01-01",
        commercialModels: [
          {
            model: "SubscriptionModel",
            use_type: "Stream",
          }
        ]
      }
    }
  };

  // Add tracks as resources
  if (state.tracks) {
    state.tracks.forEach((track: any, index: number) => {
      payload.resources[`resource-track-${index}`] = {
        title: track.title,
        isrc: track.isrc || `US-ABC-${index.toString().padStart(2, '0')}`,
        duration_seconds: track.duration_seconds || track.duration || 180,
        type: "SoundRecording",
        artists: ["party-artist"],
        file: track.file_path ? track.file_path.split('/').pop() : `track-${index}.wav`
      };
    });
    
    // Update release with resources
    payload.releases["release-main"].tracks = Object.keys(payload.resources);
  }

  // Add artwork
  if (state.artwork) {
    const artworkId = "resource-artwork";
    payload.resources[artworkId] = {
      file: state.artwork.filename || "cover.jpg",
      type: "Image",
      image_type: "FrontCoverImage"
    };
    
    // Add artwork to release resources
    if (!payload.releases["release-main"].tracks) {
      payload.releases["release-main"].tracks = [];
    }
    payload.releases["release-main"].tracks.push(artworkId);
  }

  return payload;
}