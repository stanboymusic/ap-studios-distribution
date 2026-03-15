import { useEffect, useMemo, useState } from "react";
import { apiFetch, API_BASE } from "../api/client";
import { Card, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/Table";

type ReleaseDetailResponse = {
  id: string;
  status: string;
  profile?: string | null;
  release: {
    title: string;
    version?: string | null;
    type: string;
    original_release_date?: string | null;
    language?: string | null;
    upc?: string | null;
  };
  artist?: {
    id: string;
    name: string;
    party_reference?: string | null;
    party_id?: string | null;
  } | null;
  tracks: Array<{
    id: string;
    title: string;
    isrc: string;
    duration: number;
    audio_asset?: {
      path?: string | null;
      format?: string | null;
      checksum?: string | null;
    } | null;
  }>;
  artwork?: {
    id?: string | null;
    path?: string | null;
    resolution?: string | null;
    format?: string | null;
  } | null;
  ern: {
    generated: boolean;
    last_generated_at?: string | null;
    xml_path?: string | null;
    xml?: string | null;
  };
  validation: {
    last_status?: string | null;
    signed?: boolean | null;
    signature_algorithm?: string | null;
    history: Array<{
      timestamp: string;
      validator: string;
      type: string;
      status: "passed" | "failed";
      errors: any[];
    }>;
  };
  delivery: {
    current_status?: string | null;
    timeline: Array<{
      event: string;
      timestamp: string;
      source: string;
      dsp?: string;
      message?: string;
    }>;
  };
};

function formatDuration(seconds: number) {
  const s = Math.max(0, Math.floor(seconds || 0));
  const mm = Math.floor(s / 60);
  const ss = String(s % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

function StatusBadge({ status }: { status: string }) {
  const color = useMemo(() => {
    const s = (status || "").toUpperCase();
    if (s === "CONFIRMED") return "bg-emerald-600";
    if (s === "ACCEPTED") return "bg-green-600";
    if (s === "REJECTED") return "bg-red-600";
    if (s === "DELIVERY_QUEUED" || s === "QUEUED") return "bg-indigo-600";
    if (s === "DELIVERED") return "bg-cyan-600";
    if (s === "VALIDATED") return "bg-lime-600";
    if (s === "SIGNED") return "bg-violet-600";
    if (s === "CREATED") return "bg-slate-500";
    if (s === "PROCESSING") return "bg-yellow-600";
    if (s === "UPLOADED" || s === "UPLOADING") return "bg-blue-600";
    if (s === "DRAFT") return "bg-gray-400";
    return "bg-gray-500";
  }, [status]);

  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold text-white ${color}`}>
      {(status || "UNKNOWN").toUpperCase()}
    </span>
  );
}

export default function ReleaseDetail({
  releaseId,
  onBack,
}: {
  releaseId: string;
  onBack?: () => void;
}) {
  const [data, setData] = useState<ReleaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await apiFetch<ReleaseDetailResponse>(
          `/catalog/releases/${releaseId}?include_ern_xml=true`
        );
        if (!cancelled) setData(res);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load release");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [releaseId]);

  if (loading) {
    return (
      <div className="p-8">
        <div className="text-sm text-gray-500">Loading release…</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 space-y-4">
        <div className="text-sm text-red-600">{error || "Not found"}</div>
        <Button onClick={onBack}>Back</Button>
      </div>
    );
  }

  const title = data.release?.title || "Untitled";
  const artistName = data.artist?.name || "Unknown";
  const artworkUrl = data.artwork?.id ? `${API_BASE}/assets/artwork/${data.artwork.id}` : null;

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-start justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-semibold text-[#1B4079]">{title}</h2>
            <StatusBadge status={data.delivery?.current_status || data.status} />
          </div>
          <div className="text-sm text-[#4D7C8A]">
            Release ID: <span className="font-mono">{data.id}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={onBack}>
            Back
          </Button>
        </div>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Metadata + Artist */}
        <Card className="rounded-2xl border-none shadow-sm">
          <CardContent className="p-6 space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-[#1B4079]">Metadata</h3>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <dt className="text-[#4D7C8A]">Type</dt>
                <dd className="text-gray-900">{data.release.type}</dd>
                <dt className="text-[#4D7C8A]">Release Date</dt>
                <dd className="text-gray-900">{data.release.original_release_date || "—"}</dd>
                <dt className="text-[#4D7C8A]">Language</dt>
                <dd className="text-gray-900">{data.release.language || "—"}</dd>
                <dt className="text-[#4D7C8A]">UPC</dt>
                <dd className="text-gray-900">{data.release.upc || "—"}</dd>
                <dt className="text-[#4D7C8A]">Profile</dt>
                <dd className="text-gray-900">{data.profile || "—"}</dd>
                <dt className="text-[#4D7C8A]">Signature</dt>
                <dd className="text-gray-900">
                  {data.validation?.signed ? `Signed (${data.validation.signature_algorithm || "XMLDSig"})` : "Unsigned"}
                </dd>
              </dl>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[#1B4079]">Artist</h3>
              <div className="mt-2">
                <div className="text-sm font-medium text-gray-900">{artistName}</div>
                <div className="text-xs text-[#4D7C8A] mt-1">
                  Artist ID: <span className="font-mono">{data.artist?.id || "—"}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Assets + Tracks */}
        <Card className="rounded-2xl border-none shadow-sm lg:col-span-1">
          <CardContent className="p-6 space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-[#1B4079]">Artwork</h3>
              <div className="mt-3">
                {artworkUrl ? (
                  <img
                    src={artworkUrl}
                    alt="Artwork"
                    className="w-full max-w-[320px] rounded-xl shadow-sm border border-gray-100"
                  />
                ) : (
                  <div className="text-sm text-gray-500">No artwork attached.</div>
                )}
                {data.artwork?.resolution ? (
                  <div className="text-xs text-[#4D7C8A] mt-2">
                    {data.artwork.resolution} {data.artwork.format ? `· ${data.artwork.format}` : ""}
                  </div>
                ) : null}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[#1B4079]">Tracks</h3>
              <div className="mt-3">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>ISRC</TableHead>
                      <TableHead className="text-right">Duration</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.tracks.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center py-6 text-gray-500">
                          No tracks.
                        </TableCell>
                      </TableRow>
                    ) : (
                      data.tracks.map((t) => (
                        <TableRow key={t.id || `${t.title}-${t.isrc}`}>
                          <TableCell className="font-medium">{t.title}</TableCell>
                          <TableCell className="font-mono text-xs">{t.isrc || "—"}</TableCell>
                          <TableCell className="text-right text-sm">{formatDuration(t.duration)}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Timeline + Validation */}
        <Card className="rounded-2xl border-none shadow-sm">
          <CardContent className="p-6 space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-[#1B4079]">Delivery Timeline</h3>
              <div className="mt-3 space-y-2">
                {data.delivery.timeline.length === 0 ? (
                  <div className="text-sm text-gray-500">No delivery events yet.</div>
                ) : (
                  data.delivery.timeline.map((e, idx) => (
                    <div key={`${e.timestamp}-${idx}`} className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{e.event}</div>
                        <div className="text-xs text-[#4D7C8A]">
                          {e.dsp ? `${e.dsp} · ` : ""}
                          {e.message || ""}
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 whitespace-nowrap">
                        {e.timestamp ? new Date(e.timestamp).toLocaleString() : "—"}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[#1B4079]">Validation History</h3>
              <div className="mt-3 space-y-2">
                {data.validation.history.length === 0 ? (
                  <div className="text-sm text-gray-500">No validations recorded yet.</div>
                ) : (
                  data.validation.history
                    .slice()
                    .reverse()
                    .map((v, idx) => (
                      <div key={`${v.timestamp}-${idx}`} className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {v.type} · {v.validator}
                          </div>
                          <div className="text-xs text-[#4D7C8A]">
                            {v.status.toUpperCase()}
                            {Array.isArray(v.errors) && v.errors.length ? ` · ${v.errors.length} errors` : ""}
                          </div>
                        </div>
                        <div className="text-xs text-gray-500 whitespace-nowrap">
                          {v.timestamp ? new Date(v.timestamp).toLocaleString() : "—"}
                        </div>
                      </div>
                    ))
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section>
        <Card className="rounded-2xl border-none shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[#1B4079]">ERN Preview (read-only)</h3>
              <div className="text-xs text-[#4D7C8A]">
                {data.ern.generated ? "Generated" : "Not generated"}
                {data.ern.last_generated_at ? ` · ${new Date(data.ern.last_generated_at).toLocaleString()}` : ""}
              </div>
            </div>
            <pre className="mt-4 max-h-[420px] overflow-auto rounded-xl bg-[#0B1020] text-[#EAF0F2] p-4 text-xs leading-relaxed">
              {data.ern.xml || "—"}
            </pre>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
