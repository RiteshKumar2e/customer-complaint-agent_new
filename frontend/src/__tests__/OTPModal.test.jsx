import { act, fireEvent, render, screen } from "@testing-library/react";
import OTPModal from "../components/OTPModal";

function setup(props = {}) {
  const handlers = {
    onVerify: jest.fn(() => Promise.resolve()),
    onVerified: jest.fn(),
    onClose: jest.fn(),
    onResend: jest.fn(() => Promise.resolve()),
  };
  const utils = render(<OTPModal isOpen email="a@x.com" {...handlers} {...props} />);
  const boxes = () => Array.from(document.querySelectorAll(".otp-input"));
  return { ...utils, ...handlers, boxes };
}

function typeCode(boxes, code) {
  code.split("").forEach((digit, i) => fireEvent.change(boxes()[i], { target: { value: digit } }));
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

test("renders nothing when closed", () => {
  const { container } = render(<OTPModal isOpen={false} onVerify={jest.fn()} onClose={jest.fn()} />);
  expect(container).toBeEmptyDOMElement();
});

test("shows six digit boxes", () => {
  const { boxes } = setup();
  expect(boxes()).toHaveLength(6);
});

test("auto-verifies once all six digits are typed, then hands back", async () => {
  const { boxes, onVerify, onVerified } = setup();
  typeCode(boxes, "482913");

  await act(async () => { jest.advanceTimersByTime(200); });
  expect(onVerify).toHaveBeenCalledWith("482913");

  await act(async () => { jest.advanceTimersByTime(2300); });
  expect(onVerified).toHaveBeenCalled();
});

test("rejects non-digit input", () => {
  const { boxes } = setup();
  fireEvent.change(boxes()[0], { target: { value: "a" } });
  expect(boxes()[0]).toHaveValue("");
});

test("pasting a code fills the boxes and strips non-digits", async () => {
  const { boxes, onVerify } = setup();
  fireEvent.paste(boxes()[0], { clipboardData: { getData: () => "48-29 13" } });
  expect(boxes().map((b) => b.value).join("")).toBe("482913");
  await act(async () => { jest.advanceTimersByTime(200); });
  expect(onVerify).toHaveBeenCalledWith("482913");
});

test("a wrong code shows the server message and clears the boxes", async () => {
  const onVerify = jest.fn(() => Promise.reject({ response: { data: { detail: "Invalid OTP" } } }));
  const { boxes } = setup({ onVerify });
  typeCode(boxes, "000000");

  await act(async () => { jest.advanceTimersByTime(200); });
  expect(screen.getByText("Invalid OTP")).toBeInTheDocument();

  await act(async () => { jest.advanceTimersByTime(800); });
  expect(boxes().map((b) => b.value).join("")).toBe("");
});

test("verify button is disabled until the code is complete", () => {
  const { boxes } = setup();
  const verify = screen.getByRole("button", { name: /verify otp/i });
  expect(verify).toBeDisabled();
  typeCode(boxes, "12345");
  expect(verify).toBeDisabled();
});

test("resend is locked for 30s, then requests a new code", async () => {
  const { onResend } = setup();
  expect(screen.getByRole("button", { name: /resend in 30s/i })).toBeDisabled();

  for (let i = 0; i < 30; i++) {
    await act(async () => { jest.advanceTimersByTime(1000); });
  }
  const resend = screen.getByRole("button", { name: /resend otp/i });
  expect(resend).toBeEnabled();

  await act(async () => { fireEvent.click(resend); });
  expect(onResend).toHaveBeenCalledTimes(1);
  expect(screen.getByText(/new code is on its way/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /resend in 30s/i })).toBeDisabled();
});

test("a failed resend shows an error", async () => {
  const onResend = jest.fn(() => Promise.reject({ response: { data: { detail: "Too many requests" } } }));
  setup({ onResend });
  for (let i = 0; i < 30; i++) {
    await act(async () => { jest.advanceTimersByTime(1000); });
  }
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: /resend otp/i })); });
  expect(screen.getByText("Too many requests")).toBeInTheDocument();
});

test("cancel closes the modal", () => {
  const { onClose } = setup();
  fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
  expect(onClose).toHaveBeenCalled();
});
