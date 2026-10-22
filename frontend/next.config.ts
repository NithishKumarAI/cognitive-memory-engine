import type { NextConfig } from "next";
import { validateApiOrigin } from "./lib/api-origin.mjs";

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      { key: "Permissions-Policy", value: "camera=(), microphone=(self), geolocation=()" },
      { key: "X-Frame-Options", value: "DENY" },
    ] }];
  },
  reactCompiler: true,
};

export default function config(phase: string): NextConfig {
  if (phase === "phase-production-build") validateApiOrigin(process.env);
  return nextConfig;
}
