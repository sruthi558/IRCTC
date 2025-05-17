/** @type {import('next').NextConfig} */

const NextJSObfuscatorPlugin = require("nextjs-obfuscator");
const JavaScriptObfuscator = require("webpack-obfuscator");
const { obfuscate } = require("javascript-obfuscator");

class NextJSBundleObfuscatorPlugin {
  constructor(options) {
    this.options = options;
  }

  apply(compiler) {
    compiler.hooks.emit.tapAsync("after-compile", (compilation, callback) => {
      const pages = Object.keys(compilation.namedChunks)
        .map((key) => compilation.namedChunks[key])
        .filter((chunk) => IS_BUNDLED_PAGE.test(chunk.name));
      pages.forEach((chunk) => {
        const obfuscated = obfuscate(
          compilation.assets[chunk.name].source(),
          this.options
        ).getObfuscatedCode();
        compilation.assets[chunk.name] = {
          source: () => obfuscated,
          size: () => obfuscated.length,
        };
      });
      callback();
    });
  }
}

const obfuscatoroptions = {
  rotateUnicodeArray: true,
  stringArrayShuffle: true,
  deadCodeInjection: true,
  deadCodeInjectionThreshold: 0.4,
  debugProtection: true,
  debugProtectionInterval: 0,
  disableConsoleOutput: true,
};

const nextConfig = {
  experimental: {
    proxyTimeout: 120000
  },
  webpack: (config, { dev }) => {
    config.resolve.fallback = { fs: false };
    if (!dev) {
      config.plugins.push(new JavaScriptObfuscator(obfuscatoroptions, ["bundles/**/**.js"]));
      config.plugins.push(
        new NextJSBundleObfuscatorPlugin(obfuscatoroptions)
      );
    }

    return config;
  },
  reactStrictMode: true,
  serverRuntimeConfig: {
    // Increase the server timeout (in milliseconds)
    serverTimeout: 120000
    // proxyTimeout: 120000 // 120 seconds
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_ENDPOINT}/:path*`,
      },
    ];
  },
  async redirects() {
    return [
      {
        source: "/",
        destination: "/signin",
        permanent: true,
      },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  poweredByHeader: false,
};

module.exports = nextConfig;
