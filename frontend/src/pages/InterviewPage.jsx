import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useSessionStore from '../store/sessionStore';
import { askQuestion } from '../services/interviewApi';

const InterviewPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { currentSession, fetchSessionDetails, isLoading } = useSessionStore();
  const [messages, setMessages] = useState([]);
  const [answer, setAnswer] = useState('');
  const [sending, setSending] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    loadSession();
  }, [sessionId]);

  useEffect(() => {
    if (currentSession) {
      setMessages(currentSession.messages || []);
      if (currentSession.status === 'completed') {
        setIsComplete(true);
        // Try to find summary message
        const summaryMsg = currentSession.messages?.find(m => 
          m.content && m.content.includes('Architecture Summary')
        );
        if (summaryMsg) {
          setSummary(summaryMsg.content);
          setShowSummary(true);
        }
      }
    }
  }, [currentSession]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadSession = async () => {
    try {
      await fetchSessionDetails(sessionId);
    } catch (error) {
      console.error('Failed to load session:', error);
      navigate('/');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answer.trim() || sending || isComplete) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: answer,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setAnswer('');
    setSending(true);
    inputRef.current?.focus();

    try {
      const response = await askQuestion(sessionId, answer);
      
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.feedback + '\n\n' + response.next_question,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (response.is_complete) {
        setIsComplete(true);
        if (response.architecture_summary) {
          const summaryText = '🏗️ **Architecture Summary:**\n\n' + response.architecture_summary;
          setSummary(summaryText);
          setShowSummary(true);
          const summaryMsg = {
            id: Date.now() + 2,
            role: 'assistant',
            content: summaryText,
            created_at: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, summaryMsg]);
        }
      }
    } catch (error) {
      console.error('Failed to send answer:', error);
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
      alert('Failed to send your answer. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const handleEndInterview = () => {
    navigate('/');
  };

  if (isLoading && !currentSession) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading interview...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/')}
              className="text-gray-500 hover:text-gray-700"
            >
              ←
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                {currentSession?.problem_name}
              </h1>
              <p className="text-xs text-gray-500">
                {isComplete ? '✅ Completed' : `Question ${Math.ceil(messages.length / 2)}`}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {!isComplete && (
              <button
                onClick={handleEndInterview}
                className="px-3 py-1 bg-red-50 text-red-600 text-sm rounded-md hover:bg-red-100 transition"
              >
                End Interview
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 max-w-4xl w-full mx-auto px-4 py-6 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((msg, index) => (
            <div
              key={msg.id || index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-none'
                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none'
                }`}
              >
                <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
                <div className="text-xs mt-1 opacity-60">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 rounded-bl-none">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white sticky bottom-0">
        <div className="max-w-4xl mx-auto px-4 py-4">
          {isComplete ? (
            <div className="text-center py-2">
              <p className="text-green-600 font-semibold">✅ Interview Completed</p>
              {showSummary && (
                <div className="mt-2 text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-200">
                  {summary}
                </div>
              )}
              <button
                onClick={() => navigate('/')}
                className="mt-3 text-indigo-600 hover:text-indigo-800 text-sm font-medium"
              >
                Return to Dashboard
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Type your answer..."
                className="flex-1 rounded-full border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                disabled={sending}
                autoFocus
              />
              <button
                type="submit"
                disabled={!answer.trim() || sending}
                className="px-6 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                Send
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default InterviewPage;