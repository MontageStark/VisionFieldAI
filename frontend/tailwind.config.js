/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef7ff',
          100: '#d9ecff',
          200: '#b6d8ff',
          300: '#83bbff',
          400: '#4f99ff',
          500: '#2a78f7',
          600: '#1a5ce0',
          700: '#1848b3',
          800: '#193f8e',
          900: '#1a3873',
        },
      },
    },
  },
  plugins: [],
};
