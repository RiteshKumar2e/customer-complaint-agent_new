import { installGooglePopupShield } from "../utils/googlePopupShield";

describe("installGooglePopupShield", () => {
  let nativeOpen;
  let popup;

  beforeEach(() => {
    jest.useFakeTimers();
    popup = { closed: "REAL-CROSS-ORIGIN-READ", close: jest.fn(function () { return this; }), name: "gsi" };
    nativeOpen = jest.fn(() => popup);
    window.open = nativeOpen;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("never reads the real popup.closed", () => {
    const dispose = installGooglePopupShield();
    const handle = window.open("https://accounts.google.com");
    expect(handle.closed).toBe(false);
    expect(handle.name).toBe("gsi");
    dispose();
  });

  test("methods are bound to the real popup", () => {
    const dispose = installGooglePopupShield();
    const handle = window.open("x");
    expect(handle.close()).toBe(popup);
    dispose();
  });

  test("reports closed after focus returns for the grace period", () => {
    const dispose = installGooglePopupShield();
    const handle = window.open("x");

    window.dispatchEvent(new Event("focus"));
    jest.advanceTimersByTime(1499);
    expect(handle.closed).toBe(false);
    jest.advanceTimersByTime(1);
    expect(handle.closed).toBe(true);
    dispose();
  });

  test("blur before the grace period cancels the close", () => {
    const dispose = installGooglePopupShield();
    const handle = window.open("x");

    window.dispatchEvent(new Event("focus"));
    jest.advanceTimersByTime(1000);
    window.dispatchEvent(new Event("blur"));
    jest.advanceTimersByTime(5000);
    expect(handle.closed).toBe(false);
    dispose();
  });

  test("a blocked popup (null) is passed through", () => {
    nativeOpen.mockReturnValue(null);
    const dispose = installGooglePopupShield();
    expect(window.open("x")).toBeNull();
    dispose();
  });

  test("dispose restores window.open and is idempotent", () => {
    const dispose = installGooglePopupShield();
    expect(window.open).not.toBe(nativeOpen);
    dispose();
    dispose();
    expect(window.open).toBe(nativeOpen);
  });

  test("a second install is a no-op", () => {
    const dispose = installGooglePopupShield();
    const patched = window.open;
    const disposeSecond = installGooglePopupShield();
    expect(window.open).toBe(patched);
    disposeSecond();
    expect(window.open).toBe(patched);
    dispose();
    expect(window.open).toBe(nativeOpen);
  });

  test("does not clobber someone who patched on top", () => {
    const dispose = installGooglePopupShield();
    const other = jest.fn();
    window.open = other;
    dispose();
    expect(window.open).toBe(other);
  });
});
