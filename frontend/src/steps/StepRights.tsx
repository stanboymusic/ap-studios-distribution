import { useContext, useState, useEffect } from "react";
import { WizardContext } from "../app/WizardProvider";
import { apiFetch } from "../api/client";
import { RightsShare } from "../types";

export default function StepRights({ onNext, onBack }: any) {
  const { state, dispatch } = useContext(WizardContext);
  const [shares, setShares] = useState<RightsShare[]>(state.rights?.shares || []);
  const [scope, setScope] = useState(state.rights?.scope || "release");
  
  // Initialize from first share if exists, otherwise defaults
  const firstShare = (state.rights?.shares && state.rights.shares.length > 0) ? state.rights.shares[0] : null;

  const [usageType, setUsageType] = useState(firstShare?.usageTypes?.[0] || "Streaming");
  const [territory, setTerritory] = useState(firstShare?.territories?.[0] || "WORLD");
  const [validFrom, setValidFrom] = useState(firstShare?.validFrom || new Date().toISOString().split('T')[0]);
  const [validTo, setValidTo] = useState(firstShare?.validTo || "");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Group by Role/Territory/Usage to match backend validation
  const buckets: Record<string, number> = {};
  shares.forEach(s => {
    const key = `${s.rightsType}`; // Simplified for UI display
    buckets[key] = (buckets[key] || 0) + s.sharePercentage;
  });

  const allBucketsValid = shares.length > 0 && Object.values(buckets).every(val => Math.abs(val - 100) < 0.01);
  const isValid = allBucketsValid;

  const total = shares.reduce((sum, s) => sum + s.sharePercentage, 0);

  // Sync changes to all shares when global settings change
  const handleUsageTypeChange = (val: string) => {
    setUsageType(val);
    setShares(shares.map(s => ({ ...s, usageTypes: [val] })));
  };

  const handleTerritoryChange = (val: string) => {
    setTerritory(val);
    setShares(shares.map(s => ({ ...s, territories: [val] })));
  };

  const handleValidFromChange = (val: string) => {
    setValidFrom(val);
    setShares(shares.map(s => ({ ...s, validFrom: val })));
  };

  const handleValidToChange = (val: string) => {
    setValidTo(val);
    setShares(shares.map(s => ({ ...s, validTo: val || undefined })));
  };

  useEffect(() => {
    if (total > 100) {
      setError("Total exceeds 100%");
    } else if (total < 100 && shares.length > 0) {
      setError("Total must equal 100%");
    } else {
      setError(null);
    }
  }, [total, shares]);

  const addShare = () => {
    // Default to the same rights type as the last share if it exists
    const lastRightsType = shares.length > 0 ? shares[shares.length - 1].rightsType : "SoundRecording";
    
    const newShare: RightsShare = {
      partyReference: "",
      rightsType: lastRightsType,
      usageTypes: [usageType],
      territories: [territory],
      sharePercentage: 0,
      validFrom: validFrom,
      validTo: validTo || undefined
    };
    setShares([...shares, newShare]);
  };

  const removeShare = (index: number) => {
    setShares(shares.filter((_, i) => i !== index));
  };

  const updateShare = (index: number, field: keyof RightsShare, value: any) => {
    const newShares = [...shares];
    newShares[index] = { ...newShares[index], [field]: value };
    setShares(newShares);
  };

  const applyPreset = (type: 'artist-100' | 'split-50-50') => {
    if (type === 'artist-100') {
      setShares([{
        partyReference: state.artist?.display_name || "Artist",
        rightsType: "SoundRecording",
        usageTypes: [usageType],
        territories: [territory],
        sharePercentage: 100,
        validFrom: validFrom,
        validTo: validTo || undefined
      }]);
    } else if (type === 'split-50-50') {
      setShares([
        {
          partyReference: state.artist?.display_name || "Artist",
          rightsType: "SoundRecording",
          usageTypes: [usageType],
          territories: [territory],
          sharePercentage: 50,
          validFrom: validFrom,
          validTo: validTo || undefined
        },
        {
          partyReference: "AP Studios",
          rightsType: "SoundRecording",
          usageTypes: [usageType],
          territories: [territory],
          sharePercentage: 50,
          validFrom: validFrom,
          validTo: validTo || undefined
        }
      ]);
    }
  };

  const save = async () => {
    if (!isValid) return;
    
    setIsSaving(true);
    setError(null);

    const rightsData = {
      scope,
      release_id: state.id,
      track_id: scope === "track" ? state.tracks?.[0]?.id : null,
      shares: shares.map(s => ({
        ...s,
        // Match backend naming if necessary, but schemas/rights.py uses party_reference
        party_reference: s.partyReference,
        rights_type: s.rightsType,
        usage_types: s.usageTypes,
        territories: s.territories,
        share_percentage: s.sharePercentage,
        valid_from: s.validFrom,
        valid_to: s.validTo || null
      }))
    };

    try {
      await apiFetch("/rights/configurations", {
        method: "POST",
        body: JSON.stringify(rightsData)
      });
      
      dispatch({
        type: "UPDATE_RIGHTS",
        payload: {
          scope,
          releaseId: state.id,
          shares
        }
      });
      onNext();
    } catch (err: any) {
      setError(err.message || "Failed to save rights configuration");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">[ Rights & Splits ]</h2>
        <div className="flex gap-2">
          <button 
            onClick={() => applyPreset('artist-100')}
            className="btn-ghost text-sm"
          >
            Artist 100%
          </button>
          <button 
            onClick={() => applyPreset('split-50-50')}
            className="btn-ghost text-sm"
          >
            Split 50/50
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, background: "var(--card)", padding: 16, borderRadius: 10, border: "0.5px solid var(--border)" }}>
        <div>
          <label htmlFor="rights-scope">
            Scope
          </label>
          <select 
            id="rights-scope"
            value={scope} 
            onChange={(e) => setScope(e.target.value)}
            className="mt-1 block w-full"
          >
            <option value="release">Release</option>
            <option value="track">Track (All)</option>
          </select>
        </div>
        <div>
          <label htmlFor="rights-territory">
            Territory
          </label>
          <select 
            id="rights-territory"
            value={territory} 
            onChange={(e) => handleTerritoryChange(e.target.value)}
            className="mt-1 block w-full"
          >
            <option value="WORLD">WORLD</option>
            <option value="US">United States</option>
            <option value="ES">Spain</option>
          </select>
        </div>
        <div>
          <label htmlFor="rights-usage">
            Usage Type
          </label>
          <select 
            id="rights-usage"
            value={usageType} 
            onChange={(e) => handleUsageTypeChange(e.target.value)}
            className="mt-1 block w-full"
          >
            <option value="Streaming">Streaming</option>
            <option value="Download">Download</option>
          </select>
        </div>
        <div>
          <label htmlFor="rights-valid-from">
            Valid From
          </label>
          <input 
            id="rights-valid-from"
            type="date" 
            value={validFrom}
            onChange={(e) => handleValidFromChange(e.target.value)}
            className="mt-1 block w-full"
          />
        </div>
        <div>
          <label htmlFor="rights-valid-to">
            Valid To (Optional)
          </label>
          <input 
            id="rights-valid-to"
            type="date" 
            value={validTo}
            onChange={(e) => handleValidToChange(e.target.value)}
            className="mt-1 block w-full"
          />
        </div>
      </div>

      <div style={{ border: "0.5px solid var(--border)", borderRadius: 10, overflow: "hidden" }}>
        <table className="w-full text-sm text-left table-dark">
          <thead>
            <tr>
              <th className="px-4 py-3 text-left font-medium uppercase" style={{ fontSize: 13, color: "var(--mist-d)" }}>Party</th>
              <th className="px-4 py-3 text-left font-medium uppercase" style={{ fontSize: 13, color: "var(--mist-d)" }}>Role</th>
              <th className="px-4 py-3 text-left font-medium uppercase" style={{ fontSize: 13, color: "var(--mist-d)" }}>% Share</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {shares.map((share, index) => (
              <tr key={index}>
                <td className="px-4 py-2">
                  <input 
                    type="text" 
                    aria-label={`Party name for share ${index + 1}`}
                    value={share.partyReference}
                    onChange={(e) => updateShare(index, 'partyReference', e.target.value)}
                    placeholder="Party Name/Ref"
                    className="w-full border-none focus:ring-0"
                    style={{ fontSize: 14, background: "transparent", color: "var(--mist)" }}
                  />
                </td>
                <td className="px-4 py-2">
                  <select 
                    aria-label={`Rights type for share ${index + 1}`}
                    value={share.rightsType}
                    onChange={(e) => updateShare(index, 'rightsType', e.target.value)}
                    className="w-full border-none focus:ring-0"
                    style={{ fontSize: 14, background: "transparent", color: "var(--mist)" }}
                  >
                    <option value="SoundRecording">SoundRecording</option>
                    <option value="MusicalWork">MusicalWork</option>
                  </select>
                </td>
                <td className="px-4 py-2">
                  <input 
                    type="number" 
                    aria-label={`Percentage share for ${index + 1}`}
                    value={share.sharePercentage}
                    onChange={(e) => updateShare(index, 'sharePercentage', parseFloat(e.target.value) || 0)}
                    className="w-20 border-none focus:ring-0 font-mono"
                    style={{ fontSize: 14, background: "transparent", color: "var(--mist)" }}
                    min="0"
                    max="100"
                  />
                </td>
                <td className="px-4 py-2 text-right">
                  <button onClick={() => removeShare(index)} className="font-bold" style={{ color: "var(--wine-ll)" }}>
                    REMOVE
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="p-2" style={{ borderTop: "0.5px solid var(--border)" }}>
          <button 
            onClick={addShare}
            className="text-sm font-medium" style={{ color: "var(--gold)", background: "none", border: "none", cursor: "pointer" }}
          >
            + Add Party
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {Object.entries(buckets).map(([role, sum]) => (
          <div key={role} className="p-4 rounded-md flex justify-between items-center" style={{
            background: Math.abs(sum - 100) < 0.01 ? "rgba(93,191,138,0.1)" : "rgba(201,169,110,0.1)",
            border: `0.5px solid ${Math.abs(sum - 100) < 0.01 ? "rgba(93,191,138,0.3)" : "rgba(201,169,110,0.3)"}`,
          }}>
            <div className="flex items-center gap-2">
              <div style={{ width: 12, height: 12, borderRadius: "50%", background: Math.abs(sum - 100) < 0.01 ? "var(--success)" : "var(--warning)" }}></div>
              <span className="font-medium" style={{ color: Math.abs(sum - 100) < 0.01 ? "var(--success)" : "var(--warning)" }}>{role} Total: {sum}%</span>
            </div>
            <span className="text-sm font-bold" style={{ color: Math.abs(sum - 100) < 0.01 ? "var(--success)" : "var(--warning)" }}>{Math.abs(sum - 100) < 0.01 ? 'VALID' : 'INCOMPLETE (Must be 100%)'}</span>
          </div>
        ))}
      </div>

      {error && (
        <div className="p-3 text-sm rounded" style={{ background: "rgba(168,56,90,0.1)", border: "0.5px solid rgba(168,56,90,0.3)", color: "var(--wine-ll)" }}>
          {error}
        </div>
      )}

      <div className="flex gap-2 pt-4">
        <button onClick={onBack} className="btn-ghost" disabled={isSaving}>
          Atrás
        </button>
        <button onClick={save} disabled={!isValid || isSaving} className="btn-primary flex-1">
          {isSaving ? "Guardando..." : "Confirmar Derechos & Continuar"}
        </button>
      </div>
    </div>
  );
}
