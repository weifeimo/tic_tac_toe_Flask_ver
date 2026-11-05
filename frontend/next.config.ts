import type { NextConfig } from "next";

const FLASK_URL = process.env.FLASK_URL ?? "http://127.0.0.1:5001";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${FLASK_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;