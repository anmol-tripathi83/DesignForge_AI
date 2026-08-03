import { create } from 'zustand';
import { listSessions, createSession, getSession } from '../services/sessionApi';

const useSessionStore = create((set, get) => ({
  sessions: [],
  currentSession: null,
  isLoading: false,
  error: null,

  fetchSessions: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await listSessions();
      set({ sessions: data, isLoading: false });
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to fetch sessions', isLoading: false });
    }
  },

  startSession: async (problemName) => {
    set({ isLoading: true, error: null });
    try {
      const newSession = await createSession(problemName);
      // Add to list
      set((state) => ({
        sessions: [newSession, ...state.sessions],
        isLoading: false,
      }));
      return newSession;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to create session', isLoading: false });
      throw error;
    }
  },

  fetchSessionDetails: async (sessionId) => {
    set({ isLoading: true, error: null });
    try {
      const data = await getSession(sessionId);
      set({ currentSession: data, isLoading: false });
      return data;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Failed to fetch session', isLoading: false });
      throw error;
    }
  },
}));

export default useSessionStore;