/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        steam: {
          dark: '#171a21',
          bg: '#1b2838',
          card: '#2a475e',
          hover: '#316282',
          accent: '#66c0f4',
          success: '#5ba32b',
          danger: '#d94126'
        }
      }
    },
  },
  plugins: [],
}
