import axios from "axios";

// ---------------------------------------------------------------------------
// Session storage. The access token is short-lived (15 min); the refresh token
// is rotated on every use and revoked server-side on logout.
// ---------------------------------------------------------------------------
const ACCESS_KEY = "token";
const REFRESH_KEY = "refresh_token";
const USER_KEY = "user";

export const session = {
  get access() { return localStorage.getItem(ACCESS_KEY); },
  get refresh() { return localStorage.getItem(REFRESH_KEY); },
  get user() {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); } catch { return null; }
  },
  save({ access_token, refresh_token, user }) {
    if (access_token) localStorage.setItem(ACCESS_KEY, access_token);
    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    localStorage.setItem("lastActivity", Date.now().toString());
  },
  setUser(user) { localStorage.setItem(USER_KEY, JSON.stringify(user)); },
  clear() {
    [ACCESS_KEY, REFRESH_KEY, USER_KEY, "lastPage", "sessionTimestamp", "lastActivity"].forEach((k) => localStorage.removeItem(k));
  },
};

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// The backend may cold-start on free hosting; auth calls get extra time.
const AUTH_TIMEOUT = 90000;

api.interceptors.request.use((config) => {
  const token = session.access;
  if (token && !config.skipAuth) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing = null;

async function refreshTokens() {
  const refresh_token = session.refresh;
  if (!refresh_token) throw new Error("no refresh token");
  const res = await api.post("/auth/refresh", { refresh_token }, { skipAuth: true, skipRefresh: true, timeout: AUTH_TIMEOUT });
  session.save(res.data);
  return res.data.access_token;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status;
    const code = error.response?.data?.code;
    if (status === 401 && !original.skipRefresh && !original._retried && session.refresh &&
        ["TOKEN_EXPIRED", "INVALID_TOKEN", "TOKEN_REVOKED", "NOT_AUTHENTICATED"].includes(code)) {
      original._retried = true;
      try {
        refreshing = refreshing || refreshTokens().finally(() => { refreshing = null; });
        const token = await refreshing;
        original.headers = { ...(original.headers || {}), Authorization: `Bearer ${token}` };
        return api(original);
      } catch {
        session.clear();
        window.dispatchEvent(new Event("qf:session-expired"));
      }
    } else if (status === 401 && !original.skipRefresh && session.access) {
      session.clear();
      window.dispatchEvent(new Event("qf:session-expired"));
    }
    return Promise.reject(error);
  },
);

/** Human-readable message from an API error. */
export const errorMessage = (error, fallback = "Something went wrong. Please try again.") => {
  const data = error?.response?.data;
  if (data?.errors?.length > 1) return data.errors.map((e) => e.message).join(" ");
  if (typeof data?.detail === "string") return data.detail;
  if (error?.code === "ECONNABORTED") return "The server took too long to respond. Please try again.";
  if (!error?.response) return "Cannot reach the server. Check your connection.";
  return fallback;
};

export const warmUpBackend = () => {
  api.get("/health", { timeout: AUTH_TIMEOUT, skipAuth: true }).catch(() => {});
};

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
const authPost = (url, body) => api.post(url, body, { timeout: AUTH_TIMEOUT, skipAuth: true, skipRefresh: true }).then((r) => r.data);

export const registerUser = ({ fullName, email, phone, password, organization }) =>
  authPost("/auth/register", { full_name: fullName, email, phone, password, organization: organization || null });
export const verifyRegistration = (email, otp) => authPost("/auth/verify-registration", { email, otp });
export const resendOTP = (email, purpose = "registration") => authPost("/auth/resend-otp", { email, purpose });
export const verifyEmail = (email, otp) => authPost("/auth/verify-email", { email, otp });
export const loginWithPassword = (email, password, location = null) => authPost("/auth/login", { email, password, location });
export const requestOTP = (email) => authPost("/auth/request-otp", { email });
export const verifyOTP = (email, otp, location = null) => authPost("/auth/verify-otp", { email, otp, location });
export const googleAuth = (accessToken, location = null) => authPost("/auth/google", { access_token: accessToken, location });
export const googleVerifyOTP = (email, otp, location = null) => authPost("/auth/google-verify-otp", { email, otp, location });
export const forgotPassword = (email) => authPost("/auth/forgot-password", { email });
export const resetPassword = (email, otp, new_password) => authPost("/auth/reset-password", { email, otp, new_password });

export const getMe = () => api.get("/auth/me").then((r) => r.data);
export const updateProfile = (profileData) => api.patch("/auth/me", profileData).then((r) => r.data);
export const changePassword = (current_password, new_password) =>
  api.post("/auth/change-password", { current_password, new_password }).then((r) => { session.save(r.data); return r.data; });

export const logoutUser = async () => {
  try {
    if (session.access) await api.post("/auth/logout", { refresh_token: session.refresh }, { skipRefresh: true });
  } finally {
    session.clear();
  }
};

// ---------------------------------------------------------------------------
// Complaints
// ---------------------------------------------------------------------------
export const submitComplaint = (subject, description) =>
  api.post("/complaint", { subject, description }, { timeout: 60000 }).then((r) => r.data);

/** Scoped server-side: customers get theirs, agents assigned ones, admins all. */
export const listComplaints = (params = {}) => api.get("/complaints", { params }).then((r) => r.data);
export const getAllComplaints = () => listComplaints({ page_size: 100 });
export const getComplaint = (ticketId) => api.get(`/complaints/${encodeURIComponent(ticketId)}`).then((r) => r.data);
export const getComplaintHistory = (ticketId) => api.get(`/complaints/${encodeURIComponent(ticketId)}/history`).then((r) => r.data);
export const getComplaintStats = () => api.get("/complaints/stats").then((r) => r.data);
export const deleteAllComplaints = () => api.delete("/complaints").then((r) => r.data);
export const deleteComplaint = (ticketId) => api.delete(`/complaint/${encodeURIComponent(ticketId)}`).then((r) => r.data);
export const bulkDeleteComplaints = (ids) => api.post("/complaints/bulk-delete", { ids }).then((r) => r.data);
export const submitReview = (ticketId, rating, feedback) =>
  api.post(`/complaint/${encodeURIComponent(ticketId)}/review`, { rating, feedback }).then((r) => r.data);
export const submitResolutionFeedback = (ticketId, isActuallyResolved, userComment = "") =>
  api.post(`/complaint/${encodeURIComponent(ticketId)}/resolution-feedback`,
    { is_actually_resolved: isActuallyResolved, user_comment: userComment }).then((r) => r.data);

/** Staff status change. Accepts a status string or the legacy boolean. */
export const updateComplaintStatus = (ticketId, statusOrResolved, admin_solution = null, note = null) => {
  const body = typeof statusOrResolved === "boolean" ? { is_resolved: statusOrResolved } : { status: statusOrResolved };
  if (admin_solution) body.admin_solution = admin_solution;
  if (note) body.note = note;
  return api.patch(`/complaint/${encodeURIComponent(ticketId)}/status`, body).then((r) => r.data);
};
export const assignComplaint = (ticketId, agentId) =>
  api.patch(`/complaints/${encodeURIComponent(ticketId)}/assign`, { agent_id: agentId }).then((r) => r.data);

export const uploadAttachment = (ticketId, file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post(`/complaints/${encodeURIComponent(ticketId)}/attachments`, form, {
    headers: { "Content-Type": "multipart/form-data" }, timeout: 60000,
  }).then((r) => r.data);
};
export const listAttachments = (ticketId) => api.get(`/complaints/${encodeURIComponent(ticketId)}/attachments`).then((r) => r.data);
export const downloadAttachment = async (ticketId, attachment) => {
  const res = await api.get(`/complaints/${encodeURIComponent(ticketId)}/attachments/${attachment.id}`, { responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = attachment.filename;
  link.click();
  URL.revokeObjectURL(url);
};

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------
export const listNotifications = (params = {}) => api.get("/notifications", { params }).then((r) => r.data);
export const markNotificationRead = (id) => api.post(`/notifications/${id}/read`).then((r) => r.data);
export const markAllNotificationsRead = () => api.post("/notifications/read-all").then((r) => r.data);

// ---------------------------------------------------------------------------
// Agent workspace (identity comes from the token; no email parameters)
// ---------------------------------------------------------------------------
export const getAgentQueue = (params = {}) => api.get("/agent/complaints/queue", { params }).then((r) => r.data);
export const getComplaintDetail = (ticketId) => api.get(`/agent/complaints/${encodeURIComponent(ticketId)}`).then((r) => r.data);
export const claimComplaint = (ticketId) => api.post(`/agent/complaints/${encodeURIComponent(ticketId)}/claim`).then((r) => r.data);
export const addAgentNote = (ticketId, note, internal = true) =>
  api.post(`/agent/complaints/${encodeURIComponent(ticketId)}/notes`, { note, internal }).then((r) => r.data);
export const validateSolution = (ticketId, draftSolution, steps = null) =>
  api.post("/agent/validate-solution", { ticket_id: ticketId, draft_solution: draftSolution, steps }, { timeout: 60000 }).then((r) => r.data);
export const sendResolution = (ticketId, finalSolution, steps = null) =>
  api.post("/agent/send-resolution", { ticket_id: ticketId, final_solution: finalSolution, steps }).then((r) => r.data);
export const getAllResolutions = (params = {}) => api.get("/agent/resolutions", { params }).then((r) => r.data);
export const getAuditLogs = (params = {}) => api.get("/agent/audit-logs", { params }).then((r) => r.data);

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------
export const adminOverview = () => api.get("/admin/overview").then((r) => r.data);
export const adminListUsers = (params = {}) => api.get("/admin/users", { params }).then((r) => r.data);
export const adminUpdateUser = (id, changes) => api.patch(`/admin/users/${id}`, changes).then((r) => r.data);
export const adminListAgents = () => api.get("/admin/agents").then((r) => r.data);
export const adminCategories = () => api.get("/admin/categories").then((r) => r.data);
export const adminAiLogs = (params = {}) => api.get("/admin/ai/logs", { params }).then((r) => r.data);
export const adminAiSummary = () => api.get("/admin/ai/summary").then((r) => r.data);
export const adminAuditLogs = (params = {}) => api.get("/admin/audit-logs", { params }).then((r) => r.data);
export const adminSystem = () => api.get("/admin/system").then((r) => r.data);
export const adminExportComplaints = async (params = {}) => {
  const res = await api.get("/admin/reports/complaints.csv", { params, responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = "complaints.csv";
  link.click();
  URL.revokeObjectURL(url);
};

// ---------------------------------------------------------------------------
// Public
// ---------------------------------------------------------------------------
export const submitFeedback = (feedbackData) => api.post("/feedback", feedbackData, { skipAuth: true }).then((r) => r.data);
export const chatWithBot = (message) => api.post("/agent/chat", { message }, { skipAuth: true }).then((r) => r.data);

export default api;
