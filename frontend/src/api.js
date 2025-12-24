import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const submitComplaint = async (name, email, complaintText) => {
  const response = await api.post("/complaint", {
    name,
    email,
    complaint: complaintText,
  });
  return response.data;
};

export const getAllComplaints = async () => {
  const response = await api.get("/complaints");
  return response.data;
};

export const deleteAllComplaints = async () => {
  const response = await api.delete("/complaints");
  return response.data;
};

export const submitFeedback = async (feedbackData) => {
  const response = await api.post("/feedback", feedbackData);
  return response.data;
};

// Auth API
export const registerUser = async (email, fullName, password) => {
  const response = await api.post("/auth/register", { email, full_name: fullName, password });
  return response.data;
};

export const requestOTP = async (email) => {
  const response = await api.post("/auth/request-otp", { email });
  return response.data;
};

export const verifyOTP = async (email, otp) => {
  const response = await api.post("/auth/verify-otp", { email, otp });
  return response.data;
};

export const loginWithPassword = async (email, password) => {
  const response = await api.post("/auth/login-password", { email, password });
  return response.data;
};

export const forgotPassword = async (email) => {
  const response = await api.post("/auth/forgot-password", { email });
  return response.data;
};

export const resetPassword = async (email, reset_token, new_password) => {
  const response = await api.post("/auth/reset-password", { email, reset_token, new_password });
  return response.data;
};

export const googleAuth = async (token, name) => {
  const response = await api.post("/auth/google", { token, name });
  return response.data;
};

export const googleVerifyOTP = async (email, otp) => {
  const response = await api.post("/auth/google-verify-otp", { email, otp });
  return response.data;
};

export default api;

