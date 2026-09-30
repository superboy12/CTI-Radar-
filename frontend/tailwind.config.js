/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#09090b", // Very dark, almost black
        card: "#18181b",       // Slightly lighter for cards
        border: "#27272a",
        primary: {
          DEFAULT: "#3b82f6", // Vibrant Blue
          hover: "#2563eb",
          light: "#60a5fa"
        },
        danger: {
          DEFAULT: "#ef4444", // Red for High Risk
          hover: "#dc2626"
        },
        warning: {
          DEFAULT: "#eab308", // Yellow for Medium Risk
          hover: "#ca8a04"
        },
        success: {
          DEFAULT: "#22c55e", // Green for Safe
          hover: "#16a34a"
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
