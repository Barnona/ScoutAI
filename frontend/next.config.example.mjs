/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: [
    "Client URL",
    "localhost:3000",
    "Backend URL:3000",
  ],
};

export default nextConfig;
