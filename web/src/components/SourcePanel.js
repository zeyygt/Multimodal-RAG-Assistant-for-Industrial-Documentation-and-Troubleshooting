import React from 'react';

function SourcePanel({ isOpen, onClose, sources }) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className={`fixed right-0 top-0 h-full w-96 bg-dark-card border-l border-dark-border shadow-2xl z-50 transform transition-transform duration-300 ease-out ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-border bg-dark-bg/50">
          <div className="flex items-center gap-2">
            <span className="text-xl">📚</span>
            <h2 className="text-lg font-semibold text-white">Source Documents</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-dark-bg/70 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto h-[calc(100%-64px)] p-4 space-y-4">
          {!sources || sources.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              <svg className="w-16 h-16 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-sm">No sources available</p>
              <p className="text-xs mt-1">Ask a question to see relevant sources</p>
            </div>
          ) : (
            sources.map((source, idx) => (
              <div key={idx} className="bg-dark-bg/40 rounded-xl border border-dark-border/50 overflow-hidden hover:border-primary/30 transition-all">
                {/* Source Header */}
                <div className="p-3 bg-dark-bg/60 border-b border-dark-border/30">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-primary">Source {idx + 1}</span>
                    {source.page && (
                      <span className="text-xs text-gray-500 bg-dark-card px-2 py-0.5 rounded-full">
                        Page {source.page}
                      </span>
                    )}
                  </div>
                  {source.section && (
                    <h3 className="text-sm font-medium text-white mt-1 line-clamp-2">{source.section}</h3>
                  )}
                </div>

                {/* Text Content */}
                {source.text && (
                  <div className="p-3">
                    <p className="text-xs text-gray-300 leading-relaxed line-clamp-6">
                      {source.text}
                    </p>
                  </div>
                )}

                {/* Images */}
                {source.images && source.images.length > 0 && (
                  <div className="p-3 pt-0 space-y-2">
                    {source.images.map((img, imgIdx) => (
                      <div key={imgIdx} className="relative group rounded-lg overflow-hidden border border-dark-border/30">
                        <img 
                          src={`http://localhost:8000${img.path || img}`}
                          alt={`Source ${idx + 1} - View ${imgIdx + 1}`}
                          className="w-full h-auto object-contain bg-dark-bg/20 cursor-pointer hover:scale-105 transition-transform"
                          onClick={() => window.open(`http://localhost:8000${img.path || img}`, '_blank')}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                        <div className="absolute top-2 right-2 bg-black/70 px-2 py-1 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity">
                          Click to expand
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Similarity Score */}
                {source.similarity && (
                  <div className="px-3 pb-3">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>Relevance:</span>
                      <div className="flex-1 h-1.5 bg-dark-bg rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-primary to-purple-400 rounded-full"
                          style={{ width: `${Math.min(source.similarity * 100, 100)}%` }}
                        />
                      </div>
                      <span className="font-medium text-primary">{(source.similarity * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}

export default SourcePanel;
