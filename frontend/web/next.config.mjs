/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: true
  },
  async rewrites() {
    return [
      {
        source: "/:path*",
        destination: "http://localhost:8000/:path*"
      }
    ];
  }
};

export default nextConfig;
