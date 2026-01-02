import { ReleaseDraft } from "../types";

export type WizardAction =
  | { type: "INIT"; payload: ReleaseDraft }
  | { type: "UPDATE_ARTIST"; payload: any }
  | { type: "UPDATE_RELEASE"; payload: any }
  | { type: "SET_STATUS"; payload: any }
  | { type: "SET_ID"; payload: string };

export function wizardReducer(state: ReleaseDraft, action: WizardAction) {
  switch (action.type) {
    case "INIT":
      return action.payload;
    case "UPDATE_ARTIST":
      return { ...state, artist: action.payload };
    case "UPDATE_RELEASE":
      return { ...state, release: action.payload };
    case "SET_STATUS":
      return { ...state, status: action.payload };
    case "SET_ID":
      return { ...state, id: action.payload };
    default:
      return state;
  }
}