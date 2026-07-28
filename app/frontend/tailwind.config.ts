import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        glass: {
          light: 'rgba(255,255,255,0.55)',
          dark: 'rgba(28,28,30,0.6)',
        },
        accent: {
          blue: '#4C7DFF',
          pink: '#FF6B9D',
          purple: '#9C6BFF',
          teal: '#5CD9C7',
          orange: '#FF9F45',
          red: '#FF5E5B',
        },
      },
      borderRadius: {
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"PingFang SC"',
          '"Microsoft YaHei"',
          'sans-serif',
        ],
      },
      backdropBlur: {
        xs: '4px',
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0,0,0,0.08)',
        'glass-dark': '0 8px 32px rgba(0,0,0,0.4)',
      },
    },
  },
  plugins: [],
} satisfies Config
