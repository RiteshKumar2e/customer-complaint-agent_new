import { act, fireEvent, render, screen } from "@testing-library/react";

jest.mock("../api", () => ({
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

const VALID = {
  fullName: "Asha Rao",
  phone: "9876543210",
  email: "Asha@X.com",
  organization: "Acme",
  password: "dummy-pass-123",
  confirmPassword: "dummy-pass-123",
};

function renderSignup(props = {}) {
  const onNavigate = jest.fn();
  const onRegistered = jest.fn();
  const utils = render(<Signup onNavigate={onNavigate} onRegistered={onRegistered} {...props} />);
  const agree = () => utils.container.querySelector('input[type="checkbox"]');
  const submit = () => fireEvent.submit(utils.container.querySelector("form"));
  return { ...utils, onNavigate, onRegistered, agree, submit };
}

test("every field has its icon", () => {
  const { container } = renderSignup();
  for (const name of Object.keys(VALID)) {
    const input = container.querySelector(`input[name="${name}"]`);
    expect(input.parentElement.querySelector(".input-icon")).toBeInTheDocument();
  }
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
  [{ email: "" }, "Email is required"],
  [{ password: "short1", confirmPassword: "short1" }, "at least 8"],
  [{ confirmPassword: "different-1" }, "Passwords do not match"],
])("invalid input %p is rejected before calling the API", (overrides, message) => {
  const { container, agree, submit } = renderSignup();
  fill(container, { ...VALID, ...overrides });
  fireEvent.click(agree());
  submit();
  expect(screen.getByText(new RegExp(message, "i"))).toBeInTheDocument();
  expect(api.registerUser).not.toHaveBeenCalled();
});

test("terms must be accepted", () => {
  const { container, submit } = renderSignup();
  fill(container, VALID);
  submit();
  expect(screen.getByText("Agree to Terms first")).toBeInTheDocument();
  expect(api.registerUser).not.toHaveBeenCalled();
});

test("signup opens the OTP step and only verification signs the user in", async () => {
  jest.useFakeTimers();
  api.registerUser.mockResolvedValue({ email: "asha@x.com", expires_in: 300, resend_after: 60 });
  const user = { id: 1, email: "asha@x.com", role: "customer" };
  api.verifyRegistration.mockResolvedValue({ access_token: "a", refresh_token: "r", user });
  const { container, agree, submit, onRegistered } = renderSignup();
  fill(container, VALID);
  fireEvent.click(agree());
  await act(async () => { submit(); });

  expect(api.registerUser).toHaveBeenCalledWith({
    fullName: "Asha Rao", email: "asha@x.com", phone: "9876543210", password: "dummy-pass-123", organization: "Acme",
  });
  expect(onRegistered).not.toHaveBeenCalled();
  const boxes = screen.getAllByRole("textbox").filter((el) => el.getAttribute("maxlength") === "1");
  expect(boxes).toHaveLength(6);

  fireEvent.paste(boxes[0], { clipboardData: { getData: () => "123456" } });
  await act(async () => { jest.advanceTimersByTime(300); });
  expect(api.verifyRegistration).toHaveBeenCalledWith("asha@x.com", "123456");
  expect(api.session.save).toHaveBeenCalled();
  await act(async () => { jest.advanceTimersByTime(4000); });
  expect(onRegistered).toHaveBeenCalledWith(user);
  jest.useRealTimers();
});

test("server errors (e.g. duplicate mobile) are shown", async () => {
  api.registerUser.mockRejectedValue({ response: { data: { detail: "This mobile number is already registered to another account." } } });
  const { container, agree, submit } = renderSignup();
  fill(container, VALID);
  fireEvent.click(agree());
  await act(async () => { submit(); });
  expect(screen.getByText(/already registered/)).toBeInTheDocument();
});

test("google prefill fills name and email", () => {
  const { container } = renderSignup({ prefill: { email: "g@x.com", name: "G User" } });
  expect(container.querySelector('input[name="email"]').value).toBe("g@x.com");
  expect(container.querySelector('input[name="fullName"]').value).toBe("G User");
});

test("eye button reveals both password fields", () => {
  const { container } = renderSignup();
  const pw = container.querySelector('input[name="password"]');
  const confirm = container.querySelector('input[name="confirmPassword"]');
  expect(pw).toHaveAttribute("type", "password");
  fireEvent.click(screen.getByRole("button", { name: /show password/i }));
  expect(pw).toHaveAttribute("type", "text");
  expect(confirm).toHaveAttribute("type", "text");
});
