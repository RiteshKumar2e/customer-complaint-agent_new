import "@testing-library/jest-dom";

process.env.VITE_API_URL = "http://api.test";

// jsdom has no geolocation; default to "permission denied" so location is optional
Object.defineProperty(global.navigator, "geolocation", {
  configurable: true,
  value: { getCurrentPosition: (ok, fail) => fail(new Error("denied")) },
});

beforeEach(() => {
  localStorage.clear();
  window.alert = jest.fn();
});
