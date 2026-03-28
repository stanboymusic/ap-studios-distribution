import { ReleaseDraft } from "../types";

export type WizardAction =
  | { type: "INIT"; payload: ReleaseDraft }
  | { type: "UPDATE_ARTIST"; payload: any }
  | { type: "UPDATE_RELEASE"; payload: any }
  | { type: "UPDATE_ERN"; payload: any }
  | { type: "UPDATE_TRACKS"; payload: any[] }
  | { type: "UPDATE_RIGHTS"; payload: any }
  | { type: "UPDATE_VALIDATION"; payload: any }
  | { type: "SET_STATUS"; payload: any }
  | { type: "SET_ID"; payload: string }
  | { type: "SET_FIELD"; field: string; value: any };

export function wizardReducer(state: ReleaseDraft, action: WizardAction) {
  const payloadStr = 'payload' in action ? (action as any).payload : ('value' in action ? (action as any).value : '');
  console.log('[Wizard Action]', action.type, 'field' in action ? (action as any).field : '', payloadStr);
  switch (action.type) {
    case "INIT":
      return action.payload;
    case "UPDATE_ARTIST":
      return { 
        ...state, 
        artist_id: action.payload.artist_id,
        artist: { ...state.artist, ...action.payload } 
      };
    case "UPDATE_RELEASE":
      return { ...state, release: { ...state.release, ...action.payload } };
    case "UPDATE_ERN":
      return { ...state, ern: action.payload };
    case "UPDATE_TRACKS":
      return { ...state, tracks: action.payload };
    case "UPDATE_RIGHTS":
      return { ...state, rights: action.payload };
    case "UPDATE_VALIDATION":
      return { ...state, validation: action.payload };
    case "SET_STATUS":
      return { ...state, status: action.payload };
    case "SET_ID":
      return { ...state, id: action.payload };
    case "SET_FIELD":
      return { ...state, [action.field]: action.value };
    default:
      return state;
  }
}
