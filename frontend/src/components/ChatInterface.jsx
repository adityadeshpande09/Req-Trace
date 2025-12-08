import React, { useState } from 'react';
import { api } from '../api';
import { MessageSquare } from 'lucide-react';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Send user query to backend /conversation/chat
  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = { id: Date.now(), sender: 'user', text: input };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/conversation/chat', { query: input });

      const answer = res.data?.answer || res.data?.detail || res.data?.error || 'No response from server.';

      const botMessage = {
        id: Date.now() + 1,
        sender: 'bot',
        text: answer,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      let errorMessage = '⚠️ Error: Unable to reach backend.';
      
      if (error.response) {
        // Backend responded with an error
        const status = error.response.status;
        const detail = error.response.data?.detail || error.response.data?.error || error.response.statusText;
        
        if (status === 503) {
          errorMessage = `⚠️ Rate Limit: ${detail || 'OpenAI API rate limit exceeded. Please wait a moment and try again.'}`;
        } else if (status === 500) {
          errorMessage = `⚠️ Server Error: ${detail || 'An error occurred on the server. Please try again.'}`;
        } else {
          errorMessage = `⚠️ Error (${status}): ${detail || error.response.statusText}`;
        }
      } else if (error.request) {
        // Request was made but no response received
        errorMessage = '⚠️ Error: No response from backend. Please check if the server is running on http://localhost:8000';
      } else {
        // Error setting up the request
        errorMessage = `⚠️ Error: ${error.message || 'Failed to send request'}`;
      }
      
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          sender: 'bot',
          text: errorMessage,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center space-y-3">
              <MessageSquare className="w-16 h-16 mx-auto opacity-30" />
              <p className="text-sm">Start a conversation</p>
              <p className="text-xs">Ask questions about your uploaded transcriptions</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.sender === 'user' ? 'bg-teal-600 text-white' : 'bg-gray-700 text-gray-100'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))
        )}

        {/* Typing indicator */}
        {loading && (
          <div className="flex justify-start">
            <div
              className="bg-gray-700 text-gray-300 rounded-lg px-4 py-2 italic"
              data-testid="loading-indicator"
            >
              Thinking...
            </div>
          </div>
        )}
      </div>

      {/* Input box */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your transcripts..."
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500 text-gray-100"
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="px-6 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
