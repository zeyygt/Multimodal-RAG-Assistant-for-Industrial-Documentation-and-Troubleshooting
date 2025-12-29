/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Premium solid purple palette
        'primary': '#6D3AFF',
        'primary-hover': '#5A2FE6',
        'dark-bg': '#0F0F14',
        'dark-card': '#1A1A24',
        'dark-border': '#2A2A3A',
        'purple-text': '#B8A3FF',
        'dark': '#0a0a0f',
        'darker': '#050508',
        'purple': {
          500: '#6D3AFF',
          600: '#5A2FE6',
          700: '#4A23CC',
          800: '#3A1CB3',
          900: '#2A1599',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-purple': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-dark': 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      },
    },
  },
  plugins: [],
}
