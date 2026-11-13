import fs from "fs";
import path from "path";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("../api", () => ({
  googleAuth: jest.fn(() => Promise.resolve({ requires_otp: true, email: "g@x.com", purpose: "login" })),
  googleVerifyOTP: jest.fn(),
  loginWithPassword: jest.fn(),
  warmUpBackend: jest.fn(),
  verifyEmail: jest.fn(),
  resendOTP: jest.fn(() => Promise.resolve({})),
  errorMessage: (e, f) => e?.response?.data?.detail || f,
  session: {
    save: ({ access_token, user }) => {
      globalThis.localStorage.setItem("token", access_token);
      globalThis.localStorage.setItem("user", JSON.stringify(user));
    },
  },
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

test("wrong credentials show the server's generic message", async () => {
  api.loginWithPassword.mockRejectedValue({ response: { status: 401, data: { detail: "Invalid email or password.", code: "INVALID_CREDENTIALS" } } });
  const { container, email, password, onLoginSuccess } = renderLogin();
  fireEvent.change(email, { target: { value: "a@x.com" } });
  fireEvent.change(password, { target: { value: "bad" } });
  submit(container);

  expect(await screen.findByText("Invalid email or password.")).toBeInTheDocument();
  expect(onLoginSuccess).not.toHaveBeenCalled();
});

test("there is no client-side admin allow-list: the server decides roles", async () => {
  api.loginWithPassword.mockResolvedValue({ access_token: "jwt", user: { email: "someone@x.com", role: "customer" } });
  const { container, email, password, onLoginSuccess } = renderLogin({ isAdminMode: true });
  fireEvent.change(email, { target: { value: "someone@x.com" } });
  fireEvent.change(password, { target: { value: "pw" } });
  submit(container);
  await waitFor(() => expect(onLoginSuccess).toHaveBeenCalledWith({ email: "someone@x.com", role: "customer" }));
});

test("an unverified account is sent a code and verifies inside the OTP modal", async () => {
  api.loginWithPassword.mockRejectedValue({ response: { status: 403, data: { code: "EMAIL_NOT_VERIFIED", detail: "Verify" } } });
  const { container, email, password } = renderLogin();
  fireEvent.change(email, { target: { value: "Old@X.com" } });
  fireEvent.change(password, { target: { value: "pw" } });
  submit(container);
  await waitFor(() => expect(api.resendOTP).toHaveBeenCalledWith("old@x.com", "verify_email"));
  expect(document.querySelector(".otp-input")).toBeInTheDocument();
});

test("Google sign-in sends the access token for server-side verification, without waiting for location", async () => {
  const geo = jest.spyOn(navigator.geolocation, "getCurrentPosition").mockImplementation(() => {});
  renderLogin();
  await act(async () => {
    await googleOptions.onSuccess({ access_token: "google-token" });
  });
  expect(api.googleAuth).toHaveBeenCalledWith("google-token");
  expect(document.querySelector(".otp-input")).toBeInTheDocument();
  expect(geo).not.toHaveBeenCalled();
  geo.mockRestore();
});

test("Google failure shows the reason and no OTP modal", async () => {
  api.googleAuth.mockRejectedValueOnce({ response: { data: { detail: "Email service down" } } });
  renderLogin();
  await act(async () => {
    await googleOptions.onSuccess({ access_token: "t" });
  });
  expect(await screen.findByText("Email service down")).toBeInTheDocument();
  expect(document.querySelector(".otp-input")).not.toBeInTheDocument();
});

test("a Google user without an account is sent to signup with prefilled details", async () => {
  api.googleAuth.mockRejectedValueOnce({ response: { status: 404, data: { code: "ACCOUNT_NOT_FOUND" } } });
  const { onNavigate } = renderLogin();
  await act(async () => {
    await googleOptions.onSuccess({ access_token: "t" });
  });
  expect(onNavigate).toHaveBeenCalledWith("signup", { email: "g@x.com", name: "G User" });
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
