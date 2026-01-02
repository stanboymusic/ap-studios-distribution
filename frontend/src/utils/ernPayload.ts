import { ReleaseDraft } from "../types";

export function buildErnPayload(state: ReleaseDraft) {
  const payload: any = {
    context: {
      ern_version: state.ddex.message_version,
      profile: state.ddex.release_profile,
      language: "en", // TODO: from state
      sender: {
        party_id: state.owner_party.dpid,
        name: state.owner_party.party_name
      },
      recipient: {
        party_id: "DPID-RECIPIENT", // TODO
        name: "Recipient DSP"
      },
      message: {
        thread_id: `thread-${state.id}`,
        message_id: `msg-${Date.now()}`,
        created_at: new Date().toISOString(),
        update_indicator: "OriginalMessage"
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
        release_date: "2026-01-01", // TODO: from state
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
            type: "SubscriptionModel",
            percentage: 100
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
        duration: track.duration || 180,
        resource_type: "SoundRecording",
        artists: ["party-artist"]
      };
    });

    // Update release with tracks
    payload.releases["release-main"].tracks = Object.keys(payload.resources);
  }

  // Add artwork
  if (state.artwork) {
    payload.resources["resource-artwork"] = {
      filename: state.artwork.filename || "cover.jpg",
      resource_type: "Image",
      image_type: "FrontCoverImage"
    };
  }

  return payload;
}