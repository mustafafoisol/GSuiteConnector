import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { SendEmailRequest } from "../api/types";
import { errorMessage, useToast } from "../components/Toast";

function parseList(s: string): string[] {
  return s
    .split(/[,;]/)
    .map((x) => x.trim())
    .filter(Boolean);
}

export function Compose() {
  const navigate = useNavigate();
  const toast = useToast();
  const [to, setTo] = useState("");
  const [cc, setCc] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const build = (): SendEmailRequest => ({
    to: parseList(to),
    cc: parseList(cc),
    subject,
    body,
  });

  const sendM = useMutation({
    mutationFn: () => api.sendEmail(build()),
    onSuccess: () => {
      toast("Email sent", "success");
      navigate("/inbox");
    },
    onError: (e) => toast(errorMessage(e), "error"),
  });

  const draftM = useMutation({
    mutationFn: () => api.createDraft(build()),
    onSuccess: () => toast("Draft saved", "success"),
    onError: (e) => toast(errorMessage(e), "error"),
  });

  const valid = parseList(to).length > 0 && subject.trim().length > 0;

  return (
    <>
      <div className="toolbar">
        <h2>Compose</h2>
      </div>
      <div className="card">
        <label>To (comma-separated)</label>
        <input value={to} onChange={(e) => setTo(e.target.value)} placeholder="alice@example.com" />
        <label>Cc</label>
        <input value={cc} onChange={(e) => setCc(e.target.value)} />
        <label>Subject</label>
        <input value={subject} onChange={(e) => setSubject(e.target.value)} />
        <label>Body</label>
        <textarea value={body} onChange={(e) => setBody(e.target.value)} />
        <div className="modal-actions">
          <button onClick={() => draftM.mutate()} disabled={!valid || draftM.isPending}>
            Save draft
          </button>
          <button className="primary" onClick={() => sendM.mutate()} disabled={!valid || sendM.isPending}>
            {sendM.isPending ? "Sending…" : "Send"}
          </button>
        </div>
      </div>
    </>
  );
}
