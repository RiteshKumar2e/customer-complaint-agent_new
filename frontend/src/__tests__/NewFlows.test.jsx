import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("../api", () => ({
  warmUpBackend: jest.fn(),
  forgotPassword: jest.fn(),
  resetPassword: jest.fn(),
  adminOverview: jest.fn(),
  adminListUsers: jest.fn(),
  adminUpdateUser: jest.fn(),
  adminCategories: jest.fn(),
  adminAiLogs: jest.fn(),
  adminAiSummary: jest.fn(),
  adminAuditLogs: jest.fn(),
  adminSystem: jest.fn(),
  adminExportComplaints: jest.fn(),
  errorMessage: (e, f = "Something went wrong.") => e?.response?.data?.detail || f,
}));

import * as api from "../api";
import ForgotPassword from "../components/ForgotPassword";
import AdminConsole from "../components/Admin/AdminConsole";
import { digitsOnly, homePageFor, validateEmail, validateMobile, validatePassword } from "../utils/validation";

describe("validation helpers mirror the backend", () => {
  test.each([
    ["9876543210", ""], ["6000000000", ""], ["", "required"], ["987654321", "too short"],
    ["98765432101", "too long"], ["5876543210", "start with 6"], ["98765 4321", "digits only"], ["98765abcde", "digits only"],
  ])("mobile %p", (value, fragment) => {
    const result = validateMobile(value);
    if (fragment) expect(result).toMatch(new RegExp(fragment, "i"));
    else expect(result).toBe("");
  });
  test("digitsOnly strips symbols and caps at 10", () => expect(digitsOnly("+91-98765 43210")).toBe("9198765432"));
  test("email and password", () => {
    expect(validateEmail(" A@B.co ")).toBe("");
    expect(validateEmail("nope")).not.toBe("");
    expect(validatePassword("abcdefg1")).toBe("");
    expect(validatePassword("abcdefgh")).toMatch(/number/);
  });
  test("each role lands on its own dashboard", () => {
    expect(homePageFor({ role: "admin" })).toBe("admin");
    expect(homePageFor({ role: "agent" })).toBe("agent-queue");
    expect(homePageFor({ role: "customer" })).toBe("profile");
  });
});

test("password reset: email, then code + new password", async () => {
  api.forgotPassword.mockResolvedValue({ message: "If an account exists for this email, we sent a 6-digit reset code." });
  api.resetPassword.mockResolvedValue({ message: "Password reset." });
  render(<ForgotPassword onNavigate={jest.fn()} />);
  fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "A@x.com" } });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Send code" })); });
  expect(api.forgotPassword).toHaveBeenCalledWith("a@x.com");

  fireEvent.change(screen.getByLabelText("6-digit code"), { target: { value: "12a3456" } });
  expect(screen.getByLabelText("6-digit code")).toHaveValue("123456");
  fireEvent.change(screen.getByLabelText("New password"), { target: { value: "Brand-new-99" } });
  fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "Different-99" } });
  fireEvent.click(screen.getByRole("button", { name: "Reset password" }));
  expect(screen.getByText("Passwords do not match")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "Brand-new-99" } });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Reset password" })); });
  expect(api.resetPassword).toHaveBeenCalledWith("a@x.com", "123456", "Brand-new-99");
  expect(screen.getByText("Password updated")).toBeInTheDocument();
});

describe("admin console", () => {
  beforeEach(() => {
    api.adminOverview.mockResolvedValue({
      complaints: { total: 3, needs_review: 1, avg_resolution_hours: 2.5, by_status: { open: 2, resolved: 1 },
        by_category: { Billing: 3 }, by_priority: { High: 1 }, daily: [{ date: "2026-11-12", count: 3 }] },
      users: { total: 4, by_role: { customer: 2, agent: 1, admin: 1 }, unverified: 0 },
      ai_last_30_days: { analyses: 3, fallbacks: 1, avg_latency_ms: 900 },
    });
    api.adminListUsers.mockResolvedValue({ items: [
      { id: 1, email: "boss@x.com", full_name: "Boss", role: "admin", email_verified: true, is_active: true, open_assigned: 0 },
      { id: 2, email: "c@x.com", full_name: "Cust", role: "customer", email_verified: true, is_active: true, open_assigned: 0, phone: "9876543210" },
    ], total: 2, total_pages: 1 });
  });

  test("overview shows real figures from the API", async () => {
    render(<AdminConsole user={{ id: 1 }} />);
    expect(await screen.findByText("Need human review")).toBeInTheDocument();
    expect(screen.getByText("2.5 h")).toBeInTheDocument();
  });

  test("promoting a user asks for confirmation and calls the API; own role is locked", async () => {
    window.confirm = jest.fn(() => true);
    api.adminUpdateUser.mockResolvedValue({});
    render(<AdminConsole user={{ id: 1 }} />);
    fireEvent.click(screen.getByRole("tab", { name: "Users & roles" }));
    const own = await screen.findByLabelText("Role for boss@x.com");
    expect(own).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Role for c@x.com"), { target: { value: "agent" } });
    await waitFor(() => expect(api.adminUpdateUser).toHaveBeenCalledWith(2, { role: "agent" }));
    expect(window.confirm).toHaveBeenCalled();
  });

  test("API errors are shown instead of a blank page", async () => {
    api.adminSystem.mockRejectedValue({ response: { data: { detail: "You do not have permission" } } });
    render(<AdminConsole user={{ id: 1 }} />);
    fireEvent.click(screen.getByRole("tab", { name: "System" }));
    expect(await screen.findByText("You do not have permission")).toBeInTheDocument();
  });
});
