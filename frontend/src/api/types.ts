export interface AuthStatus {
  connected: boolean;
  email: string | null;
}

export interface EmailSummary {
  id: string;
  thread_id: string;
  sender: string;
  to: string;
  subject: string;
  snippet: string;
  date: string;
  unread: boolean;
  labels: string[];
}

export interface EmailDetail extends EmailSummary {
  body: string;
}

export interface EmailListResponse {
  messages: EmailSummary[];
  next_page_token: string | null;
}

export interface SendEmailRequest {
  to: string[];
  subject: string;
  body: string;
  cc?: string[];
  bcc?: string[];
}

export interface ReplyRequest {
  thread_id: string;
  body: string;
  to?: string[];
  subject?: string | null;
}

export interface Attendee {
  email: string;
  response_status: string;
}

export interface CalendarEvent {
  id: string;
  summary: string;
  description: string;
  location: string;
  start: string;
  end: string;
  all_day: boolean;
  attendees: Attendee[];
  html_link: string;
}

export interface EventListResponse {
  events: CalendarEvent[];
}

export interface CreateEventRequest {
  summary: string;
  start: string;
  end: string;
  description?: string;
  location?: string;
  attendees?: string[];
  all_day?: boolean;
  send_updates?: boolean;
}

export interface PendingAction {
  tool: string;
  input: Record<string, unknown>;
  summary: string;
}

export interface CommandResult {
  reply: string;
  actions_taken: string[];
  pending: PendingAction | null;
}
