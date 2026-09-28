import { act, fireEvent, render, screen } from "@testing-library/react";

jest.mock("../api", () => ({ registerUser: jest.fn() }));

import * as api from "../api";
import Signup from "../components/Signup";

function fill(container, values) {
  for (const [name, value] of Object.entries(values)) {
    fireEvent.change(container.querySelector(`input[name="${name}"]`), { target: { name, value } });
  }
}

const VALID = {
  fullName: "Asha Rao",
  phone: "+91 98765 43210",
  email: "asha@x.com",
  organization: "Acme",
  password: "dummy-test-password",
  confirmPassword: "dummy-test-password",
};

function renderSignup() {
  const onNavigate = jest.fn();
  const utils = render(<Signup onNavigate={onNavigate} />);
  const agree = () => utils.container.querySelector('input[type="checkbox"]');
  const submit = () => fireEvent.submit(utils.container.querySelector("form"));
  return { ...utils, onNavigate, agree, submit };
}

test("every field has its icon", () => {
  const { container } = renderSignup();
  for (const name of Object.keys(VALID)) {
    const input = container.querySelector(`input[name="${name}"]`);
    expect(input.parentElement.querySelector(".input-icon")).toBeInTheDocument();
  }
});

test("mismatched passwords are rejected before calling the API", () => {
  const { container, agree, submit } = renderSignup();
  fill(container, { ...VALID, confirmPassword: "different" });
  fireEvent.click(agree());
  submit();
  expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
  expect(api.registerUser).not.toHaveBeenCalled();
});

test("terms must be accepted", () => {
  const { container, submit } = renderSignup();
  fill(container, VALID);
  submit();
  expect(screen.getByText("Agree to Terms first")).toBeInTheDocument();
  expect(api.registerUser).not.toHaveBeenCalled();
});

test("successful signup registers and moves to login", async () => {
  jest.useFakeTimers();
  api.registerUser.mockResolvedValue({ id: 1 });
  const { container, agree, submit, onNavigate } = renderSignup();
  fill(container, VALID);
  fireEvent.click(agree());

  await act(async () => { submit(); });
  expect(api.registerUser).toHaveBeenCalledWith(
    "asha@x.com", "Asha Rao", "dummy-test-password", "+91 98765 43210", "Acme", expect.anything(),
  );

  act(() => { jest.advanceTimersByTime(2600); });
  expect(onNavigate).toHaveBeenCalledWith("login");
  jest.useRealTimers();
});

test("failed signup shows an error", async () => {
  api.registerUser.mockRejectedValue(new Error("400"));
  const { container, agree, submit } = renderSignup();
  fill(container, VALID);
  fireEvent.click(agree());
  await act(async () => { submit(); });
  expect(screen.getByText(/Registration failed/)).toBeInTheDocument();
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
