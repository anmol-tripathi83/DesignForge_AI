import { create } from 'zustand';
import { login as loginApi, register as registerApi, logout as logoutApi, getMe } from '../services/authApi';

const useAuthStore = create((set, get) => ({
  user: null,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const user = await loginApi(email, password);
      set({ user, isLoading: false });
      return user;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Login failed', isLoading: false });
      throw error;
    }
  },

  register: async (email, password, fullName) => {
    set({ isLoading: true, error: null });
    try {
      const user = await registerApi(email, password, fullName);
      set({ isLoading: false });
      return user;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Registration failed', isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    try {
      await logoutApi();
      set({ user: null, isLoading: false });
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Logout failed', isLoading: false });
    }
  },

  fetchUser: async () => {
    set({ isLoading: true });
    try {
      const user = await getMe();
      set({ user, isLoading: false });
    } catch (error) {
      set({ user: null, isLoading: false });
    }
  },
}));

export default useAuthStore;