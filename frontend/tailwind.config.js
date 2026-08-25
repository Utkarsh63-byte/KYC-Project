/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bank: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0284c7',
          600: '#0265d2',
          700: '#034da2',
          800: '#073a77',
          900: '#0c2e5b',
          950: '#071b38',
        }
      }
    },
  },
  plugins: [],
}
