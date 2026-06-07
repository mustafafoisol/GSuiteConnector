import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "../api/client";
import type { CalendarEvent } from "../api/types";
import { EventDialog } from "./EventDialog";

function dayKey(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
}

function timeLabel(ev: CalendarEvent): string {
  if (ev.all_day) return "All day";
  const s = new Date(ev.start);
  const e = new Date(ev.end);
  const fmt = (d: Date) => d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${fmt(s)} – ${fmt(e)}`;
}

export function CalendarView() {
  const [days, setDays] = useState(7);
  const [dialog, setDialog] = useState<{ open: boolean; event: CalendarEvent | null }>({
    open: false,
    event: null,
  });

  const timeMin = useMemo(() => new Date().toISOString(), []);
  const timeMax = useMemo(
    () => new Date(Date.now() + days * 86400_000).toISOString(),
    [days]
  );

  const { data, isLoading } = useQuery({
    queryKey: ["events", days],
    queryFn: () => api.listEvents(timeMin, timeMax),
  });

  const grouped = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const ev of data?.events ?? []) {
      const k = dayKey(ev.start);
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(ev);
    }
    return Array.from(map.entries());
  }, [data]);

  return (
    <>
      <div className="toolbar">
        <h2>Calendar</h2>
        <select style={{ width: "auto" }} value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={1}>Today</option>
          <option value={7}>Next 7 days</option>
          <option value={30}>Next 30 days</option>
        </select>
        <button className="primary" onClick={() => setDialog({ open: true, event: null })}>
          + New event
        </button>
      </div>

      {isLoading && <div className="spinner">Loading events…</div>}
      {data && grouped.length === 0 && <div className="empty">No upcoming events.</div>}

      {grouped.map(([day, events]) => (
        <div className="day-group" key={day}>
          <div className="day-head">{day}</div>
          {events.map((ev) => (
            <div className="event" key={ev.id} onClick={() => setDialog({ open: true, event: ev })}>
              <div className="event-time">{timeLabel(ev)}</div>
              <div>
                <div className="event-title">{ev.summary || "(no title)"}</div>
                {ev.location && <div className="muted">{ev.location}</div>}
              </div>
            </div>
          ))}
        </div>
      ))}

      {dialog.open && (
        <EventDialog event={dialog.event} onClose={() => setDialog({ open: false, event: null })} />
      )}
    </>
  );
}
