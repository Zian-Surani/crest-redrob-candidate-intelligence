const API_ROOT = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export async function api(path, options = {}) {
  const token = localStorage.getItem("crest_token");
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body)
    headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response;
  try {
    response = await fetch(`${API_ROOT}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(
      "Could not reach the CREST backend. Start backend/run.ps1 and retry.",
      0,
    );
  }
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) {
    const message =
      typeof payload === "object" ? payload.detail || payload.message : payload;
    throw new ApiError(
      message || `Request failed (${response.status})`,
      response.status,
      payload,
    );
  }
  return payload;
}

export function apiUrl(path) {
  return `${API_ROOT}${path}`;
}

export function inr(value, compact = false) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
    notation: compact ? "compact" : "standard",
  }).format(value || 0);
}

export function initials(name = "") {
  return (
    name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join("")
      .toUpperCase() || "C"
  );
}
