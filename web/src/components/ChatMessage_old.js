import React from 'react';
import ReactMarkdown from 'react-markdown';

function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
      <div className={`flex max-w-[80%] space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isUser 
            ? 'bg-gradient-to-br from-purple-600 to-purple-800' 
            : 'bg-gradient-to-br from-purple-500 to-pink-500'
        }`}>
          {isUser ? (
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          ) : (
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          )}
        </div>

        {/* Message Content */}
        <div className={`flex-1 ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`rounded-2xl px-4 py-3 ${
            isUser 
              ? 'bg-gradient-to-br from-purple-600 to-purple-700 text-white' 
              : 'bg-gray-800/50 backdrop-blur-sm text-gray-100 border border-purple-900/30'
          }`}>
            <div className="prose prose-invert prose-sm max-w-none
                          prose-headings:text-purple-200 prose-headings:font-semibold prose-headings:mt-4 prose-headings:mb-2
                          prose-h2:text-lg prose-h3:text-base
                          prose-p:text-gray-200 prose-p:leading-relaxed prose-p:my-2
                          prose-strong:text-purple-300 prose-strong:font-bold
                          prose-em:text-purple-200 prose-em:italic
                          prose-ul:list-disc prose-ul:ml-5 prose-ul:my-2
                          prose-ol:list-decimal prose-ol:ml-5 prose-ol:my-2
                          prose-li:my-1 prose-li:text-gray-200 prose-li:leading-relaxed
                          prose-blockquote:border-l-4 prose-blockquote:border-purple-500/70
                          prose-blockquote:bg-purple-950/30 prose-blockquote:py-2
                          prose-blockquote:pl-4 prose-blockquote:my-3 prose-blockquote:italic 
                          prose-blockquote:text-purple-300
                          prose-code:text-purple-300 prose-code:bg-gray-900/70 
                          prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>

            {/* Images */}
            {message.images && message.images.length > 0 && (
              <div className="mt-4 space-y-2">
                <div className="text-xs text-purple-400 font-semibold mb-2 flex items-center gap-2">
                  <span>🖼️ Related Images</span>
                  <span className="text-purple-500">({message.images.length})</span>
                </div>
                <div className={`grid gap-3 ${message.images.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
                  {message.images.map((img, idx) => (
                    <div key={idx} className="relative group overflow-hidden rounded-lg border border-purple-900/30 
                                            hover:border-purple-500/50 transition-all bg-gray-900/40">
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
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/50 to-transparent 
                                      p-2 text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity">
                          {img.caption}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sources */}
            {message.sources && message.sources > 0 && (
              <div className="mt-3 pt-3 border-t border-purple-900/20">
                <div className="text-xs text-purple-400/70">
                  📚 {message.sources} source{message.sources > 1 ? 's' : ''} used
                </div>
              </div>
            )}
          </div>
          
          <div className="text-xs text-gray-500 mt-1 px-2">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
