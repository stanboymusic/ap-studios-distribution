import React, { createContext, useReducer } from "react";
import { wizardReducer } from "./wizardReducer";
import { ReleaseDraft } from "../types";

export const WizardContext = createContext<any>(null);

const initialDraft: ReleaseDraft = {
  id: crypto.randomUUID(),
  status: "draft",
  owner_party: {
    party_name: "AP Studios",
    dpid: "PA-DPIDA-202402050E-4",
  },
  ern: {
    version: "4.3",
    profile: "AudioAlbum",
  },
  ddex: {
    standard: "ERN",
    message_version: "4.3.1",
    release_profile: "SimpleAudioSingle",
    message_type: "NewReleaseMessage",
  },
};

export const WizardProvider: React.FC<{ children: any }> = ({ children }) => {
  const [state, dispatch] = useReducer(wizardReducer, initialDraft);
  return (
    <WizardContext.Provider value={{ state, dispatch }}>
      {children}
    </WizardContext.Provider>
  );
};