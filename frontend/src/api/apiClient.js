import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

export const sendMessageToBackend = async (message) => {
  const response = await axios.post(`${API_BASE_URL}/api/chat`, {
    query: message   // Only query is sent now
  });

  return response.data;
};
