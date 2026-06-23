/** Teal / Emerald healthcare palette — mirrors ui/themes/colors.py (the desktop
 * source of truth) so the web UI matches the brand exactly. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#0F766E",
          hover: "#0D9488",
          pressed: "#115E59",
          disabled: "#9DC4C0",
          soft: "#E6F3F1",
          softtext: "#115E59",
        },
        accent: {
          DEFAULT: "#0D9488",
          hover: "#0F766E",
          soft: "#D9F2EF",
        },
        bg: "#F6F8F8",
        surface: { DEFAULT: "#FFFFFF", alt: "#F1F6F5", sunken: "#E9F0EF" },
        border: { DEFAULT: "#E3E8E8", strong: "#C7D2D0" },
        ink: { DEFAULT: "#14201E", secondary: "#4F5E5B", muted: "#84938F" },
        success: { DEFAULT: "#16A34A", bg: "#E4F6EA", text: "#166534" },
        warning: { DEFAULT: "#D97706", bg: "#FCEFD9", text: "#92580B" },
        danger: { DEFAULT: "#DC2626", bg: "#FBE3E3", text: "#991B1B" },
        info: { DEFAULT: "#0E7490", bg: "#DEF1F5", text: "#0B5566" },
        kpi: { blue: "#0E7490", green: "#16A34A", amber: "#D97706", purple: "#6D5BD0" },
        sidebar: { top: "#134E4A", bottom: "#0F766E", active: "#2DD4BF" },
      },
      fontFamily: {
        sans: ["Cairo", "Tahoma", "Segoe UI", "system-ui", "sans-serif"],
      },
      borderRadius: { card: "14px" },
      boxShadow: {
        card: "0 1px 3px rgba(20,32,30,0.06), 0 1px 2px rgba(20,32,30,0.04)",
        soft: "0 4px 16px rgba(20,32,30,0.08)",
      },
    },
  },
  plugins: [],
};
