/** Build-time checks only. Never include server secrets in public configuration. */
/** @param {Record<string, string | undefined>} env */
export function validateApiOrigin(env) {
  if (Object.keys(env).some(key => key.startsWith("NEXT_PUBLIC_") && key !== "NEXT_PUBLIC_API_URL")) {
    throw new Error("Only NEXT_PUBLIC_API_URL is permitted as public build configuration.");
  }
  let url;
  try { url = new URL(env.NEXT_PUBLIC_API_URL ?? ""); }
  catch { throw new Error("Set NEXT_PUBLIC_API_URL to the browser-reachable HTTPS API origin before building."); }
  const host = url.hostname.toLowerCase().replace(/\.+$/, "");
  const local = host === "localhost" || host.endsWith(".localhost") || host === "0.0.0.0" || host === "[::]" || host === "[::1]" || host.startsWith("127.") || host.startsWith("[::ffff:7f");
  const localOptIn = env.ALLOW_LOCAL_API_ORIGIN === "1" && local;
  if (url.username || url.password || url.search || url.hash || url.pathname !== "/" ||
      !["http:", "https:"].includes(url.protocol) ||
      (!localOptIn && (local || url.protocol !== "https:"))) {
    throw new Error("Use an HTTPS API origin without credentials, path, query or fragment. Loopback requires the explicit local-test build opt-in.");
  }
  return url.origin;
}
