// Only used by Jest (Vite has its own transform). Kept to the test env so it
// can never change what `vite build` produces.

// Jest runs CommonJS, where `import.meta` is a syntax error; map Vite's
// `import.meta.env` onto `process.env` for tests.
function importMetaEnvToProcessEnv({ types: t }) {
  return {
    visitor: {
      MemberExpression(path) {
        const { object, property } = path.node;
        if (
          t.isMetaProperty(object) &&
          object.meta.name === "import" &&
          object.property.name === "meta" &&
          t.isIdentifier(property, { name: "env" })
        ) {
          path.replaceWith(t.memberExpression(t.identifier("process"), t.identifier("env")));
        }
      },
    },
  };
}

module.exports = (api) => {
  const isTest = api.env("test");
  return isTest
    ? {
        presets: [
          ["@babel/preset-env", { targets: { node: "current" } }],
          ["@babel/preset-react", { runtime: "automatic" }],
        ],
        plugins: [importMetaEnvToProcessEnv],
      }
    : {};
};
