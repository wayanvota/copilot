/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  basePath: "/copilot",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
