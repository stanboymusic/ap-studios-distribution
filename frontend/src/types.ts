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
  artist_id?: string;
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
    original_release_date?: string;
    upc?: string;
    release_type?: string;
    language?: string;
    territories?: string[];
  };
  tracks?: any[];
  artwork?: any;
  deals?: any;
  validation?: any;
  rights?: RightsDraft;
  delivery?: any;

  // Credits
  featuring_artists?: string[];
  remixer?: string;
  producer?: string;
  composer?: string;

  // Genre & Label
  genre?: string;
  subgenre?: string;
  label_name?: string;
  c_line?: string;
  p_line?: string;
  meta_language?: string;
  product_version?: string;
  product_code?: string;

  // Distribution
  sale_date?: string;
  preorder_date?: string;
  preorder_previewable?: boolean;
  excluded_territories?: string[];
  album_price?: string;
  track_price?: string;

  // Publishing
  publishing?: Array<{
    track_id: string;
    track_title: string;
    publishing_type: string;
    publisher_name: string;
  }>;
}

export interface RightsShare {
  partyReference: string;
  rightsType: string;
  usageTypes: string[];
  territories: string[];
  sharePercentage: number;
  validFrom: string;
  validTo?: string;
}

export interface RightsDraft {
  scope: "release" | "track";
  releaseId: string;
  trackId?: string;
  shares: RightsShare[];
}

export interface DeliveryEvent {
  event_type: string;
  dsp: string;
  message: string;
  created_at: string;
}
