jest.mock("axios", () => {
  const interceptors = { request: [], response: [] };
  const instance = jest.fn();
  Object.assign(instance, {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    post: jest.fn(() => Promise.resolve({ data: { ok: true } })),
    patch: jest.fn(() => Promise.resolve({ data: {} })),
    delete: jest.fn(() => Promise.resolve({ data: {} })),
    interceptors: {
      request: { use: (fn) => interceptors.request.push(fn) },
      response: { use: (ok, err) => interceptors.response.push({ ok, err }) },
    },
  });
  return { __esModule: true, default: { create: jest.fn(() => instance) }, instance, interceptors };
});

import { instance as http, interceptors } from "axios";
import * as api from "../api";

const AUTH = { timeout: 90000, skipAuth: true, skipRefresh: true };

beforeEach(() => localStorage.clear());

test("warmUpBackend pings /health and never throws", async () => {
  http.get.mockReturnValueOnce(Promise.reject(new Error("offline")));
  expect(() => api.warmUpBackend()).not.toThrow();
  expect(http.get).toHaveBeenCalledWith("/health", { timeout: 90000, skipAuth: true });
  await Promise.resolve();
});

test.each([
  ["registerUser", [{ fullName: "Asha", email: "a@x.com", phone: "9876543210", password: "pw12345678", organization: "" }],
    "/auth/register", { full_name: "Asha", email: "a@x.com", phone: "9876543210", password: "pw12345678", organization: null }],
  ["verifyRegistration", ["a@x.com", "123456"], "/auth/verify-registration", { email: "a@x.com", otp: "123456" }],
  ["resendOTP", ["a@x.com"], "/auth/resend-otp", { email: "a@x.com", purpose: "registration" }],
  ["verifyEmail", ["a@x.com", "123456"], "/auth/verify-email", { email: "a@x.com", otp: "123456" }],
  ["loginWithPassword", ["a@x.com", "pw"], "/auth/login", { email: "a@x.com", password: "pw", location: null }],
  ["googleAuth", ["ya29.token"], "/auth/google", { access_token: "ya29.token", location: null }],
  ["forgotPassword", ["a@x.com"], "/auth/forgot-password", { email: "a@x.com" }],
  ["resetPassword", ["a@x.com", "123456", "New-pass-1"], "/auth/reset-password", { email: "a@x.com", otp: "123456", new_password: "New-pass-1" }],
])("%s posts to %s without sending a bearer token", async (fn, args, url, body) => {
  await api[fn](...args);
  expect(http.post).toHaveBeenCalledWith(url, body, AUTH);
});

test("complaints are submitted without client-supplied identity", async () => {
  await api.submitComplaint("Charged twice", "My card was charged twice for one order.");
  expect(http.post).toHaveBeenCalledWith("/complaint", { subject: "Charged twice", description: "My card was charged twice for one order." }, { timeout: 60000 });
});

test("agent calls carry no email parameter", async () => {
  await api.getAgentQueue({ status: "pending" });
  expect(http.get).toHaveBeenCalledWith("/agent/complaints/queue", { params: { status: "pending" } });
  await api.sendResolution("QX-1", "Fixed", ["step"]);
  expect(http.post).toHaveBeenCalledWith("/agent/send-resolution", { ticket_id: "QX-1", final_solution: "Fixed", steps: ["step"] });
});

test("legacy boolean status updates still work", async () => {
  await api.updateComplaintStatus("QX-1", true, "Refunded");
  expect(http.patch).toHaveBeenCalledWith("/complaint/QX-1/status", { is_resolved: true, admin_solution: "Refunded" });
  await api.updateComplaintStatus("QX-1", "in_progress");
  expect(http.patch).toHaveBeenCalledWith("/complaint/QX-1/status", { status: "in_progress" });
});

test("request interceptor attaches the access token unless skipAuth", () => {
  api.session.save({ access_token: "acc", refresh_token: "ref", user: { id: 1 } });
  const add = interceptors.request[0];
  expect(add({ headers: {} }).headers.Authorization).toBe("Bearer acc");
  expect(add({ headers: {}, skipAuth: true }).headers.Authorization).toBeUndefined();
});

test("an expired access token is refreshed once and the request retried", async () => {
  api.session.save({ access_token: "old", refresh_token: "ref-1", user: { id: 1 } });
  http.post.mockResolvedValueOnce({ data: { access_token: "new", refresh_token: "ref-2", user: { id: 1 } } });
  http.mockResolvedValueOnce({ data: "retried" });
  const { err } = interceptors.response[0];
  const result = await err({ config: { url: "/complaints", headers: {} }, response: { status: 401, data: { code: "TOKEN_EXPIRED" } } });
  expect(http.post).toHaveBeenCalledWith("/auth/refresh", { refresh_token: "ref-1" }, expect.objectContaining({ skipRefresh: true }));
  expect(result).toEqual({ data: "retried" });
  expect(api.session.access).toBe("new");
  expect(api.session.refresh).toBe("ref-2");
});

test("a failed refresh clears the session and signals expiry", async () => {
  api.session.save({ access_token: "old", refresh_token: "ref-1", user: { id: 1 } });
  http.post.mockRejectedValueOnce({ response: { status: 401 } });
  const expired = jest.fn();
  window.addEventListener("qf:session-expired", expired);
  const { err } = interceptors.response[0];
  await expect(err({ config: { headers: {} }, response: { status: 401, data: { code: "TOKEN_EXPIRED" } } })).rejects.toBeTruthy();
  expect(api.session.access).toBeNull();
  expect(expired).toHaveBeenCalled();
});

test("errorMessage prefers the server's detail and lists multiple field errors", () => {
  expect(api.errorMessage({ response: { data: { detail: "Mobile number is required" } } })).toBe("Mobile number is required");
  expect(api.errorMessage({ response: { data: { errors: [{ message: "A" }, { message: "B" }] } } })).toBe("A B");
  expect(api.errorMessage({ code: "ECONNABORTED", response: undefined })).toMatch(/too long/);
});

test("logout revokes server-side and always clears local state", async () => {
  api.session.save({ access_token: "acc", refresh_token: "ref", user: { id: 1 } });
  http.post.mockRejectedValueOnce(new Error("offline"));
  await expect(api.logoutUser()).rejects.toThrow();
  expect(http.post).toHaveBeenCalledWith("/auth/logout", { refresh_token: "ref" }, { skipRefresh: true });
  expect(api.session.access).toBeNull();
});
