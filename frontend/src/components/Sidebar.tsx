import { useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink } from "react-router-dom";
import { api } from "../api/client";

export function Sidebar() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["auth-status"], queryFn: api.authStatus });

  return (
    <aside className="sidebar">
      <div className="brand">📬 GSuiteConnector</div>
      <NavLink to="/inbox" className="nav-link">
        Inbox
      </NavLink>
      <NavLink to="/compose" className="nav-link">
        Compose
      </NavLink>
      <NavLink to="/calendar" className="nav-link">
        Calendar
      </NavLink>
      <div className="sidebar-footer">
        {data?.email && <div>{data.email}</div>}
        <button
          style={{ marginTop: 8, width: "100%" }}
          onClick={async () => {
            await api.logout();
            qc.invalidateQueries();
          }}
        >
          Disconnect
        </button>
      </div>
    </aside>
  );
}
