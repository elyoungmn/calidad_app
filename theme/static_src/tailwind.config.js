module.exports = {
  content: [
    '../templates/**/*.html',
    '../../calidad_app/templates/**/*.html',
    '../../calidad_app/**/*.py'
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          100: '#f0f9ff',
          200: '#e0f2fe',
          300: '#bae6fd',
          400: '#7dd3fc',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
    },
  },
  plugins: [],
}
