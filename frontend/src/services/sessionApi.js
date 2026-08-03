import apiClient from './apiClient';

export const listSessions = async () => {
  const response = await apiClient.get('/sessions');
  return response.data;
};

export const createSession = async (problemName) => {
  const response = await apiClient.post('/sessions', {
    problem_name: problemName,
  });
  return response.data;
};

export const getSession = async (sessionId) => {
  const response = await apiClient.get(`/sessions/${sessionId}`);
  return response.data;
};