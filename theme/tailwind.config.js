/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // App templates
    "../templates/**/*.{html,js}",
    "../../templates/**/*.{html,js}",
    "../../**/templates/**/*.{html,js}",
    // Optional: JS in static folders
    "../static/**/*.js",
    "../../**/static/**/*.js",
    // Django forms/py strings (kept conservative)
    "../**/*.py"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
