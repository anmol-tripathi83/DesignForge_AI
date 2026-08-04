import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useSessionStore from '../store/sessionStore';

const problems = [
  'WhatsApp',
  'YouTube',
  'Uber',
  'Instagram',
  'TinyURL',
  'Netflix',
  'Twitter',
  'Dropbox',
];

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { sessions, fetchSessions, startSession, isLoading } = useSessionStore();
  const [customTopic, setCustomTopic] = useState('');
  const [randomTopic, setRandomTopic] = useState('');

  useEffect(() => {
    fetchSessions();
    setRandomTopic(problems[Math.floor(Math.random() * problems.length)]);
  }, []);

  const handleStartInterview = async (topic) => {
    if (!topic.trim()) return;
    try {
      const session = await startSession(topic.trim());
      navigate(`/interview/${session.id}`);
    } catch (error) {
      alert('Failed to start interview. Please try again.');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">
              D
            </div>
            <h1 className="text-2xl font-bold text-gray-900">DesignForge</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600 hidden sm:inline">
              {user?.full_name || user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-gray-700 transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero */}
        <div className="text-center mb-10">
          <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
            System Design Interview Practice
          </h2>
          <p className="mt-2 text-lg text-gray-600 max-w-2xl mx-auto">
            Get real‑time feedback from an AI senior interviewer. Choose a topic, try a random one, or type your own.
          </p>
        </div>

        {/* Custom Topic Input */}
        <div className="max-w-2xl mx-auto mb-10">
          <div className="flex items-center space-x-3 bg-white rounded-xl shadow-md p-2 border border-gray-200">
            <input
              type="text"
              value={customTopic}
              onChange={(e) => setCustomTopic(e.target.value)}
              placeholder="Type any system design topic (e.g., Splitwise, Amazon, etc.)"
              className="flex-1 px-4 py-2 border-0 focus:ring-0 text-gray-800 placeholder-gray-400"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && customTopic.trim()) {
                  handleStartInterview(customTopic);
                }
              }}
            />
            <button
              onClick={() => handleStartInterview(customTopic)}
              disabled={!customTopic.trim() || isLoading}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              Start
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1 text-center">
            Press Enter or click Start to begin your custom interview
          </p>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {/* Random Topic */}
          <div
            className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white cursor-pointer hover:shadow-xl transition transform hover:scale-[1.02]"
            onClick={() => handleStartInterview(randomTopic)}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm opacity-80">Feeling lucky?</p>
                <h3 className="text-2xl font-bold mt-1">🎲 Random Topic</h3>
                <p className="mt-2 text-indigo-100">
                  Try: <strong>{randomTopic}</strong>
                </p>
              </div>
              <div className="text-5xl opacity-80">🎯</div>
            </div>
          </div>

          {/* History */}
          <div
            className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200 cursor-pointer hover:shadow-xl transition transform hover:scale-[1.02]"
            onClick={() => navigate('/history')}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Your progress</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">📚 History</h3>
                <p className="mt-2 text-gray-600">
                  {sessions.length} interview{sessions.length !== 1 ? 's' : ''} completed
                </p>
              </div>
              <div className="text-5xl opacity-60">📖</div>
            </div>
          </div>
        </div>

        {/* Suggested Topics */}
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Suggested Topics</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {problems.map((problem) => (
            <div
              key={problem}
              className="bg-white rounded-xl shadow-md hover:shadow-lg transition cursor-pointer p-4 border border-gray-100 hover:border-indigo-300 flex flex-col items-center text-center"
              onClick={() => handleStartInterview(problem)}
            >
              <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-lg mb-2">
                {problem.charAt(0)}
              </div>
              <h4 className="font-medium text-gray-800">{problem}</h4>
              <p className="text-xs text-gray-400 mt-1">System Design</p>
            </div>
          ))}
        </div>

        {/* Recent Sessions */}
        {sessions.length > 0 && (
          <div className="mt-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Sessions</h3>
            <div className="bg-white rounded-xl shadow overflow-hidden">
              <div className="divide-y divide-gray-200">
                {sessions.slice(0, 3).map((session) => (
                  <div key={session.id} className="p-4 flex justify-between items-center hover:bg-gray-50">
                    <div>
                      <p className="font-medium text-gray-800">{session.problem_name}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(session.created_at).toLocaleString()}
                      </p>
                    </div>
                    <button
                      onClick={() => navigate(`/interview/${session.id}`)}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
                    >
                      {session.status === 'completed' ? 'View' : 'Resume'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default DashboardPage;