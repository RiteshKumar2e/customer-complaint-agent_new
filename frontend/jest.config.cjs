module.exports = {
  testEnvironment: "jsdom",
  roots: ["<rootDir>/src", "<rootDir>/test"],
  testMatch: ["**/*.test.{js,jsx}"],
  transform: { "^.+\.[jt]sx?$": "babel-jest" },
  moduleNameMapper: {
    "\.(css|less|scss)$": "identity-obj-proxy",
    "\.(png|jpe?g|gif|svg|webp|ico)$": "<rootDir>/test/mocks/file.js",
    // Animations are irrelevant to behaviour and slow/flaky under jsdom
    "^framer-motion$": "<rootDir>/test/mocks/framer-motion.js",
    "^canvas-confetti$": "<rootDir>/test/mocks/confetti.js",
  },
  setupFilesAfterEnv: ["<rootDir>/test/setup.js"],
  clearMocks: true,
};
