/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
          950: '#042f2e',
        },
        clinical: {
          teal: '#0f766e',
          darkTeal: '#115e59',
          lightTeal: '#f0fdfa',
          surface: '#fafaf9',
          border: '#e7e5e4',
        },
        nhs: {
          blue: '#005EB8',
          darkBlue: '#003087',
          warmYellow: '#FFB81C',
          green: '#007F3B',
          red: '#DA291C'
        }
      }
    },
  },
  plugins: [],
}
