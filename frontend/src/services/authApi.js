import apiClient from './apiClient';

export const register = async (email, password, fullName) => {
  const response = await apiClient.post('/auth/register', {
    email,
    password,
    full_name: fullName,
  });
  return response.data;
};

export const login = async (email, password) => {
  const response = await apiClient.post('/auth/login', {
    email,
    password,
  });
  return response.data;
};

export const logout = async () => {
  const response = await apiClient.post('/auth/logout');
  return response.data;
};

export const getMe = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};