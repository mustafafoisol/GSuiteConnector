import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import type { CalendarEvent, CreateEventRequest } from "../api/types";
import { errorMessage, useToast } from "../components/Toast";

/** Convert a <input type="datetime-local"> value to RFC3339 with local offset. */
function toRFC3339(local: string): string {
  const d = new Date(local);
  const off = -d.getTimezoneOffset();
  const sign = off >= 0 ? "+" : "-";
  const pad = (n: number) => String(Math.floor(Math.abs(n))).padStart(2, "0");
  const offStr = `${sign}${pad(off / 60)}:${pad(off % 60)}`;
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(
    d.getHours()
  )}:${p(d.getMinutes())}:00${offStr}`;
}

/** RFC3339/ISO -> value for datetime-local input (local wall time). */
function toLocalInput(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(
    d.getHours()
  )}:${p(d.getMinutes())}`;
}

interface Props {
  event: CalendarEvent | null; // null => create
  onClose: () => void;
}

export function EventDialog({ event, onClose }: Props) {
  const qc = useQueryClient();
  const toast = useToast();
  const editing = !!event;

  const [summary, setSummary] = useState(event?.summary ?? "");
  const [location, setLocation] = useState(event?.location ?? "");
  const [description, setDescription] = useState(event?.description ?? "");
  const [start, setStart] = useState(
    event ? toLocalInput(event.start) : toLocalInput(new Date(Date.now() + 3600_000).toISOString())
  );
  const [end, setEnd] = useState(
    event ? toLocalInput(event.end) : toLocalInput(new Date(Date.now() + 5400_000).toISOString())
  );
  const [attendees, setAttendees] = useState(event?.attendees.map((a) => a.email).join(", ") ?? "");

  const refresh = () => qc.invalidateQueries({ queryKey: ["events"] });

  const payload = (): CreateEventRequest => ({
    summary,
    location,
    description,
    start: toRFC3339(start),
    end: toRFC3339(end),
    attendees: attendees.split(/[,;]/).map((s) => s.trim()).filter(Boolean),
    send_updates: false,
  });

  const saveM = useMutation({
    mutationFn: () =>
      editing ? api.updateEvent(event!.id, payload()) : api.createEvent(payload()),
    onSuccess: () => {
      toast(editing ? "Event updated" : "Event created", "success");
      refresh();
      onClose();
    },
    onError: (e) => toast(errorMessage(e), "error"),
  });

  const deleteM = useMutation({
    mutationFn: () => api.deleteEvent(event!.id),
    onSuccess: () => {
      toast("Event deleted", "success");
      refresh();
      onClose();
    },
    onError: (e) => toast(errorMessage(e), "error"),
  });

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{editing ? "Edit event" : "New event"}</h3>
        <label>Title</label>
        <input value={summary} onChange={(e) => setSummary(e.target.value)} />
        <div className="row-2">
          <div>
            <label>Start</label>
            <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} />
          </div>
          <div>
            <label>End</label>
            <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} />
          </div>
        </div>
        <label>Location</label>
        <input value={location} onChange={(e) => setLocation(e.target.value)} />
        <label>Attendees (comma-separated)</label>
        <input value={attendees} onChange={(e) => setAttendees(e.target.value)} />
        <label>Description</label>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} />

        <div className="modal-actions">
          {editing && (
            <button
              className="danger"
              style={{ marginRight: "auto" }}
              onClick={() => deleteM.mutate()}
              disabled={deleteM.isPending}
            >
              Delete
            </button>
          )}
          <button onClick={onClose}>Cancel</button>
          <button
            className="primary"
            onClick={() => saveM.mutate()}
            disabled={saveM.isPending || !summary.trim()}
          >
            {saveM.isPending ? "Saving…" : editing ? "Save" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}
