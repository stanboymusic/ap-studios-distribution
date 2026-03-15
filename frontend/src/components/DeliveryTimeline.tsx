import React from 'react';
import { DeliveryEvent } from '../types';
import { API_BASE, getApiHeaders } from '../api/client';

async function fetchEvents(releaseId: string): Promise<DeliveryEvent[]> {
  const res = await fetch(`${API_BASE}/delivery/events/${releaseId}`, {
    headers: getApiHeaders(),
  });
  return res.json();
}

export function DeliveryTimeline({ releaseId }: { releaseId: string }) {
  const [events, setEvents] = React.useState<DeliveryEvent[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetchEvents(releaseId)
      .then(setEvents)
      .finally(() => setLoading(false));
  }, [releaseId]);

  if (loading) return <p>Cargando eventos...</p>;

  return (
    <div className="timeline">
      {events.map((event, idx) => (
        <div key={idx} className={`timeline-event ${event.event_type.toLowerCase()}`}>
          <div className="time">
            {new Date(event.created_at).toLocaleString()}
          </div>
          <div className="content">
            <strong>{event.event_type}</strong>
            <span className="dsp">({event.dsp})</span>
            <p>{event.message}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
