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
  const pillClass = useMemo(() => {
    const s = (status || "").toUpperCase();
    if (s === "CONFIRMED" || s === "ACCEPTED" || s === "VALIDATED" || s === "DELIVERED") return "pill-green";
    if (s === "REJECTED") return "pill-wine";
    if (s === "PROCESSING" || s === "DRAFT" || s === "CREATED") return "pill-gold";
    return "pill-blue";
  }, [status]);

  return (
    <span className={`pill ${pillClass}`}>
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
        <div className="text-sm" style={{ color: "var(--mist-d)" }}>Loading release…</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 space-y-4">
        <div className="text-sm" style={{ color: "var(--wine-ll)" }}>{error || "Not found"}</div>
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
            <h2 style={{ fontSize: 28, fontFamily: "var(--font-display)", fontWeight: 300, color: "#fff" }}>{title}</h2>
            <StatusBadge status={data.delivery?.current_status || data.status} />
          </div>
          <div className="text-sm" style={{ color: "var(--mist-d)" }}>
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
              <h3 className="text-sm font-semibold" style={{ color: "var(--mist)" }}>Metadata</h3>
              <dl className="release-meta mt-3 grid grid-cols-2 gap-2 text-sm">
                <dt>Type</dt>
                <dd>{data.release.type}</dd>
                <dt>Release Date</dt>
                <dd>{data.release.original_release_date || "—"}</dd>
                <dt>Language</dt>
                <dd>{data.release.language || "—"}</dd>
                <dt>UPC</dt>
                <dd>{data.release.upc || "—"}</dd>
                <dt>Profile</dt>
                <dd>{data.profile || "—"}</dd>
                <dt>Signature</dt>
                <dd>
                  {data.validation?.signed ? `Signed (${data.validation.signature_algorithm || "XMLDSig"})` : "Unsigned"}
                </dd>
              </dl>
            </div>

            <div>
              <h3 className="text-sm font-semibold" style={{ color: "var(--mist)" }}>Artist</h3>
              <div className="mt-2">
                <div className="text-sm font-medium" style={{ color: "var(--mist)" }}>{artistName}</div>
                <div className="text-sm mt-1" style={{ color: "var(--mist-d)" }}>
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
              <h3 className="text-sm font-semibold" style={{ color: "var(--mist)" }}>Artwork</h3>
              <div className="mt-3">
                {artworkUrl ? (
                  <img
                    src={artworkUrl}
                    alt="Artwork"
                    className="w-full max-w-[320px] rounded-xl"
                    style={{ border: "0.5px solid var(--border)" }}
                  />
                ) : (
                  <div className="text-sm" style={{ color: "var(--mist-d)" }}>No artwork attached.</div>
                )}
                {data.artwork?.resolution ? (
                  <div className="text-sm mt-2" style={{ color: "var(--mist-d)" }}>
                    {data.artwork.resolution} {data.artwork.format ? `· ${data.artwork.format}` : ""}
                  </div>
                ) : null}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold" style={{ color: "var(--mist)" }}>Tracks</h3>
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
                        <TableCell colSpan={3} className="text-center py-6" style={{ color: "var(--mist-d)" }}>
                          No tracks.
                        </TableCell>
                      </TableRow>
                    ) : (
                      data.tracks.map((t) => (
                        <TableRow key={t.id || `${t.title}-${t.isrc}`}>
                          <TableCell className="font-medium">{t.title}</TableCell>
                          <TableCell className="font-mono text-sm">{t.isrc || "—"}</TableCell>
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
              <h3 className="text-sm font-semibold" style={{ color: "var(--mist)" }}>Delivery Timeline</h3>
              <div className="mt-3 space-y-2">
                {data.delivery.timeline.length === 0 ? (
                  <div className="text-sm" style={{ color: "var(--mist-d)" }}>No delivery events yet.</div>
                ) : (
                  data.delivery.timeline.map((e, idx) => (
                    <div key={`${e.timestamp}-${idx}`} className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium" style={{ color: "var(--mist)" }}>{e.event}</div>
                        <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                          {e.dsp ? `${e.dsp} · ` : ""}
                          {e.message || ""}
                        </div>
                      </div>
                      <div className="text-sm whitespace-nowrap" style={{ color: "var(--mist-d)" }}>
                        {e.timestamp ? new Date(e.timestamp).toLocaleString() : "—"}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold" style={{ color: "var(--mist)" }}>Validation History</h3>
              <div className="mt-3 space-y-2">
                {data.validation.history.length === 0 ? (
                  <div className="text-sm" style={{ color: "var(--mist-d)" }}>No validations recorded yet.</div>
                ) : (
                  data.validation.history
                    .slice()
                    .reverse()
                    .map((v, idx) => (
                      <div key={`${v.timestamp}-${idx}`} className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-medium" style={{ color: "var(--mist)" }}>
                            {v.type} · {v.validator}
                          </div>
                          <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                            {v.status.toUpperCase()}
                            {Array.isArray(v.errors) && v.errors.length ? ` · ${v.errors.length} errors` : ""}
                          </div>
                        </div>
                        <div className="text-sm whitespace-nowrap" style={{ color: "var(--mist-d)" }}>
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
              <h3 className="text-sm font-semibold" style={{ color: "var(--mist)" }}>ERN Preview (read-only)</h3>
              <div className="text-sm" style={{ color: "var(--mist-d)" }}>
                {data.ern.generated ? "Generated" : "Not generated"}
                {data.ern.last_generated_at ? ` · ${new Date(data.ern.last_generated_at).toLocaleString()}` : ""}
              </div>
            </div>
            <pre className="mt-4 max-h-[420px] overflow-auto rounded-xl bg-[#0B1020] text-[#EAF0F2] p-4 text-sm leading-relaxed">
              {data.ern.xml || "—"}
            </pre>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
