import { spawn } from "node:child_process";
import { pathToFileURL } from "node:url";

export function configuredPort(value = process.env.PORT) {
  const input = value ?? "3000";
  if (!/^\d+$/.test(input) || Number(input) < 1 || Number(input) > 65535) {
    throw new Error("PORT must be an integer between 1 and 65535.");
  }
  return String(Number(input));
}

export function start() {
  const child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "0.0.0.0", "--port", configuredPort()], { stdio: "inherit" });
  for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => child.kill(signal));
  child.on("error", () => { console.error("Unable to start frontend."); process.exitCode = 1; });
  child.on("exit", (code, signal) => { process.exitCode = code ?? (signal ? 1 : 0); });
  return child;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) start();
