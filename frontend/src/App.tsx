import { Navigate, Route, Routes } from "react-router-dom";
import { CommandBar } from "./components/CommandBar";
import { ConnectGate } from "./components/ConnectGate";
import { Sidebar } from "./components/Sidebar";
import { ToastProvider } from "./components/Toast";
import { CalendarView } from "./views/CalendarView";
import { Compose } from "./views/Compose";
import { EmailDetail } from "./views/EmailDetail";
import { Inbox } from "./views/Inbox";

export default function App() {
  return (
    <ToastProvider>
      <ConnectGate>
        <div className="app">
          <Sidebar />
          <div className="main">
            <div className="content">
              <Routes>
                <Route path="/" element={<Navigate to="/inbox" replace />} />
                <Route path="/inbox" element={<Inbox />} />
                <Route path="/inbox/:id" element={<EmailDetail />} />
                <Route path="/compose" element={<Compose />} />
                <Route path="/calendar" element={<CalendarView />} />
                <Route path="*" element={<Navigate to="/inbox" replace />} />
              </Routes>
            </div>
            <CommandBar />
          </div>
        </div>
      </ConnectGate>
    </ToastProvider>
  );
}
