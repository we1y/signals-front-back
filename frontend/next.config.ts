import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  staticPageGenerationTimeout: 60
};

const withNextIntl = createNextIntlPlugin();

export default withNextIntl(nextConfig)
