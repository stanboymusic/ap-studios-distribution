import React, { createContext, useContext, useEffect, useMemo, useReducer, useState } from "react";
import { wizardReducer } from "./wizardReducer";
import { ReleaseDraft } from "../types";

export const WizardContext = createContext<any>(null);

const releaseId = crypto.randomUUID();

const initialDraft: ReleaseDraft = {
  id: releaseId,
  status: "draft",
  owner_party: { party_name: "AP Studios", dpid: "PA-DPIDA-202402050E-4" },
  ern: { version: "4.3", profile: "AudioAlbum" },
  ddex: {
    standard: "ERN",
    message_version: "4.3.1",
    release_profile: "SimpleAudioSingle",
    message_type: "NewReleaseMessage",
  },
  rights: { scope: "release", releaseId, shares: [] },
  featuring_artists: [],
  remixer: "",
  producer: "",
  composer: "",
  genre: "",
  subgenre: "",
  label_name: "",
  c_line: "",
  p_line: "",
  meta_language: "Spanish; Castilian",
  product_version: "",
  product_code: "",
  sale_date: "",
  preorder_date: "",
  preorder_previewable: false,
  excluded_territories: [],
  album_price: "Mid/Front",
  track_price: "Mid",
  publishing: [],
};

export function useWizard() {
  const ctx = useContext(WizardContext);
  if (!ctx) throw new Error("useWizard must be used inside WizardProvider");
  return ctx;
}

export const WizardProvider: React.FC<{ children: any }> = ({ children }) => {
  const [state, dispatch] = useReducer(wizardReducer, initialDraft);
  const [showDraftBanner, setShowDraftBanner] = useState(false);
  const [savedDraftMeta, setSavedDraftMeta] = useState("");

  useEffect(() => {
    const savedDraft = localStorage.getItem("ap-studios-draft");
    if (!savedDraft) return;
    try {
      const parsed = JSON.parse(savedDraft);
      if (parsed?._saved_at) setSavedDraftMeta(parsed._saved_at);
      setShowDraftBanner(true);
    } catch {
      localStorage.removeItem("ap-studios-draft");
    }
  }, []);

  useEffect(() => {
    const draft = { ...state, _saved_at: new Date().toISOString(), _version: "1.0" };
    localStorage.setItem("ap-studios-draft", JSON.stringify(draft));
  }, [state]);

  const value = useMemo(() => ({
    state,
    dispatch,
    showDraftBanner,
    savedDraftMeta,
    continueDraft: () => {
      const savedDraft = localStorage.getItem("ap-studios-draft");
      if (!savedDraft) return setShowDraftBanner(false);
      try {
        const parsed = JSON.parse(savedDraft);
        delete parsed._saved_at;
        delete parsed._version;
        dispatch({ type: "INIT", payload: parsed });
      } catch {
        localStorage.removeItem("ap-studios-draft");
      }
      setShowDraftBanner(false);
    },
    startFresh: () => {
      localStorage.removeItem("ap-studios-draft");
      dispatch({ type: "INIT", payload: initialDraft });
      setShowDraftBanner(false);
    },
  }), [state, showDraftBanner, savedDraftMeta]);

  return <WizardContext.Provider value={value}>{children}</WizardContext.Provider>;
};