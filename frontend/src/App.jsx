import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './store/authStore';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import InterviewPage from './pages/InterviewPage';
import HistoryPage from './pages/HistoryPage';

function App() {
  const { user, fetchUser, isLoading } = useAuthStore();

  useEffect(() => {
    fetchUser();
  }, []);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/" />} />
        <Route path="/register" element={!user ? <RegisterPage /> : <Navigate to="/" />} />
        <Route path="/" element={user ? <DashboardPage /> : <Navigate to="/login" />} />
        <Route path="/interview/:sessionId" element={user ? <InterviewPage /> : <Navigate to="/login" />} />
        <Route path="/history" element={user ? <HistoryPage /> : <Navigate to="/login" />} />
        <Route path="/history/:sessionId" element={user ? <HistoryPage /> : <Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;