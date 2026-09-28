import fs from "fs";
import path from "path";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("../api", () => ({
  googleAuth: jest.fn(() => Promise.resolve({ requires_otp: true })),
  googleVerifyOTP: jest.fn(),
  loginWithPassword: jest.fn(),
  warmUpBackend: jest.fn(),
}));

// Capture the options Login passes to useGoogleLogin so tests can drive the flow
let googleOptions;
jest.mock("@react-oauth/google", () => ({
  GoogleOAuthProvider: ({ children }) => children,
  useGoogleLogin: (options) => {
    googleOptions = options;
    return jest.fn();
  },
}));

import * as api from "../api";
import Login from "../components/Login";

const ADMIN = "riteshkumar90359@gmail.com";

function renderLogin(props = {}) {
  const handlers = { onNavigate: jest.fn(), onLoginSuccess: jest.fn() };
  const utils = render(<Login {...handlers} {...props} />);
  return {
    ...utils,
    ...handlers,
    email: screen.getByPlaceholderText("Enter your email"),
    password: screen.getByPlaceholderText("••••••••"),
  };
}

function submit(container) {
  fireEvent.submit(container.querySelector("form.auth-form"));
}

beforeEach(() => {
  global.fetch = jest.fn(() => Promise.resolve({ json: () => Promise.resolve({ email: "g@x.com", name: "G User" }) }));
});

test("wakes the backend on mount so the OTP request skips the cold start", () => {
  renderLogin();
  expect(api.warmUpBackend).toHaveBeenCalledTimes(1);
});

test("email and password fields both have their icon", () => {
  const { email, password } = renderLogin();
  for (const input of [email, password]) {
    expect(input.parentElement.querySelector(".input-icon")).toBeInTheDocument();
  }
});

test("eye button toggles password visibility", () => {
  const { password } = renderLogin();
  expect(password).toHaveAttribute("type", "password");
  fireEvent.click(screen.getByRole("button", { name: /show password/i }));
  expect(password).toHaveAttribute("type", "text");
  fireEvent.click(screen.getByRole("button", { name: /hide password/i }));
  expect(password).toHaveAttribute("type", "password");
});

test("successful password login stores the session and reports the user", async () => {
  const user = { email: "a@x.com", full_name: "A" };
  api.loginWithPassword.mockResolvedValue({ access_token: "jwt", user });
  const { container, email, password, onLoginSuccess } = renderLogin();

  fireEvent.change(email, { target: { value: "a@x.com" } });
  fireEvent.change(password, { target: { value: "pw" } });
  submit(container);

  await waitFor(() => expect(onLoginSuccess).toHaveBeenCalledWith(user));
  expect(api.loginWithPassword).toHaveBeenCalledWith("a@x.com", "pw", "India");
  expect(localStorage.getItem("token")).toBe("jwt");
  expect(JSON.parse(localStorage.getItem("user"))).toEqual(user);
});

test("wrong password shows a helpful message", async () => {
  api.loginWithPassword.mockRejectedValue({ response: { data: { detail: "Password is wrong. Try forgot password" } } });
  const { container, email, password, onLoginSuccess } = renderLogin();
  fireEvent.change(email, { target: { value: "a@x.com" } });
  fireEvent.change(password, { target: { value: "bad" } });
  submit(container);

  expect(await screen.findByText(/Try 'Forgot Access' below/)).toBeInTheDocument();
  expect(onLoginSuccess).not.toHaveBeenCalled();
});

test("admin portal refuses non-admin emails without calling the API", () => {
  const { container, email, password } = renderLogin({ isAdminMode: true });
  fireEvent.change(email, { target: { value: "someone@x.com" } });
  fireEvent.change(password, { target: { value: "pw" } });
  submit(container);

  expect(screen.getByText(/not authorized/i)).toBeInTheDocument();
  expect(api.loginWithPassword).not.toHaveBeenCalled();
});

