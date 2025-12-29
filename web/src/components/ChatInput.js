import React, { useState } from 'react';

function ChatInput({ onSendMessage, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-dark-border bg-dark-card">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto px-4 py-4">
        <div className="relative flex items-center">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask me about your documents..."
            rows={1}
            className="flex-1 bg-dark-bg text-white placeholder-gray-500 rounded-3xl px-6 py-4 pr-14 
                     focus:outline-none focus:ring-2 focus:ring-primary border border-dark-border
                     disabled:opacity-50 disabled:cursor-not-allowed resize-none transition-all"
            style={{ minHeight: '56px', maxHeight: '200px' }}
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
            }}
          />
          
          <button
            type="submit"
            disabled={disabled || !input.trim()}
            className="absolute right-3 w-11 h-11 bg-primary hover:bg-primary-hover 
                     disabled:opacity-40 disabled:cursor-not-allowed
                     rounded-2xl flex items-center justify-center transition-all duration-200
                     hover:scale-105 active:scale-95 shadow-lg shadow-primary/30"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        
        <div className="mt-2 text-xs text-gray-600 text-center">
          Press Enter to send • Shift+Enter for new line
        </div>
      </form>
    </div>
  );
}

export default ChatInput;
