import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { errorMessage, useToast } from "../components/Toast";

export function EmailDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const [replyText, setReplyText] = useState("");
  const [showReply, setShowReply] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["message", id],
    queryFn: () => api.getMessage(id),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["messages"] });

  const archiveM = useMutation({
    mutationFn: () => api.archive(id),
    onSuccess: () => {
      toast("Archived", "success");
      invalidate();
      navigate("/inbox");
    },
    onError: (e) => toast(errorMessage(e), "error"),
  });

  const replyM = useMutation({
    mutationFn: () => api.reply({ thread_id: data!.thread_id, body: replyText }),
    onSuccess: () => {
      toast("Reply sent", "success");
      setReplyText("");
      setShowReply(false);
      invalidate();
    },
    onError: (e) => toast(errorMessage(e), "error"),
  });

  if (isLoading || !data) return <div className="spinner">Loading…</div>;

  return (
    <>
      <div className="toolbar">
        <button onClick={() => navigate("/inbox")}>← Back</button>
        <div style={{ flex: 1 }} />
        <button onClick={() => setShowReply((s) => !s)}>Reply</button>
        <button onClick={() => archiveM.mutate()} disabled={archiveM.isPending}>
          Archive
        </button>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>{data.subject || "(no subject)"}</h2>
        <div className="muted">
          From: {data.sender}
          <br />
          To: {data.to}
          <br />
          {data.date}
        </div>
        <div className="email-body">{data.body || data.snippet}</div>
      </div>

      {showReply && (
        <div className="card" style={{ marginTop: 14 }}>
          <label>Reply</label>
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="Type your reply…"
          />
          <div className="modal-actions">
            <button onClick={() => setShowReply(false)}>Cancel</button>
            <button
              className="primary"
              onClick={() => replyM.mutate()}
              disabled={replyM.isPending || !replyText.trim()}
            >
              {replyM.isPending ? "Sending…" : "Send reply"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
