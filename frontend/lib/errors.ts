import { AxiosError } from "axios";
export function errorMessage(error: unknown, fallback: string) {
  if (!(error instanceof AxiosError)) return fallback;
  const detail: unknown = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(item => typeof item?.msg === "string" ? item.msg : "Check the submitted fields").join(". ");
  return fallback;
}
