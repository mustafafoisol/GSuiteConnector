import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

function shortDate(raw: string): string {
  const d = new Date(raw);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function senderName(from: string): string {
  const m = from.match(/^\s*"?([^"<]+)"?\s*</);
  return (m ? m[1] : from).trim();
}

export function Inbox() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [unreadOnly, setUnreadOnly] = useState(false);

  const effectiveQuery = [query, unreadOnly ? "is:unread" : ""].filter(Boolean).join(" ");

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["messages", effectiveQuery],
    queryFn: () => api.listMessages(effectiveQuery, 30),
  });

  return (
    <>
      <div className="toolbar">
        <h2>Inbox</h2>
        <button onClick={() => refetch()} disabled={isFetching}>
          {isFetching ? "…" : "Refresh"}
        </button>
      </div>

      <div className="toolbar">
        <form
          style={{ display: "flex", gap: 8, flex: 1 }}
          onSubmit={(e) => {
            e.preventDefault();
            setQuery(search);
          }}
        >
          <input
            placeholder="Search mail (Gmail syntax: from:alice newer_than:7d)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
        <label style={{ display: "flex", gap: 6, alignItems: "center", margin: 0 }}>
          <input
            type="checkbox"
            style={{ width: "auto" }}
            checked={unreadOnly}
            onChange={(e) => setUnreadOnly(e.target.checked)}
          />
          Unread only
        </label>
      </div>

      {isLoading && <div className="spinner">Loading messages…</div>}
      {isError && <div className="empty">Failed to load. Try refreshing.</div>}
      {data && data.messages.length === 0 && <div className="empty">No messages.</div>}

      {data && data.messages.length > 0 && (
        <div className="list">
          {data.messages.map((m) => (
            <div
              key={m.id}
              className={`row ${m.unread ? "unread" : ""}`}
              onClick={() => navigate(`/inbox/${m.id}`)}
            >
              <div className="row-sender">{senderName(m.sender)}</div>
              <div className="row-body">
                <span className="row-subject">{m.subject || "(no subject)"}</span>
                <span className="row-snippet"> — {m.snippet}</span>
              </div>
              <div className="row-date">{shortDate(m.date)}</div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
