/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "primary": "#2563EB",
        "primary-container": "#1D4ED8",
        "accent": "#7C3AED",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger": "#EF4444",
        "background": "#F8FAFC",
        "surface": "#FFFFFF",
        "on-surface": "#0F172A",
        "on-surface-variant": "#64748B",
        "border": "#E2E8F0",
      },
      borderRadius: {
        "DEFAULT": "1rem", // 16px
        "md": "1.25rem", // 20px
        "lg": "1.5rem", // 24px
        "xl": "2rem", // 32px
        "2xl": "2.5rem", // 40px
        "3xl": "3rem", // 48px
        "full": "9999px",
        "premium": "32px"
      },
      spacing: {
        "margin-mobile": "24px",
        "container-max": "1440px",
        "gutter": "32px",
        "unit": "4px",
        "margin-desktop": "64px"
      },
      fontFamily: {
        "headline": ["General Sans", "Satoshi", "Inter", "sans-serif"],
        "body": ["Inter", "sans-serif"],
        "mono": ["Jetbrains Mono", "monospace"]
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(15, 23, 42, 0.05)',
        'float': '0 10px 40px -10px rgba(15, 23, 42, 0.08)',
        'premium': '0 20px 50px rgba(15, 23, 42, 0.06)'
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-up": "slide-up 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-in-right": "slide-in-right 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "scale-in": "scale-in 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
      }
    }
  },
  plugins: [],
}
