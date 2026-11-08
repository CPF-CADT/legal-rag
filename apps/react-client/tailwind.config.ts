import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        khmer: ['Noto Sans Khmer', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
