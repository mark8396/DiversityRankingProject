module.exports = new Proxy(
  {},
  {
    get: (_, prop) => {
      if (prop === "__esModule") return false;
      if (typeof prop !== "string") return undefined;
      return prop;
    },
  }
);
