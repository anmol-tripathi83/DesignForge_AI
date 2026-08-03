import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useSessionStore from '../store/sessionStore';

const problems = [
  { id: 'whatsapp', name: 'WhatsApp' },
  { id: 'youtube', name: 'YouTube' },
  { id: 'uber', name: 'Uber' },
  { id: 'instagram', name: 'Instagram' },
  { id: 'tinyurl', name: 'TinyURL' },
];

const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { sessions, fetchSessions, startSession, isLoading } = useSessionStore();

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleStartInterview = async (problemName) => {
    try {
      const session = await startSession(problemName);
      navigate(`/interview/${session.id}`);
    } catch (error) {
      alert('Failed to start interview. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">DesignMentor AI</h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">Welcome, {user?.full_name || user?.email}</span>
            <button
              onClick={() => navigate('/history')}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              History
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Problems Grid */}
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Choose a System Design Problem</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {problems.map((problem) => (
            <div
              key={problem.id}
              className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 cursor-pointer border border-gray-200 hover:border-indigo-300"
              onClick={() => handleStartInterview(problem.name)}
            >
              <h3 className="text-lg font-medium text-gray-900 mb-2">{problem.name}</h3>
              <p className="text-sm text-gray-500 mb-4">Practice system design for {problem.name}</p>
              <button
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition-colors text-sm font-medium"
                disabled={isLoading}
              >
                {isLoading ? 'Starting...' : 'Start Interview'}
              </button>
            </div>
          ))}
        </div>

        {/* Recent Sessions */}
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Sessions</h2>
        {sessions.length === 0 ? (
          <p className="text-gray-500">No sessions yet. Start your first interview!</p>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Problem
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sessions.slice(0, 5).map((session) => (
                  <tr key={session.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {session.problem_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        session.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : session.status === 'in_progress'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {session.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(session.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {session.status === 'in_progress' && (
                        <button
                          onClick={() => navigate(`/interview/${session.id}`)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          Resume
                        </button>
                      )}
                      {session.status === 'completed' && (
                        <button
                          onClick={() => navigate(`/history/${session.id}`)}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          View
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
};

export default DashboardPage;