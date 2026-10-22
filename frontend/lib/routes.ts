export function captureHref(id?: number | null, observationId?: number | null) {
  if (!Number.isSafeInteger(id) || Number(id) <= 0) return "/dashboard/history";
  return `/dashboard/capture?capture=${id}${Number.isSafeInteger(observationId) && Number(observationId) > 0 ? `#observation-${observationId}` : ""}`;
}
export function memoryHref(id?: number | null) {
  return Number.isSafeInteger(id) && Number(id) > 0 ? `/dashboard/memories/${id}` : "/dashboard/memories";
}
export function safeRedirect(destination: string) {
  return /^\/dashboard(?:\/|[?#]|$)/.test(destination) && !/[\\\u0000-\u0020]/.test(destination) ? destination : "/dashboard";
}
