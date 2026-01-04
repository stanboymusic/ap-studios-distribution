export interface Artist {
  id: string;
  name: string;
  type: string;
}

export interface Release {
  id: string;
  title: string;
  type: string;
  status: string;
}

export type WizardStatus = "draft" | "invalid" | "valid" | "ready";

export interface ReleaseDraft {
  id: string;
  status: WizardStatus;
  owner_party: {
    party_name: string;
    dpid: string;
  };
  ern: {
    version: "4.2" | "4.3";
    profile: "AudioAlbum" | "AudioSingle";
  };
  ddex: {
    standard: "ERN";
    message_version: "4.3.1";
    release_profile: "SimpleAudioSingle";
    message_type: "NewReleaseMessage";
  };
  artist?: {
    display_name: string;
    country: string;
    primary_language: string;
    is_rights_holder: boolean;
  };
  release?: {
    title: { text: string; language: string };
    parental_advisory: "None" | "Explicit" | "Clean";
    genres: { primary: string; secondary?: string };
  };
  tracks?: any[];
  artwork?: any;
  deals?: any;
  validation?: any;
}

export interface DeliveryEvent {
  event_type: string;
  dsp: string;
  message: string;
  created_at: string;
}