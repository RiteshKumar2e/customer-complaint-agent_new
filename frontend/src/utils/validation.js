// Client-side checks that mirror the backend rules (the backend re-validates everything).

export const digitsOnly = (value) => String(value ?? "").replace(/\D/g, "").slice(0, 10);

/** Returns an error message, or "" when the value is a valid Indian mobile number. */
export function validateMobile(value) {
  const v = String(value ?? "");
  if (!v) return "Mobile number is required";
  if (!/^\d+$/.test(v)) return "Mobile number must contain digits only";
  if (v.length < 10) return "Mobile number must be exactly 10 digits (too short)";
  if (v.length > 10) return "Mobile number must be exactly 10 digits (too long)";
  if (!/^[6-9]/.test(v)) return "Indian mobile numbers must start with 6, 7, 8 or 9";
  return "";
}

export function validateEmail(value) {
  const v = String(value ?? "").trim().toLowerCase();
  if (!v) return "Email is required";
  if (v.length > 100 || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) return "Enter a valid email address";
  return "";
}

export function validatePassword(value) {
  const v = String(value ?? "");
  if (v.length < 8) return "Password must be at least 8 characters";
  if (v.length > 128) return "Password must be at most 128 characters";
  if (!/[A-Za-z]/.test(v) || !/\d/.test(v)) return "Password must contain at least one letter and one number";
  return "";
}

export const ROLE_LABELS = { customer: "Customer", agent: "Support Agent", admin: "Administrator" };
export const roleLabel = (role) => ROLE_LABELS[role] || "Customer";

/** Landing page for each role after sign-in. */
export const homePageFor = (user) => (user?.role === "admin" ? "admin" : user?.role === "agent" ? "agent-queue" : "profile");
