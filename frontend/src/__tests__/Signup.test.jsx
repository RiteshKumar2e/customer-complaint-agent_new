import { act, fireEvent, render, screen } from "@testing-library/react";

jest.mock("../api", () => ({
  warmUpBackend: jest.fn(),
  registerUser: jest.fn(),
  verifyRegistration: jest.fn(),
  resendOTP: jest.fn(),
  updateProfile: jest.fn(),
  session: { save: jest.fn(), setUser: jest.fn() },
  errorMessage: (e, f) => e?.response?.data?.detail || f,
}));

import * as api from "../api";
import Signup from "../components/Signup";

function fill(container, values) {
  for (const [name, value] of Object.entries(values)) {
    fireEvent.change(container.querySelector(`input[name="${name}"]`), { target: { name, value } });
  }
}

const STEP1 = { fullName: "Asha Rao", email: "Asha@X.com", phone: "9876543210" };
const STEP3 = { password: "dummy-pass-123", confirmPassword: "dummy-pass-123" };

function renderSignup(props = {}) {
  const onNavigate = jest.fn();
  const onRegistered = jest.fn();
  const utils = render(<Signup onNavigate={onNavigate} onRegistered={onRegistered} {...props} />);
  const submit = () => fireEvent.submit(utils.container.querySelector("form"));
  const toStep3 = () => {
    fill(utils.container, STEP1);
    submit();
    fill(utils.container, { organization: "Acme" });
    submit();
  };
  return { ...utils, onNavigate, onRegistered, submit, toStep3 };
}

const currentStep = () => document.querySelector('[aria-current="step"]').textContent;

test("starts on step 1 with name, email and mobile only", () => {
  const { container } = renderSignup();
  expect(currentStep()).toMatch(/About you/);
  for (const name of ["fullName", "email", "phone"]) {
    const input = container.querySelector(`input[name="${name}"]`);
    expect(input).toBeInTheDocument();
    expect(input.parentElement.querySelector(".input-icon")).toBeInTheDocument();
  }
  expect(container.querySelector('input[name="password"]')).not.toBeInTheDocument();
});

test("mobile input keeps digits only and at most 10", () => {
  const { container } = renderSignup();
  fill(container, { phone: "+91 98765-43210 99" });
  expect(container.querySelector('input[name="phone"]').value).toBe("9198765432");
});

test.each([
  [{ phone: "98765432" }, "too short"],
  [{ phone: "5876543210" }, "start with 6, 7, 8 or 9"],
  [{ phone: "" }, "Mobile number is required"],
  [{ email: "not-an-email" }, "valid email"],
  [{ fullName: "A" }, "full name"],
])("step 1 blocks %p", (overrides, message) => {
  const { container, submit } = renderSignup();
  fill(container, { ...STEP1, ...overrides });
  submit();
  expect(screen.getByRole("alert")).toHaveTextContent(new RegExp(message, "i"));
  expect(currentStep()).toMatch(/About you/);
});

test("continue and back move between steps and keep what was typed", () => {
  const { container, submit } = renderSignup();
  fill(container, STEP1);
  submit();
  expect(currentStep()).toMatch(/Your needs/);
  fill(container, { organization: "Acme" });
  fireEvent.click(screen.getByRole("button", { name: /^← Back$/ }));
  expect(currentStep()).toMatch(/About you/);
  expect(container.querySelector('input[name="email"]').value).toBe("Asha@X.com");
  submit();
  expect(container.querySelector('input[name="organization"]').value).toBe("Acme");
});

test("step 2 explains how business access works", () => {
  const { container, submit } = renderSignup();
  fill(container, STEP1);
  submit();
  fireEvent.click(screen.getByLabelText(/Handle complaints for my business/));
  expect(screen.getByRole("note")).toHaveTextContent(/administrator can give you support agent or admin access/);
});

test.each([
  [{ password: "short1", confirmPassword: "short1" }, "at least 8"],
  [{ confirmPassword: "different-1" }, "Passwords do not match"],
])("step 3 blocks %p before calling the API", (overrides, message) => {
  const { container, submit, toStep3 } = renderSignup();
  toStep3();
  fill(container, { ...STEP3, ...overrides });
  fireEvent.click(container.querySelector('.terms-row input[type="checkbox"]'));
  submit();
  expect(screen.getByRole("alert")).toHaveTextContent(new RegExp(message, "i"));
  expect(api.registerUser).not.toHaveBeenCalled();
});

test("terms must be accepted", () => {
  const { container, submit, toStep3 } = renderSignup();
  toStep3();
  fill(container, STEP3);
  submit();
  expect(screen.getByRole("alert")).toHaveTextContent("Agree to Terms first");
  expect(api.registerUser).not.toHaveBeenCalled();
});

test("finishing step 3 registers, then the OTP step signs the user in", async () => {
  jest.useFakeTimers();
  api.registerUser.mockResolvedValue({ email: "asha@x.com", expires_in: 300, resend_after: 60 });
  const user = { id: 1, email: "asha@x.com", role: "customer" };
  api.verifyRegistration.mockResolvedValue({ access_token: "a", refresh_token: "r", user });
  const { container, submit, toStep3, onRegistered } = renderSignup();
  toStep3();
  fill(container, STEP3);
  fireEvent.click(container.querySelector('.terms-row input[type="checkbox"]'));
  await act(async () => { submit(); });

  expect(api.registerUser).toHaveBeenCalledWith({
    fullName: "Asha Rao", email: "asha@x.com", phone: "9876543210", password: "dummy-pass-123", organization: "Acme",
  });
  const boxes = screen.getAllByRole("textbox").filter((el) => el.getAttribute("maxlength") === "1");
  expect(boxes).toHaveLength(6);
  fireEvent.paste(boxes[0], { clipboardData: { getData: () => "123456" } });
  await act(async () => { jest.advanceTimersByTime(300); });
  expect(api.verifyRegistration).toHaveBeenCalledWith("asha@x.com", "123456");
  await act(async () => { jest.advanceTimersByTime(4000); });
  expect(onRegistered).toHaveBeenCalledWith(user);
  jest.useRealTimers();
});

test("a taken email sends the user back to step 1 with the reason", async () => {
  api.registerUser.mockRejectedValue({ response: { data: { code: "EMAIL_TAKEN", detail: "An account with this email already exists. Please sign in instead." } } });
  const { container, submit, toStep3 } = renderSignup();
  toStep3();
  fill(container, STEP3);
  fireEvent.click(container.querySelector('.terms-row input[type="checkbox"]'));
  await act(async () => { submit(); });
  expect(currentStep()).toMatch(/About you/);
  expect(screen.getByRole("alert")).toHaveTextContent(/already exists/);
});

test("google prefill fills name and email", () => {
  const { container } = renderSignup({ prefill: { email: "g@x.com", name: "G User" } });
  expect(container.querySelector('input[name="email"]').value).toBe("g@x.com");
  expect(container.querySelector('input[name="fullName"]').value).toBe("G User");
});

test("eye button reveals both password fields", () => {
  const { container, toStep3 } = renderSignup();
  toStep3();
  const pw = container.querySelector('input[name="password"]');
  const confirm = container.querySelector('input[name="confirmPassword"]');
  expect(pw).toHaveAttribute("type", "password");
  fireEvent.click(screen.getByRole("button", { name: /show password/i }));
  expect(pw).toHaveAttribute("type", "text");
  expect(confirm).toHaveAttribute("type", "text");
});
