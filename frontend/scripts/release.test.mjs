import test from "node:test";
import assert from "node:assert/strict";
import { configuredPort } from "./start.mjs";
import { validateApiOrigin } from "../lib/api-origin.mjs";

test("runtime PORT defaults locally and accepts Cloud Run non-default ports", () => {
  assert.equal(configuredPort("8087"), "8087");
  const previous = process.env.PORT; delete process.env.PORT;
  try { assert.equal(configuredPort(), "3000"); }
  finally { if (previous !== undefined) process.env.PORT = previous; }
  for (const port of ["", "0", "65536", "8080 --inspect", "1.5", "-1"]) assert.throws(() => configuredPort(port));
});

test("release API origin fails closed for missing, loopback, insecure and secret-bearing inputs", () => {
  assert.equal(validateApiOrigin({ NEXT_PUBLIC_API_URL: "https://api.example.com" }), "https://api.example.com");
  for (const value of [undefined, "http://localhost:8000", "https://localhost", "https://localhost.", "https://sub.localhost.", "https://sub.localhost", "https://127.1", "https://2130706433", "http://0.0.0.0", "https://[::1]", "https://[::ffff:127.0.0.1]", "http://api.example.com", "https://user:secret@example.com", "https://api.example.com/path", "https://api.example.com?key=secret", "https://api.example.com#fragment", "javascript:alert(1)"]) assert.throws(() => validateApiOrigin({ NEXT_PUBLIC_API_URL: value }));
  assert.throws(() => validateApiOrigin({ NEXT_PUBLIC_API_URL: "https://api.example.com", NEXT_PUBLIC_GEMINI_API_KEY: "synthetic" }));
});

test("explicit local opt-in allows loopback only and never weakens public origin HTTPS", () => {
 assert.equal(validateApiOrigin({ NEXT_PUBLIC_API_URL: "http://127.0.0.1:8100", ALLOW_LOCAL_API_ORIGIN: "1" }), "http://127.0.0.1:8100");
 assert.throws(() => validateApiOrigin({ NEXT_PUBLIC_API_URL: "http://api.example.com", ALLOW_LOCAL_API_ORIGIN: "1" }));
});
