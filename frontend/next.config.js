/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Enable SWC minification for better performance
  swcMinify: true,

  // Configure experimental features
  experimental: {
    // App Router is now stable in Next.js 14, no experimental flags needed
  },

  // Environment variables to expose to the browser
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_APP_NAME:
      process.env.NEXT_PUBLIC_APP_NAME || "Universal Product Automation System",
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || "1.0.0",
  },

  // Image optimization configuration
  images: {
    // Configure allowed image domains for optimization
    domains: [
      "localhost",
      "127.0.0.1",
      // Add production domains here when deployed
    ],

    // Configure image formats
    formats: ["image/webp", "image/avif"],

    // Configure image sizes for responsive images
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Configure redirects
  async redirects() {
    return [
      // Redirect root to dashboard (when implemented)
      // {
      //   source: '/',
      //   destination: '/dashboard',
      //   permanent: false,
      // },
    ];
  },

  // Configure rewrites for API proxy (if needed)
  async rewrites() {
    return [
      // Proxy API requests to backend during development
      {
        source: "/api/:path*",
        destination: `${
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        }/api/:path*`,
      },
    ];
  },

  // Configure headers for security and performance
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          // Security headers
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          // Performance headers
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
        ],
      },
    ];
  },

  // Configure webpack for custom optimizations
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Add custom webpack configurations here if needed

    // Example: Add bundle analyzer in development
    if (dev && !isServer) {
      // Uncomment to enable bundle analyzer
      // const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      // config.plugins.push(
      //   new BundleAnalyzerPlugin({
      //     analyzerMode: 'server',
      //     openAnalyzer: false,
      //   })
      // );
    }

    return config;
  },

  // Configure TypeScript
  typescript: {
    // Enable type checking during build
    ignoreBuildErrors: false,
  },

  // Configure ESLint
  eslint: {
    // Enable ESLint during build
    ignoreDuringBuilds: false,
  },

  // Configure output for different deployment targets
  output: process.env.NODE_ENV === "production" ? "standalone" : undefined,

  // Configure compression
  compress: true,

  // Configure power-ups for better performance
  poweredByHeader: false,

  // Configure trailing slash behavior
  trailingSlash: false,
};

module.exports = nextConfig;
