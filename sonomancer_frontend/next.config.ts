import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    domains: ['i.pravatar.cc'],
  },
  serverExternalPackages: [],
};

export default nextConfig;