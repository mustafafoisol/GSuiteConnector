import { useQuery } from "@tanstack/react-query";
import { useEffect, type ReactNode } from "react";
import { api } from "../api/client";
import { useToast } from "./Toast";

/** Blocks the app until Google is connected; shows a Connect screen otherwise. */
export function ConnectGate({ children }: { children: ReactNode }) {
  const toast = useToast();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["auth-status"],
    queryFn: api.authStatus,
  });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("auth") === "success") {
      toast("Connected to Google", "success");
      window.history.replaceState({}, "", "/");
      refetch();
    } else if (params.get("auth") === "error") {
      toast("Google authorization failed", "error");
      window.history.replaceState({}, "", "/");
    }
  }, [toast, refetch]);

  if (isLoading) return <div className="center">Loading…</div>;

  if (!data?.connected) {
    return (
      <div className="center">
        <h1>GSuiteConnector</h1>
        <p className="muted">Connect your Google account to get started.</p>
        <button
          className="primary"
          onClick={async () => {
            try {
              window.location.href = await api.loginUrl();
            } catch (e) {
              toast("Could not start login. Is client_secret.json in place?", "error");
            }
          }}
        >
          Connect Google
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
