import React from 'react';

// Cute minimal robot SVG icon
const RobotIcon = () => (
  <svg className="w-8 h-8" viewBox="0 0 40 40" fill="none">
    {/* Head */}
    <rect x="10" y="10" width="20" height="18" rx="6" fill="#6D3AFF" opacity="0.9"/>
    {/* Antenna */}
    <circle cx="20" cy="7" r="2" fill="#B8A3FF"/>
    <line x1="20" y1="9" x2="20" y2="10" stroke="#B8A3FF" strokeWidth="2"/>
    {/* Eyes */}
    <circle cx="16" cy="17" r="2" fill="white"/>
    <circle cx="24" cy="17" r="2" fill="white"/>
    {/* Mouth */}
    <path d="M 15 23 Q 20 25 25 23" stroke="white" strokeWidth="2" strokeLinecap="round" fill="none"/>
    {/* Body */}
    <rect x="12" y="28" width="16" height="8" rx="3" fill="#6D3AFF" opacity="0.7"/>
  </svg>
);

export default RobotIcon;
