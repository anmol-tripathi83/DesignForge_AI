import apiClient from './apiClient';

export const askQuestion = async (sessionId, answer) => {
  const response = await apiClient.post(`/interview/${sessionId}/ask`, {
    answer,
  });
  return response.data;
};

export const getSessionDetails = async (sessionId) => {
  const response = await apiClient.get(`/sessions/${sessionId}`);
  return response.data;
};