/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        wine: {
          50: "#fdf2f4",
          100: "#fce7ec",
          200: "#f9d0d9",
          300: "#f4a8b8",
          400: "#ec7590",
          500: "#e0486e",
          600: "#c82a52",
          700: "#a81e42",
          800: "#8c1b3b",
          900: "#771a37",
          950: "#43091b",
        },
      },
    },
  },
  plugins: [],
};
