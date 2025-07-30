/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: '#374151',
            a: {
              color: '#2563eb',
              textDecoration: 'underline',
              '&:hover': {
                color: '#1d4ed8',
              },
            },
            strong: {
              color: '#111827',
              fontWeight: '600',
            },
            h1: {
              color: '#111827',
              fontWeight: '700',
              fontSize: '1.25rem',
              marginTop: '0',
              marginBottom: '0.5rem',
            },
            h2: {
              color: '#111827',
              fontWeight: '600',
              fontSize: '1.125rem',
              marginTop: '0',
              marginBottom: '0.5rem',
            },
            h3: {
              color: '#111827',
              fontWeight: '500',
              fontSize: '1rem',
              marginTop: '0',
              marginBottom: '0.25rem',
            },
            p: {
              marginTop: '0',
              marginBottom: '0.5rem',
              '&:last-child': {
                marginBottom: '0',
              },
            },
            ul: {
              marginTop: '0',
              marginBottom: '0.5rem',
              paddingLeft: '1.25rem',
            },
            ol: {
              marginTop: '0',
              marginBottom: '0.5rem',
              paddingLeft: '1.25rem',
            },
            li: {
              marginTop: '0.25rem',
              marginBottom: '0.25rem',
            },
            blockquote: {
              borderLeftColor: '#d1d5db',
              color: '#6b7280',
              fontStyle: 'italic',
              marginTop: '0',
              marginBottom: '0.5rem',
            },
            code: {
              backgroundColor: '#f3f4f6',
              padding: '0.125rem 0.25rem',
              borderRadius: '0.25rem',
              fontSize: '0.875rem',
              color: '#374151',
              '&::before': {
                content: '""',
              },
              '&::after': {
                content: '""',
              },
            },
            pre: {
              backgroundColor: '#f3f4f6',
              padding: '0.5rem',
              borderRadius: '0.25rem',
              fontSize: '0.875rem',
              overflow: 'auto',
              marginTop: '0',
              marginBottom: '0.5rem',
            },
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
