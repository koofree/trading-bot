/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      animation: {
        'fade-in': 'fadeIn 0.5s ease',
        'pulse-soft': 'pulseSoft 2s infinite',
      },
      keyframes: {
        fadeIn: {
          'from': {
            opacity: '0',
            transform: 'translateY(10px)'
          },
          'to': {
            opacity: '1',
            transform: 'translateY(0)'
          }
        },
        pulseSoft: {
          '0%': {
            boxShadow: '0 0 0 0 rgba(102, 126, 234, 0.7)'
          },
          '70%': {
            boxShadow: '0 0 0 10px rgba(102, 126, 234, 0)'
          },
          '100%': {
            boxShadow: '0 0 0 0 rgba(102, 126, 234, 0)'
          }
        }
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }
    },
  },
  plugins: [],
}

