import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        upla: {
          navy: "#1F4E79",
          blue: "#2E74B5",
          sky: "#5B9BD5",
          gold: "#D4AF37",
          cream: "#F5F1E8",
          charcoal: "#2A2A2A",
          ink: "#1a1a2e",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        chat: "0 4px 24px rgba(31, 78, 121, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
