import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import type { CommandResult, PendingAction } from "../api/types";
import { errorMessage, useToast } from "./Toast";

export function CommandBar() {
  const qc = useQueryClient();
  const toast = useToast();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<CommandResult | null>(null);
  const [pending, setPending] = useState<PendingAction | null>(null);

  const refreshViews = () => {
    qc.invalidateQueries({ queryKey: ["messages"] });
    qc.invalidateQueries({ queryKey: ["events"] });
  };

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true);
    setResult(null);
    setPending(null);
    try {
      const res = await api.command(text);
      setResult(res);
      setPending(res.pending);
      if (res.actions_taken.length) refreshViews();
      setText("");
    } catch (e) {
      toast(errorMessage(e), "error");
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!pending) return;
    setBusy(true);
    try {
      await api.confirm(pending);
      toast("Done", "success");
      setPending(null);
      setResult(null);
      refreshViews();
    } catch (e) {
      toast(errorMessage(e), "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="commandbar">
      {result?.reply && <div className="assistant-reply">{result.reply}</div>}
      {pending && (
        <div className="assistant-reply pending">
          <strong>Confirm:</strong> {pending.summary}
          <div className="pending-row">
            <button className="primary" onClick={confirm} disabled={busy}>
              Confirm
            </button>
            <button onClick={() => setPending(null)} disabled={busy}>
              Cancel
            </button>
          </div>
        </div>
      )}
      <form onSubmit={submit}>
        <input
          placeholder="Ask anything… e.g. “summarize my unread emails” or “schedule a 30-min sync tomorrow 3pm”"
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={busy}
        />
        <button className="primary" type="submit" disabled={busy || !text.trim()}>
          {busy ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
