import React from 'react';
import { DeliveryEvent } from '../types';

async function fetchEvents(releaseId: string): Promise<DeliveryEvent[]> {
  const res = await fetch(
    `http://127.0.0.1:8000/api/delivery/events/${releaseId}`
  );
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