/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ninja: {
          dark: '#0f0f10',
          bg: '#1a1a1d',        // Dark charcoal gray
          card: '#222226',      // Slightly lighter for cards
          sidebar: '#8b0000',   // Deep red sidebar
          hover: '#a40000',     // Hover red
          accent: '#cd9b1d',    // Golden-brown border
          danger: '#dc3545',    // Vibrant red button
          dangerDark: '#8b0000',// Dark red border for button
          success: '#28a745',
          text: '#e5e5e5'
        }
      }
    },
  },
  plugins: [],
}