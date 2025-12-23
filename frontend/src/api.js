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

export default api;
