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
            className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
          >
            Artist 100%
          </button>
          <button 
            onClick={() => applyPreset('split-50-50')}
            className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
          >
            Split 50/50
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded border">
        <div>
          <label htmlFor="rights-scope" className="block text-sm font-medium text-gray-700">Scope</label>
          <select 
            id="rights-scope"
            value={scope} 
            onChange={(e) => setScope(e.target.value)}
            className="mt-1 block w-full border rounded-md p-2"
          >
            <option value="release">Release</option>
            <option value="track">Track (All)</option>
          </select>
        </div>
        <div>
          <label htmlFor="rights-territory" className="block text-sm font-medium text-gray-700">Territory</label>
          <select 
            id="rights-territory"
            value={territory} 
            onChange={(e) => handleTerritoryChange(e.target.value)}
            className="mt-1 block w-full border rounded-md p-2"
          >
            <option value="WORLD">WORLD</option>
            <option value="US">United States</option>
            <option value="ES">Spain</option>
          </select>
        </div>
        <div>
          <label htmlFor="rights-usage" className="block text-sm font-medium text-gray-700">Usage Type</label>
          <select 
            id="rights-usage"
            value={usageType} 
            onChange={(e) => handleUsageTypeChange(e.target.value)}
            className="mt-1 block w-full border rounded-md p-2"
          >
            <option value="Streaming">Streaming</option>
            <option value="Download">Download</option>
          </select>
        </div>
        <div>
          <label htmlFor="rights-valid-from" className="block text-sm font-medium text-gray-700">Valid From</label>
          <input 
            id="rights-valid-from"
            type="date" 
            value={validFrom}
            onChange={(e) => handleValidFromChange(e.target.value)}
            className="mt-1 block w-full border rounded-md p-2"
          />
        </div>
        <div>
          <label htmlFor="rights-valid-to" className="block text-sm font-medium text-gray-700">Valid To (Optional)</label>
          <input 
            id="rights-valid-to"
            type="date" 
            value={validTo}
            onChange={(e) => handleValidToChange(e.target.value)}
            className="mt-1 block w-full border rounded-md p-2"
          />
        </div>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Party</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">% Share</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {shares.map((share, index) => (
              <tr key={index}>
                <td className="px-4 py-2">
                  <input 
                    type="text" 
                    aria-label={`Party name for share ${index + 1}`}
                    value={share.partyReference}
                    onChange={(e) => updateShare(index, 'partyReference', e.target.value)}
                    placeholder="Party Name/Ref"
                    className="w-full border-none focus:ring-0 text-sm"
                  />
                </td>
                <td className="px-4 py-2">
                  <select 
                    aria-label={`Rights type for share ${index + 1}`}
                    value={share.rightsType}
                    onChange={(e) => updateShare(index, 'rightsType', e.target.value)}
                    className="w-full border-none focus:ring-0 text-sm"
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
                    className="w-20 border-none focus:ring-0 text-sm font-mono"
                    min="0"
                    max="100"
                  />
                </td>
                <td className="px-4 py-2 text-right">
                  <button onClick={() => removeShare(index)} className="text-red-500 hover:text-red-700 font-bold">
                    REMOVE
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="p-2 bg-gray-50 border-t">
          <button 
            onClick={addShare}
            className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
          >
            + Add Party
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {Object.entries(buckets).map(([role, sum]) => (
          <div key={role} className={`p-4 rounded-md flex justify-between items-center ${Math.abs(sum - 100) < 0.01 ? 'bg-green-50 text-green-800' : 'bg-yellow-50 text-yellow-800'}`}>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${Math.abs(sum - 100) < 0.01 ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
              <span className="font-medium">{role} Total: {sum}%</span>
            </div>
            <span className="text-sm font-bold">{Math.abs(sum - 100) < 0.01 ? 'VALID' : 'INCOMPLETE (Must be 100%)'}</span>
          </div>
        ))}
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
          {error}
        </div>
      )}

      <div className="flex gap-2 pt-4">
        <button 
          onClick={onBack} 
          className="px-6 py-2 border rounded-md hover:bg-gray-50"
          disabled={isSaving}
        >
          Atrás
        </button>
        <button 
          onClick={save} 
          disabled={!isValid || isSaving}
          className={`flex-1 px-6 py-2 rounded-md font-bold text-white transition-colors ${
            !isValid || isSaving ? 'bg-gray-400 cursor-not-allowed' : 'bg-black hover:bg-gray-800'
          }`}
        >
          {isSaving ? "Guardando..." : "Confirmar Derechos & Continuar"}
        </button>
      </div>
    </div>
  );
}
