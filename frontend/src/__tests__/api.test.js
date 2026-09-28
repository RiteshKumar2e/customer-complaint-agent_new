jest.mock("axios", () => {
  const instance = {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    post: jest.fn(() => Promise.resolve({ data: { ok: true } })),
    patch: jest.fn(() => Promise.resolve({ data: {} })),
    delete: jest.fn(() => Promise.resolve({ data: {} })),
  };
  return { __esModule: true, default: { create: jest.fn(() => instance) }, instance };
});

import { instance as http } from "axios";
import * as api from "../api";

const AUTH_TIMEOUT = 90000;

describe("api client", () => {
  test("warmUpBackend pings /health with the long cold-start timeout", () => {
    api.warmUpBackend();
    expect(http.get).toHaveBeenCalledWith("/health", { timeout: AUTH_TIMEOUT });
  });

  test("warmUpBackend never throws when the backend is down", async () => {
    http.get.mockReturnValueOnce(Promise.reject(new Error("offline")));
    expect(() => api.warmUpBackend()).not.toThrow();
    await Promise.resolve(); // let the rejection settle without an unhandled error
  });

  test.each([
    ["requestOTP", ["a@x.com"], "/auth/request-otp", { email: "a@x.com" }],
    ["verifyOTP", ["a@x.com", "123456"], "/auth/verify-otp", { email: "a@x.com", otp: "123456", location: null }],
    ["googleAuth", ["a@x.com", "A"], "/auth/google", { token: "a@x.com", name: "A", location: null }],
    ["googleVerifyOTP", ["a@x.com", "1"], "/auth/google-verify-otp", { email: "a@x.com", otp: "1", location: null }],
    ["loginWithPassword", ["a@x.com", "pw"], "/auth/login-password", { email: "a@x.com", password: "pw", location: null }],
    ["forgotPassword", ["a@x.com"], "/auth/forgot-password", { email: "a@x.com" }],
  ])("%s posts to %s with the auth timeout", async (fn, args, url, body) => {
    const data = await api[fn](...args);
    expect(http.post).toHaveBeenCalledWith(url, body, { timeout: AUTH_TIMEOUT });
    expect(data).toEqual({ ok: true });
  });

  test("registerUser maps fields to the backend's snake_case", async () => {
    await api.registerUser("a@x.com", "Asha", "pw", "99", "Org", null);
    expect(http.post).toHaveBeenCalledWith(
      "/auth/register",
      { email: "a@x.com", full_name: "Asha", password: "pw", phone: "99", organization: "Org", profile_image: null },
      { timeout: AUTH_TIMEOUT },
    );
  });

  test("agent queue encodes the agent email and filters", async () => {
    await api.getAgentQueue("agent+1@x.com", { status: "pending", priority: "High" });
    const url = http.get.mock.calls[0][0];
    expect(url).toMatch(/^\/agent\/complaints\/queue\?/);
    const params = new URLSearchParams(url.split("?")[1]);
    expect(params.get("agent_email")).toBe("agent+1@x.com");
    expect(params.get("status")).toBe("pending");
    expect(params.get("priority")).toBe("High");
  });

  test("validateSolution and sendResolution send the agent payload", async () => {
    await api.validateSolution("ag@x.com", "QX-1", "Fix", ["a"]);
    expect(http.post).toHaveBeenCalledWith("/agent/validate-solution", {
      agent_email: "ag@x.com", ticket_id: "QX-1", draft_solution: "Fix", steps: ["a"],
    });
    await api.sendResolution("ag@x.com", "QX-1", "Fix");
    expect(http.post).toHaveBeenCalledWith("/agent/send-resolution", {
      agent_email: "ag@x.com", ticket_id: "QX-1", final_solution: "Fix", steps: null,
    });
  });

  test("updateComplaintStatus only sends admin_solution when given", async () => {
    await api.updateComplaintStatus("QX-1", true);
    expect(http.patch).toHaveBeenLastCalledWith("/complaint/QX-1/status", { is_resolved: true });
    await api.updateComplaintStatus("QX-1", true, "Done");
    expect(http.patch).toHaveBeenLastCalledWith("/complaint/QX-1/status", { is_resolved: true, admin_solution: "Done" });
  });

  test("getAllComplaints encodes the email filter", async () => {
    await api.getAllComplaints("a b@x.com");
    expect(http.get).toHaveBeenLastCalledWith("/complaints?email=a%20b%40x.com");
    await api.getAllComplaints();
    expect(http.get).toHaveBeenLastCalledWith("/complaints");
  });
});
