import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useSessionStore from '../store/sessionStore';

const HistoryPage = () => {
  const navigate = useNavigate();
  const { sessions, fetchSessions, isLoading } = useSessionStore();

  useEffect(() => {
    fetchSessions();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Interview History</h1>
          <button
            onClick={() => navigate('/')}
            className="text-indigo-600 hover:text-indigo-800"
          >
            ← Back to Dashboard
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-12 text-gray-600">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">No interviews yet.</p>
            <button
              onClick={() => navigate('/')}
              className="mt-4 text-indigo-600 hover:text-indigo-800"
            >
              Start your first interview
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {session.problem_name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Started: {new Date(session.created_at).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500">
                      Status:{' '}
                      <span
                        className={`font-medium ${
                          session.status === 'completed'
                            ? 'text-green-600'
                            : 'text-yellow-600'
                        }`}
                      >
                        {session.status.replace('_', ' ')}
                      </span>
                    </p>
                    <p className="text-sm text-gray-500">
                      Steps: {session.current_step}
                    </p>
                  </div>
                  <button
                    onClick={() =>
                      navigate(
                        session.status === 'completed'
                          ? `/history/${session.id}`
                          : `/interview/${session.id}`
                      )
                    }
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
                  >
                    {session.status === 'completed' ? 'View' : 'Resume'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;