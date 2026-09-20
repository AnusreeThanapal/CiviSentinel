/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ops: {
          base: "#080C10",
          surface: "#0D1117",
          card: "#161B22",
          border: "rgba(255, 255, 255, 0.08)",
          accent: "#00E5FF",
          violet: "#8B5CF6"
        },
        sev: {
          cyan: "#00F2FE",
          amber: "#FFB800",
          red: "#FF3366"
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace']
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -3px rgba(0, 242, 254, 0.3)',
        'glow-amber': '0 0 20px -3px rgba(255, 184, 0, 0.3)',
        'glow-red': '0 0 25px -3px rgba(255, 51, 102, 0.4)',
        'glow-brand': '0 0 20px -3px rgba(0, 229, 255, 0.3)',
      },
      animation: {
        'ping-slow': 'ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.9', transform: 'scale(1.05)' },
        }
      }
    },
  },
  plugins: [],
}
