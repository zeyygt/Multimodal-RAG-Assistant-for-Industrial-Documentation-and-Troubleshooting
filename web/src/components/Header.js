import React from 'react';

function Header() {
  return (
    <header className="border-b border-dark-border bg-dark-card">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white">RAG Assistant</h1>
            <p className="text-xs text-gray-500">Document Q&A</p>
          </div>
        </div>
        
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
      </div>
    </header>
  );
}

export default Header;