test("Google sign-in requests the OTP immediately, without waiting for location", async () => {
  // A permission prompt that is never answered used to block the OTP request
  const geo = jest.spyOn(navigator.geolocation, "getCurrentPosition").mockImplementation(() => {});
  renderLogin();

  await act(async () => {
    await googleOptions.onSuccess({ access_token: "google-token" });
  });

  expect(api.googleAuth).toHaveBeenCalledWith("g@x.com", "G User");
  expect(document.querySelector(".otp-input")).toBeInTheDocument();
  expect(geo).not.toHaveBeenCalled();
  geo.mockRestore();
});

test("Google sign-in in admin mode blocks non-admin accounts", async () => {
  renderLogin({ isAdminMode: true });
  await act(async () => {
    await googleOptions.onSuccess({ access_token: "t" });
  });
  expect(screen.getByText(/Unauthorized account/)).toBeInTheDocument();
  expect(api.googleAuth).not.toHaveBeenCalled();
});

test("Google OTP failure closes the modal and shows the reason", async () => {
  api.googleAuth.mockRejectedValueOnce({ response: { data: { detail: "Email service down" } } });
  renderLogin();
  await act(async () => {
    await googleOptions.onSuccess({ access_token: "t" });
  });
  expect(await screen.findByText("Email service down")).toBeInTheDocument();
  expect(document.querySelector(".otp-input")).not.toBeInTheDocument();
});

test("admin email passes the admin-mode check", async () => {
  global.fetch = jest.fn(() => Promise.resolve({ json: () => Promise.resolve({ email: ADMIN, name: "Admin" }) }));
  renderLogin({ isAdminMode: true });
  await act(async () => {
    await googleOptions.onSuccess({ access_token: "t" });
  });
  expect(api.googleAuth).toHaveBeenCalledWith(ADMIN, "Admin");
});

describe("input icon CSS", () => {
  // Layout can't be measured in jsdom, so guard the fix at the stylesheet level:
  // translateY centering gets overridden by framer-motion / ButtonReset.css.
  const css = fs.readFileSync(path.join(__dirname, "../styles/Auth.css"), "utf8");
  const rule = (selector) => css.match(new RegExp(`\\n${selector.replace(".", "\\.")} \\{([^}]*)\\}`))[1];

  test.each([".input-icon", ".password-toggle"])("%s is centered without transform", (selector) => {
    const body = rule(selector);
    expect(body).toMatch(/top:\s*0/);
    expect(body).toMatch(/bottom:\s*0/);
    expect(body).toMatch(/margin:\s*auto 0/);
    expect(body).not.toMatch(/transform/);
  });
});

describe("remembered login", () => {
  test("an old saved password is purged and only the email is restored", () => {
    localStorage.setItem("saved_creds", JSON.stringify({ email: "a@x.com", password: "dummy-old-password" }));
    const { email, password } = renderLogin();

    expect(email).toHaveValue("a@x.com");
    expect(password).toHaveValue("");
    expect(JSON.parse(localStorage.getItem("saved_creds"))).toEqual({ email: "a@x.com" });
  });

  test("logging in again never writes the password to storage", async () => {
    localStorage.setItem("saved_creds", JSON.stringify({ email: "a@x.com" }));
    api.loginWithPassword.mockResolvedValue({ access_token: "jwt", user: { email: "a@x.com" } });
    const { container, password, onLoginSuccess } = renderLogin();

    fireEvent.change(password, { target: { value: "dummy-old-password" } });
    submit(container);

    await waitFor(() => expect(onLoginSuccess).toHaveBeenCalled());
    expect(localStorage.getItem("saved_creds")).not.toContain("dummy-old-password");
  });

  test("corrupt saved data is discarded", () => {
    localStorage.setItem("saved_creds", "{not json");
    renderLogin();
    expect(localStorage.getItem("saved_creds")).toBeNull();
  });
});
