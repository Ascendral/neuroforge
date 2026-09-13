import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        accent: '#E10500',
        canvas: '#0A0A0B',
        gold: '#FFD05D',
        sky: '#9BD2FF',
      },
      fontFamily: {
        display: ['ui-serif', '"New York"', '"Iowan Old Style"', 'Georgia', 'serif'],
        text: ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Text"', '"Helvetica Neue"', 'Inter', 'sans-serif'],
        mono: ['ui-monospace', '"SF Mono"', 'Menlo', 'monospace'],
      },
      borderRadius: {
        card: '26px',
        tile: '18px',
      },
    },
  },
  plugins: [],
};

export default config;
