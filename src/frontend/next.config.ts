import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    agentFeedback: true,
  },
  devIndicators: {
    position: "bottom-right",
  },
  cacheComponents: true,
  partialPrefetching: true,
};

export default nextConfig;
