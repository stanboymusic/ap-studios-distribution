import { useContext, useMemo } from "react";
import { WizardContext } from "../app/WizardProvider";

export default function StepPreview({ onNext, onBack }: any) {
  const { state } = useContext(WizardContext);
  const publishingMap = useMemo(() => {
    const m = new Map<string, any>();
    (state.publishing || []).forEach((p: any) => m.set(p.track_id, p));
    return m;
  }, [state.publishing]);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Preview & Validate</h2>

      <div style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}>
        <div style={{ color: "#fff", fontSize: 20 }}>
          {state.release?.title?.text || "Untitled"} {state.product_version ? `· ${state.product_version}` : ""}
        </div>
        <div style={{ color: "var(--mist)" }}>{state.artist?.display_name || "Unknown Artist"}</div>
        {!!state.featuring_artists?.length && <div style={{ color: "var(--mist-d)" }}>Feat. {state.featuring_artists.join(", ")}</div>}
      </div>

      <div style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}>
        <div>Genre: {state.genre || "-"}</div>
        <div>Subgenre: {state.subgenre || "-"}</div>
        <div>Language: {state.meta_language || "-"}</div>
        <div>Label: {state.label_name || "-"}</div>
        <div>(C): {state.c_line || "-"}</div>
        <div>(P): {state.p_line || "-"}</div>
      </div>

      <div style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}>
        <div>Territories: {!state.excluded_territories?.length ? "WW" : "Custom"}</div>
        <div>Excluded: {state.excluded_territories?.join(", ") || "None"}</div>
        <div>Album Price: {state.album_price || "-"}</div>
        <div>Track Price: {state.track_price || "-"}</div>
        <div>Pre-order: {state.preorder_date || "-"}</div>
      </div>

      <div style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}>
        <h3>Tracks</h3>
        {(state.tracks || []).map((t: any, i: number) => {
          const id = t.track_id || t.id || String(i + 1);
          const pub = publishingMap.get(id);
          return (
            <div key={id} style={{ marginBottom: 8 }}>
              {i + 1}. {t.title || "Untitled"} · {t.isrc || "No ISRC"}
              <div style={{ color: "var(--mist-d)" }}>
                Producer: {state.producer || "-"} · Composer: {state.composer || "-"} · Publishing: {pub?.publishing_type || "controlled_100"}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex gap-2">
        <button onClick={onBack} className="btn-ghost">Back</button>
        <button onClick={onNext} className="btn-primary">Next: Validate</button>
      </div>
    </div>
  );
}
