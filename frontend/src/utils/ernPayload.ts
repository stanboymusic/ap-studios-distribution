import { ReleaseDraft } from "../types";

export function buildErnPayload(state: ReleaseDraft) {
  const releaseDate = state.release?.original_release_date || state.sale_date || "2026-01-01";

  const payload: any = {
    ern: {
      version: state.ern?.version || "4.3",
      profile: state.ern?.profile || "AudioAlbum",
      message_id: `msg-${Date.now()}`,
      sender: { party_id: state.owner_party.dpid, name: state.label_name || state.owner_party.party_name },
      recipient: { party_id: "DPID-RECIPIENT", name: "Recipient DSP" },
    },
    parties: {
      "party-artist": {
        display_name: state.artist?.display_name || "Unknown Artist",
        country: state.artist?.country || "US",
        primary_language: state.artist?.primary_language || "en",
        is_rights_holder: state.artist?.is_rights_holder || true,
      },
      "party-sender": {
        display_name: state.label_name || state.owner_party.party_name,
        party_id: state.owner_party.dpid,
        role: "RightsController",
      },
    },
    resources: {},
    releases: {
      "release-main": {
        title: state.release?.title.text || "Untitled",
        release_type: state.release?.release_type || "Single",
        artist: "party-artist",
        genres: { primary: state.genre || "Pop", secondary: state.subgenre || undefined },
        release_date: releaseDate,
        upc: state.release?.upc || "123456789012",
        label_name: state.label_name || state.owner_party.party_name,
        c_line: state.c_line,
        p_line: state.p_line,
        meta_language: state.meta_language,
        product_version: state.product_version,
        product_code: state.product_code,
        sale_date: state.sale_date || releaseDate,
        preorder_date: state.preorder_date,
        preorder_previewable: state.preorder_previewable || false,
        excluded_territories: state.excluded_territories || [],
        album_price: state.album_price,
        track_price: state.track_price,
        featuring_artists: state.featuring_artists || [],
        producer: state.producer,
        composer: state.composer,
        remixer: state.remixer,
        publishing: state.publishing || [],
      },
    },
    deals: {
      "deal-main": {
        release: "release-main",
        territories: ["Worldwide"],
        startDate: releaseDate,
        commercialModels: [{ model: "SubscriptionModel", use_type: "Stream" }],
      },
    },
  };

  if (state.tracks) {
    state.tracks.forEach((track: any, index: number) => {
      const trackId = track.track_id || track.id || `track-${index + 1}`;
      const publishing = (state.publishing || []).find((p: any) => p.track_id === trackId);
      payload.resources[`resource-track-${index}`] = {
        track_id: trackId,
        title: track.title,
        isrc: track.isrc || `US-ABC-${index.toString().padStart(2, "0")}`,
        duration_seconds: track.duration_seconds || track.duration || 180,
        type: "SoundRecording",
        artists: ["party-artist"],
        file: track.file_path ? track.file_path.split("/").pop() : `track-${index}.wav`,
        featuring_artists: state.featuring_artists || [],
        producer: state.producer,
        composer: state.composer,
        remixer: state.remixer,
        publishing,
      };
    });

    payload.releases["release-main"].tracks = Object.keys(payload.resources);
  }

  return payload;
}