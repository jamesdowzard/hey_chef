export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {
      // Support for browsers from last 2 versions
      overrideBrowserslist: [
        'last 2 versions',
        'not dead',
        'not < 2%',
        'not ie 11'
      ],
      // Add prefixes for CSS Grid
      grid: 'autoplace',
      // Remove outdated prefixes
      remove: true
    },
    // CSS optimization for production
    ...(process.env.NODE_ENV === 'production' && {
      cssnano: {
        preset: ['default', {
          // Preserve important comments (like license headers)
          discardComments: { removeAll: false },
          // Normalize whitespace but keep readability
          normalizeWhitespace: { exclude: false },
          // Optimize custom properties for chef theme
          reduceIdents: false,
          // Keep calc() functions readable
          calc: false,
          // Preserve chef-specific animations
          reduceTransforms: false
        }]
      }
    })
  }
}