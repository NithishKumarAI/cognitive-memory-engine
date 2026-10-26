import { isAxiosError } from "axios";

export class AccountCreatedError extends Error {
  constructor() { super("Your account was created, but automatic sign-in did not finish. Please sign in to continue."); }
}

// Never render raw provider/server detail: validation payloads can include submitted input.
export function authFeedback(error: unknown, operation: "register" | "login") {
  if (!isAxiosError(error)) return operation === "login" ? "Unable to verify your session. Please try signing in again." : "Unable to create your account. Please try again.";
  if (!error.response) return "Unable to connect to the LearnTrack server. Check that the backend is running.";
  const { status, data } = error.response;
  if (status === 403 && operation === "register") return "Registration is temporarily disabled. Please try again later.";
  if (status === 400 || status === 409) {
    if (data?.detail === "Email already registered") return "Email already registered. Try signing in.";
    if (data?.detail === "Username already exists") return "Username already taken. Choose another username.";
  }
  if (status === 422 || status === 400) return "Some form values are invalid. Please check your details.";
  if (status === 401) return "Invalid email or password.";
  if (status === 429) return "Too many attempts. Please wait before trying again.";
  if (status >= 500) return "The LearnTrack database or service is unavailable. Please try again later.";
  return operation === "login" ? "Unable to sign in. Please try again." : "Unable to create your account. Please try again.";
}

export function passwordValidation(value: string): true | string {
  if (Array.from(value).length < 8) return "Use at least 8 characters.";
  if (!value.trim() || value.includes("\0")) return "Use a non-blank password without null characters.";
  if (new TextEncoder().encode(value).length > 72) return "Use at most 72 UTF-8 bytes (some symbols use more than one byte).";
  return true;
}
