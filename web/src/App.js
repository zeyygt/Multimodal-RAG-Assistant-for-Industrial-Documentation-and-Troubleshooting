import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import Header from './components/Header';
import RobotIcon from './components/RobotIcon';
import SourcePanel from './components/SourcePanel';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: 'Hi! 👋 I\'m your RAG assistant. Ask me anything about your documents!',
      timestamp: new Date(),
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [sourcePanelOpen, setSourcePanelOpen] = useState(false);
  const [currentSources, setCurrentSources] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content) => {
    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call backend API
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: content
      });

      // Add assistant response
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.answer,
        images: response.data.images || [],
        sources: response.data.sources_count || 0,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update sources for panel
      if (response.data.source_chunks && response.data.source_chunks.length > 0) {
        setCurrentSources(response.data.source_chunks);
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: "I couldn't reach the backend 🤖\nMake sure the server is running on port 8000.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-dark-bg">
      <Header />
      
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          {isLoading && (
            <div className="flex items-start gap-3 max-w-[85%]">
              <div className="w-10 h-10">
                <RobotIcon />
              </div>
              <div className="flex items-center gap-3 px-5 py-4 bg-dark-card rounded-3xl border border-dark-border shadow-xl">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm text-purple-text">Thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input */}
      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
      
      {/* Floating Source Button */}
      {currentSources.length > 0 && (
        <button
          onClick={() => setSourcePanelOpen(!sourcePanelOpen)}
          className="fixed bottom-24 right-6 w-14 h-14 bg-primary hover:bg-primary-hover shadow-lg shadow-primary/50 rounded-full flex items-center justify-center transition-all hover:scale-110 active:scale-95 z-30 group"
          title="View Sources"
        >
          <div className="relative">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-purple-400 text-white text-xs font-bold rounded-full flex items-center justify-center">
              {currentSources.length}
            </span>
          </div>
        </button>
      )}
      
      {/* Source Panel */}
      <SourcePanel 
        isOpen={sourcePanelOpen} 
        onClose={() => setSourcePanelOpen(false)}
        sources={currentSources}
      />
    </div>
  );
}

export default App;
