import { useContext, useMemo } from 'react';
import { WizardContext } from '../app/WizardProvider';

interface Props {
  onNext: () => void;
  onBack: () => void;
}

const cardStyle: any = {
  background: 'var(--card)',
  border: '0.5px solid var(--border)',
  borderRadius: 12,
  padding: 16,
};

export default function StepPreview({ onNext, onBack }: Props) {
  const { state } = useContext(WizardContext);

  const trackPublishing = useMemo(() => {
    const map = new Map<string, any>();
    (state.publishing || []).forEach((p: any) => map.set(p.track_id, p));
    return map;
  }, [state.publishing]);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Preview & Validate</h2>

      <div style={{ ...cardStyle, display: 'grid', gridTemplateColumns: '100px 1fr', gap: 14 }}>
        <div style={{ width: 100, height: 100, borderRadius: 8, border: '0.5px solid var(--border)', background: 'rgba(255,255,255,0.04)', display: 'grid', placeItems: 'center', color: 'var(--mist-d)', fontSize: 12 }}>
          Artwork
        </div>
        <div>
          <div style={{ color: '#fff', fontSize: 20, fontFamily: 'var(--font-display)' }}>
            {state.release?.title?.text || 'Untitled'}{state.product_version ? ` · ${state.product_version}` : ''}
          </div>
          <div style={{ color: 'var(--mist)' }}>{state.artist?.display_name || 'Unknown Artist'}</div>
          {!!state.featuring_artists?.length && <div style={{ color: 'var(--mist-d)', fontSize: 13 }}>Feat. {state.featuring_artists.join(', ')}</div>}
          <div style={{ color: 'var(--mist-d)', fontSize: 13 }}>{state.release?.release_type || 'Single'} · {state.genre || 'Unspecified Genre'}</div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div style={cardStyle}>
          <div style={{ color: 'var(--mist-d)', fontSize: 12, letterSpacing: '.12em', textTransform: 'uppercase', marginBottom: 12 }}>Release Info</div>
          <div style={{ color: 'var(--mist)', fontSize: 14, lineHeight: 1.8 }}>
            <div>Genre: {state.genre || '-'}</div>
            <div>Subgenre: {state.subgenre || '-'}</div>
            <div>Language: {state.meta_language || state.release?.title?.language || '-'}</div>
            <div>Label: {state.label_name || state.owner_party?.party_name || '-'}</div>
            <div>(C): {state.c_line || '-'}</div>
            <div>(P): {state.p_line || '-'}</div>
          </div>
        </div>

        <div style={cardStyle}>
          <div style={{ color: 'var(--mist-d)', fontSize: 12, letterSpacing: '.12em', textTransform: 'uppercase', marginBottom: 12 }}>Distribution</div>
          <div style={{ color: 'var(--mist)', fontSize: 14, lineHeight: 1.8 }}>
            <div>Territories: {!state.excluded_territories?.length ? 'WW' : 'Custom'}</div>
            <div>Excluded: {state.excluded_territories?.length ? state.excluded_territories.join(', ') : 'None'}</div>
            <div>Album Price: {state.album_price || '-'}</div>
            <div>Track Price: {state.track_price || '-'}</div>
            <div>Pre-order: {state.preorder_date || '-'}</div>
          </div>
        </div>
      </div>

      <div style={cardStyle}>
        <div style={{ color: 'var(--mist-d)', fontSize: 12, letterSpacing: '.12em', textTransform: 'uppercase', marginBottom: 12 }}>Tracks</div>
        {!state.tracks?.length ? (
          <div style={{ color: 'var(--mist-d)' }}>No tracks added yet.</div>
        ) : (
          <div className="space-y-3">
            {state.tracks.map((track: any, index: number) => {
              const id = track.track_id || track.id || String(track.track_number || index + 1);
              const pub = trackPublishing.get(id);
              return (
                <div key={id} style={{ border: '0.5px solid var(--border)', borderRadius: 8, padding: 10 }}>
                  <div style={{ color: 'var(--mist)' }}>{index + 1}. {track.title || 'Untitled'} · {track.isrc || 'No ISRC'} · {Math.round(track.duration_seconds || 0)}s</div>
                  <div style={{ fontSize: 13, color: 'var(--mist-d)' }}>
                    Producer: {state.producer || '-'} · Composer: {state.composer || '-'}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--mist-d)' }}>
                    Publishing: {pub?.publishing_type || 'controlled_100'} · {pub?.publisher_name || state.label_name || 'AP Studios'}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', gap: 16, color: 'var(--mist)' }}>
        <div>UPC: {state.release?.upc || state.id?.slice(0, 12) || '-'}</div>
        <div>Release: {state.release?.original_release_date || '-'}</div>
      </div>

      <div className="flex gap-2">
        <button onClick={onBack} className="btn-ghost">Back</button>
        <button onClick={onNext} className="btn-primary">Next: Validate</button>
      </div>
    </div>
  );
}
