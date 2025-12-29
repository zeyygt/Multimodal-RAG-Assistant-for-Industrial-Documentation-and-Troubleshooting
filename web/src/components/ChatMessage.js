import React from 'react';
import ReactMarkdown from 'react-markdown';
import RobotIcon from './RobotIcon';

function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex max-w-[85%] gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
        {/* Avatar */}
        <div className="flex-shrink-0">
          {isUser ? (
            <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
          ) : (
            <div className="w-10 h-10">
              <RobotIcon />
            </div>
          )}
        </div>

        {/* Message Content */}
        <div className="flex-1">
          <div className={`rounded-3xl px-5 py-4 ${
            isUser 
              ? 'bg-primary text-white shadow-lg' 
              : 'bg-dark-card border border-dark-border shadow-xl text-white'
          }`}>
            <div className={`prose prose-sm max-w-none prose-invert ${
              !isUser && 
                'prose-headings:text-purple-text prose-headings:font-semibold prose-headings:mt-3 prose-headings:mb-2 prose-h2:text-base prose-h3:text-sm prose-p:text-gray-200 prose-p:leading-relaxed prose-p:my-2 prose-strong:text-primary prose-strong:font-semibold prose-em:text-purple-300 prose-ul:list-disc prose-ul:ml-4 prose-ul:my-2 prose-ol:list-decimal prose-ol:ml-4 prose-ol:my-2 prose-li:my-1.5 prose-li:text-gray-200 prose-li:leading-relaxed prose-blockquote:border-l-4 prose-blockquote:border-primary/70 prose-blockquote:bg-primary/10 prose-blockquote:py-2 prose-blockquote:pl-4 prose-blockquote:my-3 prose-blockquote:italic prose-blockquote:text-purple-text prose-code:text-primary prose-code:bg-dark-bg/70 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm'
            }`}>
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>

            {/* Images */}
            {message.images && message.images.length > 0 && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center gap-2 text-xs font-medium">
                  <span className="text-primary">🖼️ Related Images</span>
                  <span className="px-2 py-0.5 bg-primary/20 text-purple-text rounded-full">{message.images.length}</span>
                </div>
                <div className={`grid gap-3 ${message.images.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
                  {message.images.map((img, idx) => (
                    <div key={idx} className="relative group overflow-hidden rounded-xl border border-dark-border hover:border-primary/50 transition-all bg-dark-bg/40">
                      <img 
                        src={`http://localhost:8000${img.path}`}
                        alt={img.caption || `Image ${idx + 1}`}
                        className="w-full h-auto object-contain cursor-pointer transform group-hover:scale-105 transition-transform"
                        onClick={() => window.open(`http://localhost:8000${img.path}`, '_blank')}
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                      {img.caption && (
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-3 text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity">
                          {img.caption}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sources */}
            {!isUser && message.sources && message.sources > 0 && (
              <div className="mt-3 pt-3 border-t border-dark-border/50">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-dark-bg/50 rounded-full text-xs text-gray-400">
                  <span>📄</span>
                  <span>{message.sources} source{message.sources > 1 ? 's' : ''} used</span>
                </div>
              </div>
            )}
          </div>
          
          <div className="text-xs text-gray-600 mt-1.5 px-2">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
