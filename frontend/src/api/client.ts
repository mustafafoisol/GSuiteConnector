import axios from "axios";
import type {
  AuthStatus,
  CalendarEvent,
  CommandResult,
  CreateEventRequest,
  EmailDetail,
  EmailListResponse,
  EventListResponse,
  PendingAction,
  ReplyRequest,
  SendEmailRequest,
} from "./types";

const http = axios.create({ baseURL: "/api" });

export const api = {
  // auth
  authStatus: () => http.get<AuthStatus>("/auth/status").then((r) => r.data),
  loginUrl: () =>
    http.get<{ authorization_url: string }>("/auth/login").then((r) => r.data.authorization_url),
  logout: () => http.post("/auth/logout").then((r) => r.data),

  // gmail
  listMessages: (q = "", maxResults = 25) =>
    http
      .get<EmailListResponse>("/gmail/messages", { params: { q, max_results: maxResults } })
      .then((r) => r.data),
  getMessage: (id: string) =>
    http.get<EmailDetail>(`/gmail/messages/${id}`).then((r) => r.data),
  sendEmail: (req: SendEmailRequest) =>
    http.post("/gmail/messages/send", req).then((r) => r.data),
  createDraft: (req: SendEmailRequest) =>
    http.post("/gmail/drafts", req).then((r) => r.data),
  reply: (req: ReplyRequest) =>
    http.post("/gmail/messages/reply", req).then((r) => r.data),
  archive: (id: string) =>
    http.post(`/gmail/messages/${id}/archive`).then((r) => r.data),
  markRead: (id: string) =>
    http.post(`/gmail/messages/${id}/read`).then((r) => r.data),

  // calendar
  listEvents: (timeMin?: string, timeMax?: string, q?: string) =>
    http
      .get<EventListResponse>("/calendar/events", {
        params: { time_min: timeMin, time_max: timeMax, q },
      })
      .then((r) => r.data),
  createEvent: (req: CreateEventRequest) =>
    http.post<CalendarEvent>("/calendar/events", req).then((r) => r.data),
  updateEvent: (id: string, req: Partial<CreateEventRequest>) =>
    http.patch<CalendarEvent>(`/calendar/events/${id}`, req).then((r) => r.data),
  deleteEvent: (id: string) =>
    http.delete(`/calendar/events/${id}`).then((r) => r.data),

  // assistant
  command: (text: string) =>
    http.post<CommandResult>("/assistant/command", { text }).then((r) => r.data),
  confirm: (action: PendingAction) =>
    http
      .post("/assistant/confirm", { tool: action.tool, input: action.input })
      .then((r) => r.data),
};
